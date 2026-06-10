import unittest

from pydantic import ValidationError

from app.schemas.report_schema import ReportGenerateRequest


class ReportSchemaTestCase(unittest.TestCase):
    def test_generate_request_accepts_title_without_model_id(self) -> None:
        payload = ReportGenerateRequest(title="模型实验报告")

        self.assertEqual(payload.title, "模型实验报告")

    def test_generate_request_rejects_overlong_title(self) -> None:
        with self.assertRaises(ValidationError):
            ReportGenerateRequest(title="x" * 257)


if __name__ == "__main__":
    unittest.main()
