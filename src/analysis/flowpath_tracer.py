"""
Flowpath & Valley Downstream Tracer (Track B Bonus Feature)
Given an upstream hazard release point (e.g., glacier lake outburst / avalanche collapse),
traces the flow corridor down the valley using elevation gradients and identifies all settlements along the path.
"""

import os
import json
import math
from typing import Dict, Any, List, Tuple


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OSM_DIR = os.path.join(DATA_DIR, "osm")


class ElevationFlowpathTracer:
    """Downstream flood and debris flowpath tracer along the Himalayan river gradient."""

    def __init__(self, settlements_path: str = None):
        if settlements_path is None:
            settlements_path = os.path.join(OSM_DIR, "settlements.json")
        with open(settlements_path, "r", encoding="utf-8") as f:
            self.settlements = json.load(f)
            
        # Sort settlements from North (High Elevation Upstream) to South (Low Elevation Downstream)
        self.settlements.sort(key=lambda s: s["lat"], reverse=True)

    def trace_downstream_flow(
        self,
        upstream_lat: float = 28.32,
        upstream_lon: float = 85.38,
        upstream_elevation_m: float = 4300,
        flow_velocity_ms: float = 8.0 # Typical Himalayan debris torrent speed (~28.8 km/h)
    ) -> Dict[str, Any]:
        """
        Traces flow path from release point down the valley corridor.
        Computes distance, wave arrival time, and endangered settlements.
        """
        downstream_settlements = []
        cumulative_dist_km = 0.0
        prev_lat, prev_lon = upstream_lat, upstream_lon
        prev_elev = upstream_elevation_m

        for s in self.settlements:
            # Check if settlement is downstream (lower latitude along the south-flowing corridor)
            if s["lat"] < upstream_lat:
                step_km = self._haversine(prev_lat, prev_lon, s["lat"], s["lon"])
                cumulative_dist_km += step_km
                
                # Flow time calculation: time = distance / velocity
                arrival_time_min = round((cumulative_dist_km * 1000.0) / (flow_velocity_ms * 60.0), 1)
                elev_drop_m = round(prev_elev - s.get("elevation_m", 0), 1)
                
                downstream_settlements.append({
                    "name": s["name"],
                    "name_ne": s.get("name_ne", ""),
                    "lat": s["lat"],
                    "lon": s["lon"],
                    "elevation_m": s.get("elevation_m", 0),
                    "distance_downstream_km": round(cumulative_dist_km, 2),
                    "estimated_arrival_minutes": arrival_time_min,
                    "elevation_drop_from_origin_m": round(upstream_elevation_m - s.get("elevation_m", 0), 1)
                })
                
                prev_lat, prev_lon = s["lat"], s["lon"]
                prev_elev = s.get("elevation_m", 0)

        return {
            "origin": {
                "description": "Glacier Avalanche Inception Point (Northern Rasuwa)",
                "lat": upstream_lat,
                "lon": upstream_lon,
                "elevation_m": upstream_elevation_m,
                "estimated_flow_velocity_kmh": round(flow_velocity_ms * 3.6, 1)
            },
            "settlements_in_flow_path_count": len(downstream_settlements),
            "total_downstream_corridor_km": round(cumulative_dist_km, 2),
            "downstream_sequence": downstream_settlements
        }

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c


if __name__ == "__main__":
    tracer = ElevationFlowpathTracer()
    res = tracer.trace_downstream_flow()
    print("Upstream Hazard Release Traced Downstream:")
    print(f"  - Total Settlements along Flow Path: {res['settlements_in_flow_path_count']}")
    print(f"  - Total Corridor Length: {res['total_downstream_corridor_km']} km")
    for s in res["downstream_sequence"][:5]:
        print(f"    * {s['name']} (+{s['distance_downstream_km']} km) - Arrival in ~{s['estimated_arrival_minutes']} mins")
