"""
Route clustering and optimization for in-person and remote sales routes
"""
from typing import List, Dict, Any

# Approximate coordinates for main Chilean communes to enable cluster mapping
COMUNA_COORDS = {
    "SANTIAGO": (-33.4372, -70.6506),
    "PROVIDENCIA": (-33.4314, -70.6190),
    "LAS CONDES": (-33.4116, -70.5815),
    "VITACURA": (-33.3887, -70.5847),
    "LO BARNECHEA": (-33.3533, -70.5178),
    "NUNOA": (-33.4569, -70.5976),
    "QUILICURA": (-33.3644, -70.7308),
    "HUECHURABA": (-33.3742, -70.6358),
    "SAN JOAQUIN": (-33.4939, -70.6277),
    "PUDAHUEL": (-33.4419, -70.7678),
    "MAIPU": (-33.5111, -70.7578),
    "VALPARAISO": (-33.0472, -71.6127),
    "VINA DEL MAR": (-33.0245, -71.5518),
    "CONCEPCION": (-36.8270, -73.0503),
    "ANTOFAGASTA": (-23.6509, -70.3975),
    "PUERTO MONTT": (-41.4693, -72.9424),
    "LA SERENA": (-29.9027, -71.2520),
    "RANCAGUA": (-34.1708, -70.7444),
    "TALCA": (-35.4264, -71.6554),
    "TEMUCO": (-38.7359, -72.5904)
}

def cluster_by_corridor(companies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups companies by street or avenue to plan a walking or short driving route.
    """
    clusters = {}
    for comp in companies:
        street = (comp.get("calle") or "SIN DIRECCION REGISTRADA").strip().upper()
        # Clean generic words
        main_street = street.replace("AVENIDA", "AV.").replace("PASAJE", "PSJE.").strip()
        if main_street not in clusters:
            clusters[main_street] = []
        clusters[main_street].append(comp)
    
    # Sort by cluster size descending
    sorted_clusters = dict(sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True))
    return sorted_clusters

def build_route_plan(companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates an ordered itinerary with google maps route link.
    """
    waypoints = []
    for c in companies:
        addr = f"{c.get('calle', '')} {c.get('numero', '')}, {c.get('comuna', '')}".strip()
        if addr:
            waypoints.append(addr)
            
    maps_route_url = ""
    if waypoints:
        import urllib.parse
        base_url = "https://www.google.com/maps/dir/"
        encoded_pts = "/".join(urllib.parse.quote(p) for p in waypoints[:10])
        maps_route_url = base_url + encoded_pts
        
    return {
        "total_visitas": len(companies),
        "empresas_ordenadas": companies,
        "google_maps_route": maps_route_url
    }
