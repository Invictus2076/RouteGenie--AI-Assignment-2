"""
test_knowledge_base.py
Checks that every destination is complete and that the planner can
build a plan for every origin × destination × hotel style.

Run: python -m unittest test_knowledge_base -v
"""

import re
import shutil
import tempfile
import unittest

import pddl_generator
from knowledge_base import (
    ATTRACTION_CATEGORIES, CITIES, HOTEL_STYLES, ORIGIN_CITIES,
    get_airline, get_flight_cost, get_flight_hours, pddl_ident,
)
from planner import TravelPlanner

PDDL_SYMBOL = re.compile(r"^[a-z][a-z0-9_]*$")


class KnowledgeBaseTests(unittest.TestCase):

    def test_every_destination_is_complete(self):
        for cid, city in CITIES.items():
            with self.subTest(city=cid):
                self.assertEqual(set(city.hotels), set(HOTEL_STYLES))
                for style, hotel in city.hotels.items():
                    self.assertEqual(hotel.style, style)
                    self.assertGreater(hotel.cost_per_night, 0)
                    self.assertIn(hotel.stars, range(1, 6))
                self.assertGreaterEqual(len(city.attractions), 6)
                self.assertTrue(city.lat or city.lon, "missing coordinates")
                self.assertTrue(city.region)

    def test_attraction_categories_match_ui_chips(self):
        for cid, city in CITIES.items():
            for att in city.attractions:
                with self.subTest(city=cid, attraction=att.name):
                    self.assertIn(att.category, ATTRACTION_CATEGORIES)
                    self.assertGreaterEqual(att.entry_cost, 0)
                    self.assertGreater(att.duration_hours, 0)

    def test_pddl_ids_are_valid_and_unique(self):
        for cid, city in CITIES.items():
            ids = [a.pddl_id() for a in city.attractions]
            ids += [h.pddl_id() for h in city.hotels.values()]
            with self.subTest(city=cid):
                self.assertEqual(len(ids), len(set(ids)), "duplicate PDDL id")
                for i in ids + [pddl_ident(city.transport_mode)]:
                    self.assertRegex(i, PDDL_SYMBOL)

    def test_pddl_ident_examples(self):
        self.assertEqual(pddl_ident("Montmartre & Sacré-Cœur"), "montmartre_sacre_coeur")
        self.assertEqual(pddl_ident("Musée d'Orsay"), "musee_dorsay")
        self.assertEqual(pddl_ident("9/11 Memorial"), "n_9_11_memorial")
        self.assertEqual(pddl_ident("Çırağan Palace Kempinski"), "ciragan_palace_kempinski")

    def test_every_route_has_cost_hours_and_airline(self):
        for org in ORIGIN_CITIES:
            for dst in CITIES:
                if org == dst:
                    continue
                with self.subTest(origin=org, destination=dst):
                    cost = get_flight_cost(org, dst)
                    self.assertIsNotNone(cost)
                    self.assertGreater(cost, 0)
                    self.assertGreater(get_flight_hours(org, dst), 0)
                    self.assertTrue(get_airline(org, dst))

    def test_explicit_routes_win_over_estimates(self):
        self.assertEqual(get_flight_cost("london", "paris"), 85)
        self.assertEqual(get_flight_cost("paris", "london"), 85)
        self.assertEqual(get_flight_hours("paris", "rome"), 2.0)

    def test_estimates_are_plausible(self):
        # Short domestic hop vs. long-haul
        self.assertLess(get_flight_cost("delhi", "jaipur"), 120)
        self.assertGreater(get_flight_cost("mumbai", "queenstown"), 800)
        self.assertGreater(get_flight_hours("mumbai", "queenstown"), 14)


class PlannerSweepTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig = pddl_generator.generate_problem.__defaults__
        # Write generated PDDL into a temp folder instead of pddl_output/
        pddl_generator.generate_problem.__defaults__ = (self.tmp,)

    def tearDown(self):
        pddl_generator.generate_problem.__defaults__ = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_plan_for_every_combination(self):
        for org in ORIGIN_CITIES:
            for dst in CITIES:
                if org == dst:
                    continue
                for style in HOTEL_STYLES:
                    with self.subTest(origin=org, destination=dst, style=style):
                        result = TravelPlanner(
                            origin=org, destination=dst, budget=8000,
                            duration=5, hotel_style=style,
                            interests=["culture", "food"], travellers=2,
                            dep_date_str="2026-12-01",
                        ).generate()
                        self.assertEqual(result["summary"]["destination"], dst)
                        self.assertIn("(define (problem", result["pddl_str"])
                        # An unaffordable trip yields no actions, but then
                        # the user must see an over-budget warning.
                        self.assertTrue(result["actions"] or result["summary"]["warnings"])

    def test_generous_budget_reaches_trip_complete(self):
        for dst in CITIES:
            with self.subTest(destination=dst):
                result = TravelPlanner(
                    origin="delhi" if dst != "delhi" else "mumbai",
                    destination=dst, budget=15000, duration=4,
                    hotel_style="budget", interests=["culture"],
                    travellers=1, dep_date_str="2026-12-01",
                ).generate()
                names = [a["name"] for a in result["actions"]]
                self.assertTrue(any(n.startswith("COMPLETE_TRIP") for n in names), names)


if __name__ == "__main__":
    unittest.main()
