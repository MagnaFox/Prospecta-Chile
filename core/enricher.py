"""
Contact enrichment and search link generator for B2B prospecting
"""
import urllib.parse
import json
import ssl
import urllib.request
from typing import Dict, Any

def get_external_links(razon_social: str, comuna: str = "") -> Dict[str, str]:
    """Generates direct 1-click links for commercial intelligence"""
    query_google = f'"{razon_social}" {comuna} chile'.strip()
    query_linkedin = f'"{razon_social}" (contador OR finanzas OR "gerente general" OR GAF)'.strip()
    query_maps = f'{razon_social}, {comuna}, Chile'.strip()
    
    return {
        "google_search": f"https://www.google.com/search?q={urllib.parse.quote(query_google)}",
        "google_maps": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query_maps)}",
        "linkedin_search": f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query_linkedin)}",
        "sii_consulta": "https://zeus.sii.cl/cvc_cgi/dte/ce_consulta_rut.cgi"
    }

def query_mercadopublico(rut: str) -> Dict[str, Any]:
    """
    Queries public supplier directory from Mercado Publico.
    Handles self-signed or internal SSL certificates gracefully.
    """
    clean_rut = rut.replace(".", "").replace("-", "").strip()
    # Mercado Publico API endpoint
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/Empresas/BuscarProveedor?rut={clean_rut}"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProspectaChile/1.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("listaEmpresas", [])
            if items:
                emp = items[0]
                return {
                    "encontrado": True,
                    "nombre_fantasia": emp.get("NombreEmpresa", ""),
                    "telefono": emp.get("Telefono", ""),
                    "email": emp.get("MailContacto", ""),
                    "sitio_web": emp.get("SitioWeb", ""),
                    "contacto": emp.get("NombreContacto", ""),
                    "fuente": "Mercado Público"
                }
    except Exception as e:
        pass
        
    return {
        "encontrado": False,
        "mensaje": "No figura registrado como proveedor activo de Mercado Público"
    }
