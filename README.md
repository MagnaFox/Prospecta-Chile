# ProspectaChile B2B 🚀
### Plataforma de Prospección Comercial y Planificación de Rutas para Automatización Contable en Chile

ProspectaChile B2B es una solución integral diseñada para captadores y ejecutivos comerciales que ofrecen servicios y software de automatización contable (conciliación bancaria, emisión/recepción de facturas, honorarios y cobranza).

La aplicación procesa y estructura el universo de contribuyentes del **Servicio de Impuestos Internos (SII)**, permitiendo:
1. **Segmentar el mercado objetivo (ICP):** Filtrar por empresas activas, tramo de ventas (PyME tramos 3 a 8), número de trabajadores y rubros de alta carga contable (comercio, gastronomía, logística, servicios, manufactura).
2. **Planificar Rutas de Visita en Terreno:** Agrupar prospectos por comuna y eje comercial (corredores de oficinas) para visitar hasta 8-10 empresas a pie o en auto por jornada, con exportación directa de waypoints a **Google Maps**.
3. **Optimizar Contacto Remoto:** Enriquecer datos con la **API de Mercado Público** (búsqueda de teléfonos y correos corporativos registrados) y accesos directos de 1-clic a **LinkedIn** para ubicar al Contador General, GAF o Gerente de Operaciones.
4. **Pipeline Comercial Integrado:** Seguimiento de estados (*Por Contactar, Visita Agendada, Interesado, Cliente Ganado*) y bitácora de notas.

---

## 🛠️ Cómo Iniciar la Aplicación

No requiere instalaciones complejas ni dependencias externas pesadas (funciona con la biblioteca estándar de Python):

`ash
cd C:\Users\MagnaFox\.gemini\antigravity\scratch\prospecta-chile
python run.py
`

El navegador se abrirá automáticamente en:
👉 **http://localhost:8080**

---

## 📂 Estructura del Proyecto

* 
un.py: Lanzador principal que inicia el servidor local y abre la interfaz web.
* server.py: Servidor HTTP con API REST para filtros, exportación CSV, agrupamiento de rutas y CRM.
* core/database.py: Esquema SQLite con índices optimizados para consultas instantáneas.
* core/enricher.py: Conector para la API de Mercado Público y enlaces inteligentes de prospección.
* core/router.py: Motor de agrupamiento geográfico por corredores comerciales y generación de rutas para Google Maps.
* core/importer.py: Generador de dataset enriquecido y normalizador de datos.
* core/sii_sync.py: Descargador e ingestor automático de los archivos ZIP oficiales del SII.
* ui/: Dashboard interactivo (TailwindCSS, Lucide Icons, Leaflet OpenStreetMap).
* 	est_app.py: Suite de pruebas automatizadas.

---

## 🔄 Sincronización con el Archivo Completo del SII

Para descargar e incorporar la base de datos nacional completa del SII (+500.000 empresas):

`ash
python -m core.sii_sync
`
