"""
Importer and seed generator for SII companies dataset
"""
import os
import random
import sqlite3
from typing import List, Dict, Any
from .database import get_connection, init_db
from .router import COMUNA_COORDS

SEED_COMPANIES = [
    ("76123456", "K", "DISTRIBUIDORA DE ALIMENTOS DEL VALLE SPA", 7, 28, "2012-03-15", None, "COMERCIO AL POR MAYOR Y MENOR", "VENTA AL POR MAYOR DE ALIMENTOS Y BEBIDAS", "XIII REGION METROPOLITANA", "SANTIAGO", "AV. PROVIDENCIA", "1208", "OF 402"),
    ("76987654", "3", "LOGISTICA Y TRANSPORTES TRANSCHILE LIMITADA", 8, 45, "2010-06-20", None, "TRANSPORTE Y ALMACENAMIENTO", "TRANSPORTE INTERURBANO DE CARGA POR CARRETERA", "XIII REGION METROPOLITANA", "QUILICURA", "AMERICO VESPUCIO NORTE", "2350", "MODULO B"),
    ("77123987", "4", "CONSTRUCTORA E INMOBILIARIA CORDILLERA S.A.", 9, 82, "2008-01-10", None, "CONSTRUCCION", "CONSTRUCCION DE EDIFICIOS RESIDENCIALES", "XIII REGION METROPOLITANA", "LAS CONDES", "AV. APOQUINDO", "4501", "PISO 8"),
    ("76554433", "2", "GASTRONOMIA Y SERVICIOS GOURMET SPA", 6, 18, "2016-11-04", None, "ACTIVIDADES DE ALOJAMIENTO Y DE SERVICIO DE COMIDAS", "RESTAURANTES Y SERVICIOS MOVILES DE COMIDAS", "XIII REGION METROPOLITANA", "PROVIDENCIA", "MANUEL MONTT", "340", ""),
    ("77443322", "1", "SERVICIOS MEDICOS Y CLINICOS SAN CRISTOBAL SPA", 8, 34, "2014-08-22", None, "ACTIVIDADES DE ATENCION DE LA SALUD HUMANA", "ACTIVIDADES DE CENTROS MEDICOS Y DE ATENCION DENTAL", "XIII REGION METROPOLITANA", "PROVIDENCIA", "AV. PROVIDENCIA", "1650", "OF 301"),
    ("76234567", "5", "IMPORTADORA Y EXPORTADORA PACIFICO SUR LTDA", 7, 15, "2015-04-12", None, "COMERCIO AL POR MAYOR Y MENOR", "VENTA AL POR MAYOR DE MAQUINARIA Y EQUIPO", "XIII REGION METROPOLITANA", "SANTIAGO", "HUERFANOS", "1160", "OF 802"),
    ("76889900", "8", "ASESORIAS Y SOLUCIONES EN TECNOLOGIA CLOUD SPA", 6, 12, "2019-02-18", None, "INFORMACION Y COMUNICACIONES", "DESARROLLO DE PROGRAMAS INFORMATICOS Y CONSULTORIA", "XIII REGION METROPOLITANA", "LAS CONDES", "AV. EL GOLF", "40", "OF 601"),
    ("77556677", "9", "CENTRO DENTAL Y ESTETICA INTEGRAL VITACURA LTDA", 5, 8, "2018-09-01", None, "ACTIVIDADES DE ATENCION DE LA SALUD HUMANA", "ACTIVIDADES DE PRACTICA MEDICA Y ODONTOLOGICA", "XIII REGION METROPOLITANA", "VITACURA", "AV. VITACURA", "3565", "OF 204"),
    ("76332211", "0", "MAESTRANZA E INGENIERIA INDUSTRIAL DEL SUR SPA", 7, 24, "2011-10-30", None, "INDUSTRIA MANUFACTURERA", "FABRICACION DE ESTRUCTURAS METALICAS", "VIII REGION DEL BIOBIO", "CONCEPCION", "AV. PAICAVI", "1850", ""),
    ("77889911", "6", "OPERADORA HOTELERA Y TURISMO AUSTRAL LIMITADA", 6, 19, "2013-12-05", None, "ACTIVIDADES DE ALOJAMIENTO Y DE SERVICIO DE COMIDAS", "HOTELES Y ALOJAMIENTOS SIMILARES", "X REGION DE LOS LAGOS", "PUERTO MONTT", "DIEGO PORTALES", "860", ""),
    ("76445566", "7", "CADENA FARMACEUTICA Y VENTA AL DETALLE LTDA", 8, 52, "2009-05-14", None, "COMERCIO AL POR MAYOR Y MENOR", "VENTA AL POR MENOR DE PRODUCTOS FARMACEUTICOS", "V REGION DE VALPARAISO", "VINA DEL MAR", "AV. LIBERTAD", "1348", ""),
    ("77221100", "8", "AGENCIA DE PUBLICIDAD Y MARKETING DIGITAL SPA", 5, 9, "2020-01-20", None, "ACTIVIDADES PROFESIONALES, CIENTIFICAS Y TECNICAS", "ACTIVIDADES DE AGENCIAS DE PUBLICIDAD", "XIII REGION METROPOLITANA", "NUNOA", "AV. IRARRAZAVAL", "2401", "OF 505"),
    ("76778899", "1", "SERVICIOS DE SEGURIDAD Y VIGILANCIA PRIVADA LTDA", 7, 38, "2012-07-19", None, "ACTIVIDADES DE SERVICIOS ADMINISTRATIVOS Y DE APOYO", "ACTIVIDADES DE SEGURIDAD PRIVADA Y SERVICIOS DE SISTEMAS", "XIII REGION METROPOLITANA", "SANTIAGO", "MONEDA", "970", "OF 1104"),
    ("76001122", "3", "AUTOMOTRIZ Y REPUESTOS DEL VALLE CENTRAL SPA", 6, 14, "2017-03-25", None, "COMERCIO AL POR MAYOR Y MENOR", "MANTENIMIENTO Y REPARACION DE VEHICULOS AUTOMOTORES", "VI REGION DEL LIBERTADOR GRAL. B. OHIGGINS", "RANCAGUA", "AV. BERNARDO O HIGGINS", "450", "")
]

# Generate realistic PyMEs across Chilean commercial centers
RUBROS_LIST = [
    ("COMERCIO AL POR MAYOR Y MENOR", ["VENTA AL POR MAYOR DE ENSERES DOMESTICOS", "COMERCIO AL POR MENOR EN COMERCIOS NO ESPECIALIZADOS", "VENTA AL POR MAYOR DE MATERIALES DE CONSTRUCCION", "VENTA DE ARTICULOS DE FERRETERIA Y PINTURAS"]),
    ("ACTIVIDADES PROFESIONALES, CIENTIFICAS Y TECNICAS", ["ACTIVIDADES JURIDICAS Y DE CONTABILIDAD", "ACTIVIDADES DE CONSULTORIA DE GESTION", "SERVICIOS DE ARQUITECTURA E INGENIERIA"]),
    ("TRANSPORTE Y ALMACENAMIENTO", ["TRANSPORTE DE CARGA POR CARRETERA", "OTRAS ACTIVIDADES DE APOYO AL TRANSPORTE", "SERVICIOS DE MENSAJERIA Y LOGISTICA"]),
    ("ACTIVIDADES DE ALOJAMIENTO Y DE SERVICIO DE COMIDAS", ["RESTAURANTES Y SERVICIOS MOVILES DE COMIDAS", "SUMINISTRO DE COMIDAS POR ENCARGO", "ACTIVIDADES DE BARES Y CAFETERIAS"]),
    ("INDUSTRIA MANUFACTURERA", ["ELABORACION DE PRODUCTOS ALIMENTICIOS", "FABRICACION DE PRODUCTOS METALICOS", "IMPRESION Y ACTIVIDADES DE SERVICIOS CONEXAS"]),
    ("CONSTRUCCION", ["CONSTRUCCION DE OTRAS OBRAS DE INGENIERIA CIVIL", "INSTALACIONES ELECTRICAS Y DE GASFITERIA", "TERMINACION Y ACABADO DE EDIFICIOS"])
]

COMUNAS_CALLES = {
    "PROVIDENCIA": [
        ("AV. PROVIDENCIA", ["1200", "1650", "2050", "2450"]),
        ("AV. PEDRO DE VALDIVIA", ["100", "350", "720", "1200"]),
        ("AV. NUEVA PROVIDENCIA", ["1881", "1945", "2155", "2250"]),
        ("MANUEL MONTT", ["100", "340", "850"]),
        ("AV. EL BOSQUE", ["10", "150", "220"])
    ],
    "LAS CONDES": [
        ("AV. APOQUINDO", ["3000", "4500", "5550", "6415"]),
        ("AV. EL GOLF", ["40", "99", "150"]),
        ("ISIDORA GOYENECHEA", ["2800", "3000", "3250"]),
        ("AV. ALONSO DE CORDOVA", ["5150", "5870"]),
        ("AV. AMERICO VESPUCIO SUR", ["100", "850"])
    ],
    "SANTIAGO": [
        ("HUERFANOS", ["770", "1055", "1160"]),
        ("AGUSTINAS", ["853", "1185", "1442"]),
        ("MONEDA", ["970", "1040", "1137"]),
        ("AHUMADA", ["131", "254", "312"]),
        ("TEATINOS", ["220", "333", "449"])
    ],
    "HUECHURABA": [
        ("AV. DEL VALLE", ["550", "720", "850"]),
        ("AV. DEL PARQUE", ["4161", "4928"]),
        ("AV. SANTA CLARA", ["301", "421"])
    ],
    "QUILICURA": [
        ("AMERICO VESPUCIO NORTE", ["1400", "2350"]),
        ("PANAMERICANA NORTE", ["5500", "7800"]),
        ("AV. SAN IGNACIO", ["200", "500"])
    ],
    "NUNOA": [
        ("AV. IRARRAZAVAL", ["1900", "2401", "3600"]),
        ("MANUEL MONTT", ["1800", "2200"]),
        ("JOSE DOMINGO CANAS", ["1200", "1500"])
    ],
    "VITACURA": [
        ("AV. VITACURA", ["2909", "3565", "4380"]),
        ("AV. NUEVA COSTANERA", ["3800", "4100"])
    ]
}

def seed_sample_dataset(count: int = 1500):
    """Seeds rich, realistic data for instantaneous exploration"""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM empresas")
    if cursor.fetchone()[0] >= count:
        conn.close()
        return
        
    print(f"Generando dataset de demostracion optimizado con {count} empresas...")
    
    # Insert curated high-value companies first
    for item in SEED_COMPANIES:
        rut, dv, razon, tramo, trab, ini, tg, rubro, act, reg, com, calle, num, depto = item
        dir_comp = f"{calle} {num} {depto}, {com}".strip()
        base_lat, base_lon = COMUNA_COORDS.get(com, (-33.4372, -70.6506))
        lat = base_lat + random.uniform(-0.01, 0.01)
        lon = base_lon + random.uniform(-0.01, 0.01)
        
        cursor.execute("""
            INSERT OR REPLACE INTO empresas (
                rut, dv, razon_social, tramo_ventas, trabajadores, 
                inicio_actividades, termino_giro, rubro, actividad_economica, 
                region, comuna, calle, numero, depto, direccion_completa, lat, lon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rut, dv, razon, tramo, trab, ini, tg, rubro, act, reg, com, calle, num, depto, dir_comp, lat, lon))
        
    # Generate bulk realistic PyMEs
    prefix = ["SERVICIOS", "COMERCIAL", "DISTRIBUIDORA", "CONSULTORA", "LOGISTICA", "CONSTRUCTORA", "SOLUCIONES", "TECNOLOGIAS", "INGENIERIA", "TRANSPORTES", "IMPORTADORA", "CLINICA", "RESTAURANTE", "ASESORIAS"]
    suffix = ["CHILE", "ANDINA", "DEL PACIFICO", "GLOBAL", "INTEGRAL", "DEL VALLE", "METROPOLITANA", "SUR", "NORTE", "AVANZADA", "CENTRAL", "PROFESIONAL", "PRIME", "EXPRESS"]
    legal_forms = ["SPA", "LIMITADA", "S.A.", "E.I.R.L."]
    
    start_rut = 76500000
    for i in range(count):
        curr_rut = str(start_rut + i)
        dv = str(random.randint(0, 9)) if random.random() > 0.1 else "K"
        p = random.choice(prefix)
        s = random.choice(suffix)
        form = random.choice(legal_forms)
        razon = f"{p} {s} {random.choice(['SERVICIOS', 'GESTION', 'OPERACIONES', 'DESARROLLO', ''])} {form}".replace("  ", " ").strip()
        
        # Most companies are PyMEs (tramos 3 to 8: target for accounting automation)
        tramo = random.choices([2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[5, 15, 25, 20, 15, 10, 6, 3, 1])[0]
        trabajadores = max(1, int(tramo * random.uniform(1.8, 4.5)))
        
        year = random.randint(2005, 2024)
        m = str(random.randint(1, 12)).zfill(2)
        d = str(random.randint(1, 28)).zfill(2)
        ini = f"{year}-{m}-{d}"
        
        # 95% active, 5% closed
        tg = None
        if random.random() < 0.05:
            tg = f"{random.randint(2021, 2025)}-{m}-{d}"
            
        rubro_info = random.choice(RUBROS_LIST)
        rubro = rubro_info[0]
        act = random.choice(rubro_info[1])
        
        com = random.choice(list(COMUNAS_CALLES.keys()))
        reg = "XIII REGION METROPOLITANA"
        calle_info = random.choice(COMUNAS_CALLES[com])
        calle = calle_info[0]
        num = random.choice(calle_info[1])
        depto = f"OF {random.randint(201, 1405)}" if random.random() > 0.3 else ""
        dir_comp = f"{calle} {num} {depto}, {com}".strip()
        
        base_lat, base_lon = COMUNA_COORDS.get(com, (-33.4372, -70.6506))
        lat = base_lat + random.uniform(-0.015, 0.015)
        lon = base_lon + random.uniform(-0.015, 0.015)
        
        cursor.execute("""
            INSERT OR IGNORE INTO empresas (
                rut, dv, razon_social, tramo_ventas, trabajadores, 
                inicio_actividades, termino_giro, rubro, actividad_economica, 
                region, comuna, calle, numero, depto, direccion_completa, lat, lon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (curr_rut, dv, razon, tramo, trabajadores, ini, tg, rubro, act, reg, com, calle, num, depto, dir_comp, lat, lon))
        
    conn.commit()
    conn.close()
    print("Demostracion cargada exitosamente.")
