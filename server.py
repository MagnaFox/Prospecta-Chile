"""
ProspectaChile B2B HTTP Server and REST API
Runs with zero external dependencies on standard Python 3.x
"""
import http.server
import socketserver
import urllib.parse
import json
import os
import sys
import csv
import io
from core.database import (
    init_db, query_companies, get_stats, get_filter_options, 
    update_crm_status, save_route, get_routes, get_connection
)
from core.enricher import get_external_links, query_mercadopublico
from core.router import cluster_by_corridor, build_route_plan
from core.importer import seed_sample_dataset

PORT = 8080
# Compatible con ejecución normal y con bundle PyInstaller (.exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")

class ApiRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Static index
        if path == "/" or path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()

        # API: Stats
        if path == "/api/stats":
            self.send_json(get_stats())
            return

        # API: Filter Options
        if path == "/api/filters":
            self.send_json(get_filter_options())
            return

        # API: Companies Search
        if path == "/api/companies":
            q = query.get("q", [""])[0]
            region = query.get("region", [""])[0]
            comuna = query.get("comuna", [""])[0]
            rubro = query.get("rubro", [""])[0]
            tramo_min = int(query.get("tramo_min", [0])[0])
            tramo_max = int(query.get("tramo_max", [13])[0])
            trabajadores_min = int(query.get("trabajadores_min", [0])[0])
            crm_estado = query.get("crm_estado", [""])[0]
            solo_activas = query.get("solo_activas", ["true"])[0].lower() in ["true", "1", "yes"]
            limit = min(int(query.get("limit", [50])[0]), 200)
            offset = int(query.get("offset", [0])[0])

            res = query_companies(
                query=q, region=region, comuna=comuna, rubro=rubro,
                tramo_min=tramo_min, tramo_max=tramo_max,
                trabajadores_min=trabajadores_min, crm_estado=crm_estado,
                solo_activas=solo_activas, limit=limit, offset=offset
            )
            self.send_json(res)
            return

        # API: Routes List
        if path == "/api/routes":
            self.send_json(get_routes())
            return

        # API: Export CSV
        if path == "/api/export":
            comuna = query.get("comuna", [""])[0]
            rubro = query.get("rubro", [""])[0]
            tramo_min = int(query.get("tramo_min", [0])[0])
            res = query_companies(comuna=comuna, rubro=rubro, tramo_min=tramo_min, limit=2000)
            
            output = io.StringIO()
            writer = csv.writer(output, delimiter=";")
            writer.writerow(["RUT", "Razon Social", "Tramo Ventas", "Trabajadores", "Rubro", "Comuna", "Direccion", "Estado CRM", "Telefono", "Email"])
            for r in res["results"]:
                writer.writerow([
                    f"{r['rut']}-{r['dv']}", r['razon_social'], r['tramo_ventas'], 
                    r['trabajadores'], r['rubro'], r['comuna'], r['direccion_completa'],
                    r['crm_estado'], r.get('contacto_telefono', ''), r.get('contacto_email', '')
                ])
            
            content = output.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=prospectos_chile.csv")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # API: Corridor clusters
        if path == "/api/clusters":
            comuna = query.get("comuna", ["PROVIDENCIA"])[0]
            res = query_companies(comuna=comuna, limit=200)
            clusters = cluster_by_corridor(res["results"])
            self.send_json(clusters)
            return

        # Fallback to static files
        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body) if body else {}

        # API: Enrich company contact info
        if path == "/api/enrich":
            rut = data.get("rut", "")
            razon = data.get("razon_social", "")
            comuna = data.get("comuna", "")
            
            mp_data = query_mercadopublico(rut)
            links = get_external_links(razon, comuna)
            
            # If MP returned email/phone, update DB
            if mp_data.get("encontrado"):
                update_crm_status(
                    rut=rut, 
                    estado="Por Contactar", 
                    email=mp_data.get("email"), 
                    telefono=mp_data.get("telefono")
                )
            
            self.send_json({
                "rut": rut,
                "mercadopublico": mp_data,
                "links": links
            })
            return

        # API: Update CRM Status
        if path == "/api/crm/status":
            rut = data.get("rut")
            estado = data.get("estado")
            notas = data.get("notas")
            email = data.get("email")
            telefono = data.get("telefono")
            
            ok = update_crm_status(rut, estado, notas, email, telefono)
            self.send_json({"success": ok})
            return

        # API: Save Route
        if path == "/api/routes/save":
            nombre = data.get("nombre", "Ruta sin nombre")
            fecha = data.get("fecha", "")
            comuna = data.get("comuna", "")
            ruts = data.get("ruts", [])
            notas = data.get("notas", "")
            
            route_id = save_route(nombre, fecha, comuna, ruts, notas)
            self.send_json({"success": True, "id": route_id})
            return

        # API: Build Map Route
        if path == "/api/routes/build":
            ruts = data.get("ruts", [])
            conn = get_connection()
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(ruts))
            cursor.execute(f"SELECT * FROM empresas WHERE rut IN ({placeholders})", ruts)
            comps = [dict(r) for r in cursor.fetchall()]
            conn.close()
            plan = build_route_plan(comps)
            self.send_json(plan)
            return

        self.send_error(404, "Endpoint not found")

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def run_server():
    init_db()
    seed_sample_dataset(count=1500)
    
    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, ApiRequestHandler)
    print(f"============================================================")
    print(f" ProspectaChile B2B Server iniciado exitosamente")
    print(f" URL Local: http://localhost:{PORT}")
    print(f" Presiona Ctrl+C para detener el servidor")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
