import unittest
from unittest.mock import patch
import os
import platform

from linodecli.baked.colors import colorize_string, DO_COLORS, CLEAR_COLOR, COLOR_CODE_MAP


class ColorizeStringTestCase:
    def test_colorize_string_supported_platform(self):
        with patch('platform.system', return_value='Linux'):
            result = colorize_string("Hello", "red")
            expected = "\x1b[31mHello\x1b[0m"
            self.assertEqual(result, expected)

    def test_colorize_string_unsupported_platform(self):
        with patch('platform.system', return_value='Windows'):
            result = colorize_string("Hello", "red")
            expected = "Hello"
            self.assertEqual(result, expected)

    def test_DO_COLORS_default_value(self):
        self.assertTrue(DO_COLORS)

    def test_CLEAR_COLOR_value(self):
        self.assertEqual(CLEAR_COLOR, "\x1b[0m")

    def test_COLOR_CODE_MAP_contains_expected_colors(self):
        expected_colors = ["red", "green", "yellow", "black", "white"]
        for color in expected_colors:
            self.assertIn(color, COLOR_CODE_MAP)

    def test_COLOR_CODE_MAP_values_are_ansi_escape_codes(self):
        for color_code in COLOR_CODE_MAP.values():
            self.assertTrue(color_code.startswith("\x1b["))


