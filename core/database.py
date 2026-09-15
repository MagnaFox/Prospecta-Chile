"""
Database management for ProspectaChile B2B
"""
import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prospecta.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        rut TEXT PRIMARY KEY,
        dv TEXT,
        razon_social TEXT NOT NULL,
        tramo_ventas INTEGER DEFAULT 0,
        trabajadores INTEGER DEFAULT 0,
        inicio_actividades TEXT,
        termino_giro TEXT,
        rubro TEXT,
        subrubro TEXT,
        actividad_economica TEXT,
        region TEXT,
        provincia TEXT,
        comuna TEXT,
        calle TEXT,
        numero TEXT,
        depto TEXT,
        direccion_completa TEXT,
        lat REAL,
        lon REAL,
        crm_estado TEXT DEFAULT 'Nuevo',
        crm_notas TEXT,
        contacto_email TEXT,
        contacto_telefono TEXT,
        contacto_fuente TEXT,
        actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comuna ON empresas(comuna)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_region ON empresas(region)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tramo ON empresas(tramo_ventas)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rubro ON empresas(rubro)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_estado ON empresas(crm_estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_razon ON empresas(razon_social)")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rutas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fecha TEXT NOT NULL,
        comuna TEXT,
        notas TEXT,
        ruts_ordenados TEXT,
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def query_companies(
    query: str = "",
    region: str = "",
    comuna: str = "",
    rubro: str = "",
    tramo_min: int = 0,
    tramo_max: int = 13,
    trabajadores_min: int = 0,
    crm_estado: str = "",
    solo_activas: bool = True,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if solo_activas:
        where_clauses.append("(termino_giro IS NULL OR termino_giro = '')")
        
    if query:
        clean_q = query.replace(".", "").replace("-", "").strip()
        where_clauses.append("(rut LIKE ? OR razon_social LIKE ?)")
        params.extend([f"%{clean_q}%", f"%{query}%"])
        
    if region:
        where_clauses.append("region = ?")
        params.append(region)
        
    if comuna:
        where_clauses.append("comuna = ?")
        params.append(comuna)
        
    if rubro:
        where_clauses.append("rubro = ?")
        params.append(rubro)
        
    if tramo_min > 0:
        where_clauses.append("tramo_ventas >= ?")
        params.append(tramo_min)
        
    if tramo_max < 13:
        where_clauses.append("tramo_ventas <= ?")
        params.append(tramo_max)
        
    if trabajadores_min > 0:
        where_clauses.append("trabajadores >= ?")
        params.append(trabajadores_min)
        
    if crm_estado:
        where_clauses.append("crm_estado = ?")
        params.append(crm_estado)
        
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    
    count_sql = f"SELECT COUNT(*) FROM empresas {where_sql}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]
    
    sql = f"""
    SELECT rut, dv, razon_social, tramo_ventas, trabajadores, 
           inicio_actividades, termino_giro, rubro, actividad_economica,
           region, comuna, calle, numero, depto, direccion_completa,
           lat, lon, crm_estado, crm_notas, contacto_email, contacto_telefono
    FROM empresas 
    {where_sql}
    ORDER BY tramo_ventas DESC, trabajadores DESC
    LIMIT ? OFFSET ?
    """
    cursor.execute(sql, params + [limit, offset])
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": rows
    }

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM empresas")
    total_empresas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM empresas WHERE termino_giro IS NULL OR termino_giro = ''")
    activas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM empresas WHERE crm_estado != 'Nuevo'")
    prospectos_crm = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT crm_estado, COUNT(*) as cant 
        FROM empresas 
        WHERE crm_estado != 'Nuevo'
        GROUP BY crm_estado
    """)
    estados_crm = {r["crm_estado"]: r["cant"] for r in cursor.fetchall()}
    
    cursor.execute("""
        SELECT comuna, COUNT(*) as cant 
        FROM empresas 
        WHERE comuna IS NOT NULL AND comuna != ''
        GROUP BY comuna 
        ORDER BY cant DESC 
        LIMIT 10
    """)
    top_comunas = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT rubro, COUNT(*) as cant 
        FROM empresas 
        WHERE rubro IS NOT NULL AND rubro != ''
        GROUP BY rubro 
        ORDER BY cant DESC 
        LIMIT 10
    """)
    top_rubros = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total": total_empresas,
        "activas": activas,
        "prospectos_crm": prospectos_crm,
        "estados_crm": estados_crm,
        "top_comunas": top_comunas,
        "top_rubros": top_rubros
    }

def get_filter_options() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT region FROM empresas WHERE region IS NOT NULL AND region != '' ORDER BY region")
    regiones = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT comuna FROM empresas WHERE comuna IS NOT NULL AND comuna != '' ORDER BY comuna")
    comunas = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT rubro FROM empresas WHERE rubro IS NOT NULL AND rubro != '' ORDER BY rubro")
    rubros = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    return {
        "regiones": regiones,
        "comunas": comunas,
        "rubros": rubros,
        "estados_crm": ["Nuevo", "Por Contactar", "Visita Agendada", "En Negociación", "Cliente Ganado", "Descartado"],
        "tramos_venta": [
            {"id": 1, "nombre": "Sin ventas (0 UF)"},
            {"id": 2, "nombre": "0.01 a 200 UF"},
            {"id": 3, "nombre": "200.01 a 600 UF"},
            {"id": 4, "nombre": "600.01 a 2.400 UF (Micro)"},
            {"id": 5, "nombre": "2.400.01 a 5.000 UF (Pequeña 1)"},
            {"id": 6, "nombre": "5.000.01 a 10.000 UF (Pequeña 2)"},
            {"id": 7, "nombre": "10.000.01 a 25.000 UF (Pequeña 3)"},
            {"id": 8, "nombre": "25.000.01 a 50.000 UF (Mediana 1)"},
            {"id": 9, "nombre": "50.000.01 a 100.000 UF (Mediana 2)"},
            {"id": 10, "nombre": "Más de 100.000 UF (Grande)"}
        ]
    }

def update_crm_status(rut: str, estado: str, notas: Optional[str] = None, email: Optional[str] = None, telefono: Optional[str] = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = ["crm_estado = ?"]
    values = [estado]
    
    if notas is not None:
        fields.append("crm_notas = ?")
        values.append(notas)
    if email is not None:
        fields.append("contacto_email = ?")
        values.append(email)
    if telefono is not None:
        fields.append("contacto_telefono = ?")
        values.append(telefono)
        
    fields.append("actualizado_en = CURRENT_TIMESTAMP")
    values.append(rut)
    
    join_str = ", ".join(fields)
    sql = f"UPDATE empresas SET {join_str} WHERE rut = ?"
    cursor.execute(sql, values)
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def save_route(nombre: str, fecha: str, comuna: str, ruts: List[str], notas: str = "") -> int:
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rutas (nombre, fecha, comuna, notas, ruts_ordenados)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, fecha, comuna, notas, json.dumps(ruts)))
    route_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return route_id

def get_routes() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, fecha, comuna, notas, ruts_ordenados, creado_en FROM rutas ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
