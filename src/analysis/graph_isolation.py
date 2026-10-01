"""
Settlement Isolation Engine: Graph Network Routing & Healthcare Access Analysis
Uses NetworkX to identify settlements cut off from roads, hospitals, and relief hubs.
"""

import os
import json
import math
from typing import Dict, Any, List, Tuple
import networkx as nx
import shapely.geometry


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OSM_DIR = os.path.join(DATA_DIR, "osm")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")


class SettlementIsolationAnalyzer:
    """Constructs road graph before and after disaster to identify isolated communities."""

    def __init__(
        self,
        roads_fc_path: str = None,
        settlements_path: str = None,
        hospitals_path: str = None,
        damage_summary_path: str = None
    ):
        if roads_fc_path is None:
            roads_fc_path = os.path.join(OUTPUT_DIR, "damage_assessment_roads.geojson")
        if settlements_path is None:
            settlements_path = os.path.join(OSM_DIR, "settlements.json")
        if hospitals_path is None:
            hospitals_path = os.path.join(OSM_DIR, "hospitals.json")
            
        self.roads_path = roads_fc_path
        self.settlements_path = settlements_path
        self.hospitals_path = hospitals_path

    def analyze_isolation(self) -> Dict[str, Any]:
        """Builds pre- and post-flood graphs, performs Dijkstra routing, and categorizes isolation."""
        with open(self.roads_path, "r", encoding="utf-8") as f:
            roads_fc = json.load(f)
        with open(self.settlements_path, "r", encoding="utf-8") as f:
            settlements = json.load(f)
        with open(self.hospitals_path, "r", encoding="utf-8") as f:
            hospitals = json.load(f)

        # Build full network graph (Pre-event) and functional network graph (Post-event)
        G_pre = nx.Graph()
        G_post = nx.Graph()

        # Add edges from road features
        for feat in roads_fc["features"]:
            coords = feat["geometry"]["coordinates"]
            props = feat["properties"]
            length_km = props.get("length_km", 1.0)
            is_severed = props.get("status") == "SEVERED"

            # Node representations using string tuple coordinates rounded to 4 decimals (~10m)
            u = f"{coords[0][0]:.4f},{coords[0][1]:.4f}"
            v = f"{coords[-1][0]:.4f},{coords[-1][1]:.4f}"

            G_pre.add_edge(u, v, weight=length_km, name=props["name"], id=props["id"])
            if not is_severed:
                G_post.add_edge(u, v, weight=length_km, name=props["name"], id=props["id"])

        # Map each hospital to nearest graph node
        hospital_nodes = []
        for hosp in hospitals:
            h_lon, h_lat = hosp["lon"], hosp["lat"]
            nearest_node = self._find_nearest_node(G_pre, h_lon, h_lat)
            hospital_nodes.append({
                "hospital": hosp,
                "node": nearest_node
            })

        settlement_results = []
        isolated_count = 0
        impaired_count = 0
        accessible_count = 0

        for s in settlements:
            s_lon, s_lat = s["lon"], s["lat"]
            s_node = self._find_nearest_node(G_pre, s_lon, s_lat)

            # Pre-event shortest route to any hospital
            best_pre_dist = float("inf")
            best_pre_hosp = None
            for hn in hospital_nodes:
                try:
                    dist = nx.shortest_path_length(G_pre, s_node, hn["node"], weight="weight")
                    if dist < best_pre_dist:
                        best_pre_dist = dist
                        best_pre_hosp = hn["hospital"]["name"]
                except nx.NetworkXNoPath:
                    pass

            # Post-event shortest route to any hospital
            best_post_dist = float("inf")
            best_post_hosp = None
            shortest_path_nodes = []
            
            if s_node in G_post:
                for hn in hospital_nodes:
                    if hn["node"] in G_post:
                        try:
                            dist = nx.shortest_path_length(G_post, s_node, hn["node"], weight="weight")
                            if dist < best_post_dist:
                                best_post_dist = dist
                                best_post_hosp = hn["hospital"]["name"]
                                shortest_path_nodes = nx.shortest_path(G_post, s_node, hn["node"], weight="weight")
                        except nx.NetworkXNoPath:
                            pass

            # Classify isolation state
            if math.isinf(best_post_dist):
                status = "CUT_OFF"
                status_label = "Completely Isolated (Road Access Severed)"
                color = "#FF0000" # Red
                isolated_count += 1
                recommended_action = "Urgent Helicopter Evacuation & Aerial Food Airdrop"
            elif best_post_dist > best_pre_dist * 1.3:
                status = "IMPAIRED"
                status_label = f"Impaired (+{round(best_post_dist - best_pre_dist, 1)} km Detour Required)"
                color = "#FFA500" # Orange
                impaired_count += 1
                recommended_action = "4x4 High-Clearance Emergency Vehicles Only"
            else:
                status = "ACCESSIBLE"
                status_label = "Direct Road Access Intact"
                color = "#2E8B57" # Green
                accessible_count += 1
                recommended_action = "Standard Emergency Supply Convoy"

            settlement_results.append({
                "name": s["name"],
                "name_ne": s.get("name_ne", ""),
                "lat": s["lat"],
                "lon": s["lon"],
                "elevation_m": s.get("elevation_m", 0),
                "status": status,
                "status_label": status_label,
                "color": color,
                "pre_event_hospital_km": round(best_pre_dist, 1) if not math.isinf(best_pre_dist) else None,
                "post_event_hospital_km": round(best_post_dist, 1) if not math.isinf(best_post_dist) else None,
                "nearest_hospital": best_post_hosp if best_post_hosp else best_pre_hosp,
                "recommended_action": recommended_action
            })

        summary = {
            "total_settlements": len(settlements),
            "isolated_settlements_count": isolated_count,
            "impaired_settlements_count": impaired_count,
            "accessible_settlements_count": accessible_count,
            "isolation_rate_pct": round((isolated_count / len(settlements)) * 100, 1),
            "isolated_settlements": [s for s in settlement_results if s["status"] == "CUT_OFF"]
        }

        # Save outputs
        res_payload = {
            "summary": summary,
            "settlements": settlement_results
        }
        out_path = os.path.join(OUTPUT_DIR, "settlement_isolation_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res_payload, f, indent=2, ensure_ascii=False)

        return res_payload

    def _find_nearest_node(self, G: nx.Graph, lon: float, lat: float) -> str:
        """Finds closest node in the road graph to a given coordinate."""
        best_node = None
        min_dist = float("inf")
        for node in G.nodes():
            n_lon, n_lat = map(float, node.split(","))
            dist = (lon - n_lon) ** 2 + (lat - n_lat) ** 2
            if dist < min_dist:
                min_dist = dist
                best_node = node
        return best_node


if __name__ == "__main__":
    analyzer = SettlementIsolationAnalyzer()
    res = analyzer.analyze_isolation()
    s = res["summary"]
    print("Settlement Isolation Analysis Completed:")
    print(f"  - Total Settlements: {s['total_settlements']}")
    print(f"  - Completely Cut Off: {s['isolated_settlements_count']} ({s['isolation_rate_pct']}%)")
    print(f"  - Impaired Access: {s['impaired_settlements_count']}")
    print(f"  - Accessible: {s['accessible_settlements_count']}")
    print("Isolated Settlements List:")
    for iso in s["isolated_settlements"]:
        print(f"    * {iso['name']} - Elevation: {iso['elevation_m']}m - Nearest: {iso['nearest_hospital']}")
