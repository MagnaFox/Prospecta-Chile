"""
SII Full Dataset Sync Pipeline
Downloads and streams the official SII open data directly into SQLite
"""
import urllib.request
import zipfile
import io
import os
import sqlite3
import time
from .database import get_connection, init_db

NOMINA_URLS = {
    "empresas": "https://www.sii.cl/estadisticas/nominas/PUB_EMPRESAS_PJ_2020_A_2024.zip",
    "direcciones": "https://www.sii.cl/estadisticas/nominas/PUB_NOM_DIRECCIONES.zip"
}

def sync_sii_full(data_dir: str = None, limit_records: int = None):
    """
    Syncs companies and addresses directly from SII archives.
    """
    if not data_dir:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProspectaChile/1.0"}
    
    print("[SII Sync] Iniciando descarga e ingesta de datos del SII...")
    
    # 1. Download PUB_EMPRESAS_PJ_2020_A_2024.zip if not present
    zip_path = os.path.join(data_dir, "PUB_EMPRESAS_PJ_2020_A_2024.zip")
    if not os.path.exists(zip_path):
        print(f"[SII Sync] Descargando nómina de empresas desde {NOMINA_URLS['empresas']}...")
        req = urllib.request.Request(NOMINA_URLS["empresas"], headers=headers)
        with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as out:
            chunk = resp.read(1024 * 1024)
            while chunk:
                out.write(chunk)
                chunk = resp.read(1024 * 1024)
        print("[SII Sync] Descarga completada.")
        
    # Read the latest year file (2024) inside the zip
    with zipfile.ZipFile(zip_path, "r") as z:
        # Find latest year file
        txt_files = [f for f in z.namelist() if f.endswith(".txt")]
        txt_files.sort(reverse=True)
        target_file = txt_files[0] if txt_files else None
        
        if target_file:
            print(f"[SII Sync] Procesando archivo {target_file}...")
            with z.open(target_file) as f:
                header = f.readline().decode("latin1").strip().split("\t")
                print(f"[SII Sync] Cabeceras: {len(header)} columnas encontradas.")
                
                count = 0
                batch = []
                for line in f:
                    try:
                        row = line.decode("latin1", errors="ignore").strip().split("\t")
                        if len(row) >= 20:
                            # Mapping:
                            # 1: RUT, 2: DV, 3: Razon Social, 4: Tramo Ventas, 5: Trabajadores
                            # 6: Fecha Inicio, 7: Fecha TG, 14: Rubro, 16: Actividad, 17: Region, 19: Comuna
                            rut = row[1].strip()
                            dv = row[2].strip()
                            razon = row[3].strip()
                            tramo = int(row[4]) if row[4].isdigit() else 0
                            trab = int(row[5]) if row[5].isdigit() else 0
                            ini = row[6].strip()
                            tg = row[7].strip() or None
                            rubro = row[14].strip()
                            act = row[16].strip()
                            reg = row[17].strip()
                            com = row[19].strip()
                            
                            batch.append((rut, dv, razon, tramo, trab, ini, tg, rubro, act, reg, com))
                            count += 1
                            
                            if len(batch) >= 5000:
                                cursor.executemany("""
                                    INSERT OR REPLACE INTO empresas (
                                        rut, dv, razon_social, tramo_ventas, trabajadores, 
                                        inicio_actividades, termino_giro, rubro, actividad_economica, 
                                        region, comuna
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, batch)
                                conn.commit()
                                batch = []
                                print(f"[SII Sync] {count} empresas procesadas...")
                                
                            if limit_records and count >= limit_records:
                                break
                    except Exception as e:
                        continue
                        
                if batch:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO empresas (
                            rut, dv, razon_social, tramo_ventas, trabajadores, 
                            inicio_actividades, termino_giro, rubro, actividad_economica, 
                            region, comuna
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    
                print(f"[SII Sync] Total de empresas sincronizadas: {count}")
                
    conn.close()

if __name__ == "__main__":
    sync_sii_full(limit_records=50000)
