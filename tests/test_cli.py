import unittest
from unittest.mock import Mock, patch

from main import CrawlReport, build_argument_parser, main


class CommandLineTests(unittest.TestCase):
    def test_accepts_manual_recovery_parameters_and_export_formats(self):
        args = build_argument_parser().parse_args(
            [
                "--course-id", "course-1",
                "--class-id", "class-1",
                "--cpi", "cpi-1",
                "--format", "json", "xlsx",
                "--output-dir", "exports",
            ]
        )

        self.assertEqual("course-1", args.course_id)
        self.assertEqual(["json", "xlsx"], args.formats)
        self.assertEqual("exports", args.output_dir)

    def test_manual_recovery_mode_skips_course_listing(self):
        client = Mock()
        client.crawl_course.return_value = CrawlReport("course-1", "unknown_course", [])

        with patch("main.XXT", return_value=client), patch("main.getpass.getpass", return_value="password"):
            exit_code = main([
                "--username", "user",
                "--course-id", "course-1",
                "--class-id", "class-1",
                "--cpi", "cpi-1",
                "--format", "json",
            ])

        self.assertEqual(0, exit_code)
        client.get_schools.assert_not_called()


if __name__ == "__main__":
    unittest.main()
