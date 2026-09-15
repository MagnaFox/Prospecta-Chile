# test_app.py
import os
import sys
import unittest

BASE_DIR = r"C:\Users\MagnaFox\.gemini\antigravity\scratch\prospecta-chile"
sys.path.insert(0, BASE_DIR)

from core.database import (
    init_db, query_companies, get_stats, get_filter_options,
    update_crm_status, save_route, get_routes, get_connection
)
from core.enricher import get_external_links, query_mercadopublico
from core.router import cluster_by_corridor, build_route_plan
from core.importer import seed_sample_dataset

class TestProspectaChile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_sample_dataset(count=500)

    def test_database_stats(self):
        stats = get_stats()
        self.assertGreater(stats["total"], 0)
        self.assertGreater(stats["activas"], 0)
        self.assertTrue(isinstance(stats["top_comunas"], list))
        print(f"Stats OK: {stats['total']} empresas, {stats['activas']} activas")

    def test_query_filters(self):
        # Test comuna filter
        res = query_companies(comuna="PROVIDENCIA", limit=10)
        self.assertGreater(len(res["results"]), 0)
        for r in res["results"]:
            self.assertEqual(r["comuna"], "PROVIDENCIA")
            
        # Test tramo filter
        res_tramo = query_companies(tramo_min=5, limit=10)
        for r in res_tramo["results"]:
            self.assertGreaterEqual(r["tramo_ventas"], 5)
            
        # Test text search
        res_text = query_companies(query="DISTRIBUIDORA", limit=5)
        self.assertGreater(len(res_text["results"]), 0)
        print("Query filters OK")

    def test_crm_update(self):
        res = query_companies(limit=1)
        rut = res["results"][0]["rut"]
        
        ok = update_crm_status(rut, "Visita Agendada", "Interesado en demo de conciliacion bancaria", "test@empresa.cl", "+56912345678")
        self.assertTrue(ok)
        
        # Verify persistence
        updated = query_companies(query=rut, limit=1)["results"][0]
        self.assertEqual(updated["crm_estado"], "Visita Agendada")
        self.assertEqual(updated["contacto_email"], "test@empresa.cl")
        self.assertEqual(updated["crm_notas"], "Interesado en demo de conciliacion bancaria")
        print("CRM update OK")

    def test_enricher_links(self):
        links = get_external_links("DISTRIBUIDORA DE ALIMENTOS DEL VALLE SPA", "PROVIDENCIA")
        self.assertIn("google.com", links["google_search"])
        self.assertIn("linkedin.com", links["linkedin_search"])
        self.assertIn("google.com/maps", links["google_maps"])
        print("Enricher links OK")

    def test_route_clustering(self):
        res = query_companies(comuna="PROVIDENCIA", limit=50)
        clusters = cluster_by_corridor(res["results"])
        self.assertIsInstance(clusters, dict)
        self.assertGreater(len(clusters), 0)
        
        # Build route plan
        plan = build_route_plan(res["results"][:5])
        self.assertEqual(plan["total_visitas"], 5)
        self.assertIn("google.com/maps/dir", plan["google_maps_route"])
        print("Route clustering OK")

if __name__ == "__main__":
    unittest.main(verbosity=2)
