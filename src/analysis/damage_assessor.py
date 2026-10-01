"""
Damage Assessment Engine: Infrastructure Impact Analysis
Intersects satellite-derived flood & debris masks with OpenStreetMap roads and bridges.
Identifies severed road segments and destroyed bridges.
"""

import os
import json
from typing import Dict, Any, List
import shapely.geometry
from shapely.ops import unary_union


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OSM_DIR = os.path.join(DATA_DIR, "osm")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")


class InfrastructureDamageAssessor:
    """Evaluates physical damage to roads and bridges caused by flood and debris."""

    def __init__(self, roads_geojson_path: str = None, flood_geojson_path: str = None):
        if roads_geojson_path is None:
            roads_geojson_path = os.path.join(OSM_DIR, "pre_event_roads.geojson")
        if flood_geojson_path is None:
            flood_geojson_path = os.path.join(OUTPUT_DIR, "flood_and_debris_impact.geojson")
            
        self.roads_path = roads_geojson_path
        self.flood_path = flood_geojson_path

    def assess_damage(self) -> Dict[str, Any]:
        """Runs spatial intersection between transport infrastructure and hazard zones."""
        with open(self.roads_path, "r", encoding="utf-8") as f:
            roads_fc = json.load(f)
            
        with open(self.flood_path, "r", encoding="utf-8") as f:
            flood_fc = json.load(f)

        # Build unified geometry for water and debris polygons
        water_geoms = []
        debris_geoms = []
        for feat in flood_fc["features"]:
            poly = shapely.geometry.shape(feat["geometry"])
            if feat["properties"]["hazard_type"] == "water":
                water_geoms.append(poly)
            else:
                debris_geoms.append(poly)
                
        water_union = unary_union(water_geoms) if water_geoms else shapely.geometry.Polygon()
        debris_union = unary_union(debris_geoms) if debris_geoms else shapely.geometry.Polygon()
        hazard_union = unary_union([water_union, debris_union])

        total_road_length_km = 0.0
        severed_road_length_km = 0.0
        damaged_roads = []
        intact_roads = []
        severed_bridges = []

        for feat in roads_fc["features"]:
            geom = shapely.geometry.shape(feat["geometry"])
            props = feat["properties"]
            seg_len = props.get("length_km", 0.0)
            total_road_length_km += seg_len
            
            is_bridge = props.get("bridge", "no") == "yes"

            # Check for intersection with hazard zones
            if geom.intersects(hazard_union):
                intersection = geom.intersection(hazard_union)
                # Estimate severed length
                ratio = min(1.0, intersection.length / geom.length) if geom.length > 0 else 1.0
                severed_km = round(seg_len * ratio, 2)
                severed_road_length_km += severed_km
                
                # Determine primary damage cause
                cause = "Debris Flow Blockage" if geom.intersects(debris_union) else "Submerged by Floodwaters"
                
                status_props = {
                    **props,
                    "status": "SEVERED",
                    "damage_cause": cause,
                    "severed_length_km": severed_km,
                    "damage_ratio_pct": round(ratio * 100, 1),
                    "color": "#FF0000" if is_bridge else "#FF4500"
                }
                
                damaged_roads.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": status_props
                })
                
                if is_bridge:
                    severed_bridges.append({
                        "name": props["name"],
                        "road_id": props["id"],
                        "damage_cause": cause
                    })
            else:
                intact_roads.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": {
                        **props,
                        "status": "PASSABLE",
                        "color": "#32CD32"
                    }
                })

        summary = {
            "total_network_km": round(total_road_length_km, 2),
            "severed_road_km": round(severed_road_length_km, 2),
            "damaged_pct": round((severed_road_length_km / total_road_length_km * 100) if total_road_length_km else 0, 1),
            "total_segments_analyzed": len(roads_fc["features"]),
            "severed_segments_count": len(damaged_roads),
            "passable_segments_count": len(intact_roads),
            "severed_bridges_count": len(severed_bridges),
            "severed_bridges": severed_bridges
        }

        # Save output GeoJSON
        damaged_network_fc = {
            "type": "FeatureCollection",
            "attribution": "FloodWatch Space Damage Assessment. © OpenStreetMap contributors.",
            "features": damaged_roads + intact_roads
        }
        out_path = os.path.join(OUTPUT_DIR, "damage_assessment_roads.geojson")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(damaged_network_fc, f, indent=2)

        summary_path = os.path.join(OUTPUT_DIR, "damage_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return {
            "summary": summary,
            "damaged_network_geojson": damaged_network_fc,
            "intact_roads": intact_roads,
            "damaged_roads": damaged_roads
        }


if __name__ == "__main__":
    assessor = InfrastructureDamageAssessor()
    res = assessor.assess_damage()
    s = res["summary"]
    print("Damage Assessment Completed:")
    print(f"  - Total Road Network: {s['total_network_km']} km")
    print(f"  - Severed Road Length: {s['severed_road_km']} km ({s['damaged_pct']}%)")
    print(f"  - Severed Bridges: {s['severed_bridges_count']}")
    for b in s['severed_bridges']:
        print(f"    * {b['name']}: {b['damage_cause']}")
