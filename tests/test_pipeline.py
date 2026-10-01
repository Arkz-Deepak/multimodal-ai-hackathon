"""
End-to-End Pipeline Verification Test Suite
Verifies all modules of the FloodWatch Space system.
"""

import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.osm_fetcher import fetch_osm_roads_overpass, get_corridor_settlements, get_emergency_hospitals
from src.data.sar_processor import SARChangeDetector
from src.analysis.damage_assessor import InfrastructureDamageAssessor
from src.analysis.graph_isolation import SettlementIsolationAnalyzer
from src.ai_copilot.sitrep_generator import SituationReportCopilot
from src.ai_copilot.qa_agent import RescueQAAgent


class TestFloodWatchSpace(unittest.TestCase):

    def test_01_osm_fetcher(self):
        """Test pre-event OSM roads, settlements, and hospitals."""
        roads = fetch_osm_roads_overpass(use_cache=True)
        settlements = get_corridor_settlements()
        hospitals = get_emergency_hospitals()
        
        self.assertGreater(len(roads["features"]), 0)
        self.assertGreater(len(settlements), 5)
        self.assertGreater(len(hospitals), 1)

    def test_02_sar_change_detection(self):
        """Test SAR backscatter differencing."""
        detector = SARChangeDetector()
        pre_vv, pre_vh, post_vv, post_vh = detector.generate_synthetic_sentinel1_pair()
        results = detector.detect_changes(pre_vv, pre_vh, post_vv, post_vh)
        
        stats = results["stats"]
        self.assertGreater(stats["water_inundation_km2"], 0)
        self.assertGreater(stats["debris_deposition_km2"], 0)
        self.assertTrue(os.path.exists(stats["geojson_path"]))

    def test_03_damage_assessment(self):
        """Test infrastructure intersection and severed road detection."""
        assessor = InfrastructureDamageAssessor()
        res = assessor.assess_damage()
        summary = res["summary"]
        
        self.assertGreater(summary["total_network_km"], 0)
        self.assertGreater(summary["severed_road_km"], 0)
        self.assertGreater(summary["severed_bridges_count"], 0)

    def test_04_graph_isolation(self):
        """Test network graph shortest-path routing and isolated settlements."""
        analyzer = SettlementIsolationAnalyzer()
        res = analyzer.analyze_isolation()
        summary = res["summary"]
        
        self.assertGreater(summary["total_settlements"], 0)
        self.assertGreater(summary["isolated_settlements_count"], 0)
        self.assertLessEqual(summary["isolated_settlements_count"], summary["total_settlements"])

    def test_05_sitrep_generator(self):
        """Test bilingual situation report generation."""
        copilot = SituationReportCopilot()
        reports = copilot.generate_bilingual_report()
        
        self.assertTrue(os.path.exists(reports["english_path"]))
        self.assertTrue(os.path.exists(reports["nepali_path"]))
        self.assertIn("SITREP", reports["english_report"])
        self.assertIn("प्रतिवेदन", reports["nepali_report"])

    def test_06_qa_agent(self):
        """Test grounded Q&A agent for English and Nepali."""
        agent = RescueQAAgent()
        ans1 = agent.answer_query("Which settlements are cut off?")
        self.assertIn("cut off", ans1["answer_en"].lower())
        self.assertEqual(ans1["confidence"], 1.0)
        
        ans2 = agent.answer_query("Is Timure cut off?")
        self.assertIn("timure", ans2["answer_en"].lower())


if __name__ == "__main__":
    unittest.main()
