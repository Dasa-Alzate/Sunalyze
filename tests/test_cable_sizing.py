import unittest

from app.services.cable_sizing_service import (
    maximum_length_m,
    select_section,
    size_installation,
)


class CableSizingTest(unittest.TestCase):
    def test_selects_smallest_section_covering_current_and_minimum(self):
        self.assertEqual(select_section(30, 4)['section_mm2'], 4)
        self.assertEqual(select_section(39, 4)['section_mm2'], 6)
        self.assertEqual(select_section(30, 6)['section_mm2'], 6)
        self.assertIsNone(select_section(600, 4))

    def test_maximum_length_uses_half_voltage_drop_budget_and_two_conductors(self):
        self.assertAlmostEqual(maximum_length_m(20, 230, 6), 11.5)

    def test_installation_sizing_uses_panel_isc_and_inverter_output_current(self):
        class Panel:
            isc = 13.8
            vmp = 41.0

        class Inverter:
            I_max_output = 24.0

        sizing = size_installation(Panel(), Inverter(), cell_amount=12, max_cell_amount=15)

        self.assertEqual(sizing['dc']['nominal_current_a'], 13.8)
        self.assertEqual(sizing['dc']['current_a'], 17.25)
        self.assertEqual(sizing['dc']['minimum_section_mm2'], 4)
        self.assertEqual(sizing['dc']['voltage_v'], 492.0)
        self.assertAlmostEqual(sizing['dc']['maximum_length_m'], 19.01, places=2)
        self.assertEqual(sizing['ac']['nominal_current_a'], 24.0)
        self.assertEqual(sizing['ac']['current_a'], 30.0)
        self.assertEqual(sizing['ac']['minimum_section_mm2'], 6)
        self.assertAlmostEqual(sizing['ac']['maximum_length_m'], 7.67, places=2)
        self.assertEqual(sizing['ground_section_mm2'], sizing['ac']['section_mm2'])


if __name__ == '__main__':
    unittest.main()