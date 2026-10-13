import io
from unittest import TestCase
from unittest.mock import MagicMock, patch

from lutris.util import extract


class TestSevenZipProgress(TestCase):
    def run_extraction(self, output, return_code=0):
        process = MagicMock()
        process.__enter__.return_value = process
        process.stdout = io.BytesIO(output)
        process.wait.return_value = return_code
        progress = []
        with (
            patch.object(extract, "_get_7zip_path", return_value="/usr/bin/7z"),
            patch.object(extract.subprocess, "Popen", return_value=process) as popen,
        ):
            extract._extract_7zip("archive with spaces.zip", "target with spaces", progress_callback=progress.append)
        return progress, popen.call_args.args[0]

    def test_progress_with_carriage_returns_and_backspaces(self):
        output = b"7-Zip header\n  0%\r 25%\b\b\b\b 25%\r 75%\r100%"
        progress, command = self.run_extraction(output)
        self.assertEqual(progress, [0, 25, 75, 99, 100])
        self.assertIn("-bsp1", command)
        self.assertIn("-o" + "target with spaces", command)
        self.assertIn("archive with spaces.zip", command)

    def test_diagnostics_are_not_progress(self):
        progress, _ = self.run_extraction(b"file 42% complete\n101%\r 80%\r")
        self.assertEqual(progress, [0, 80, 100])

    def test_failure_does_not_report_completion(self):
        process = MagicMock()
        process.__enter__.return_value = process
        process.stdout = io.BytesIO(b" 50%\r100%")
        process.wait.return_value = 2
        progress = []
        with (
            patch.object(extract, "_get_7zip_path", return_value="/usr/bin/7z"),
            patch.object(extract.subprocess, "Popen", return_value=process),
            self.assertRaises(extract.ExtractError),
        ):
            extract._extract_7zip("bad.iso", "target", progress_callback=progress.append)
        self.assertNotIn(100, progress)
