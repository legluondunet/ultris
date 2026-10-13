from unittest import TestCase
from unittest.mock import patch

from lutris.buildinfo import get_display_version


class TestBuildVersion(TestCase):
    def test_packaged_commit_is_shortened(self):
        with patch("lutris.buildinfo.Path.read_text", return_value="ABCDEF1234567890\n"):
            self.assertEqual(get_display_version("0.5.23"), "0.5.23 (commit abcdef1)")

    def test_missing_metadata_preserves_version(self):
        with patch("lutris.buildinfo.Path.read_text", side_effect=FileNotFoundError):
            self.assertEqual(get_display_version("0.5.23"), "0.5.23")

    def test_invalid_metadata_preserves_version(self):
        with patch("lutris.buildinfo.Path.read_text", return_value="unknown revision"):
            self.assertEqual(get_display_version("0.5.23"), "0.5.23")
