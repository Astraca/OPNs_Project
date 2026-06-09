import tempfile
import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.db_models.dataset import Dataset
from app.db_models.user import User
from app.services import dataset_service


class DatasetChartServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.user = User(
            username="chart_user",
            email="chart@example.com",
            password_hash="hash",
        )
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)

        frame = pd.DataFrame(
            {
                "age": [20, 30, None, 50],
                "creatinine": [1.0, 1.2, 1.4, 1.6],
                "M": ["M0", "M1", "M1", "M0"],
                "E": ["E0", "E0", "E1", "E0"],
            }
        )
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.temp_file.close()
        frame.to_csv(self.temp_file.name, index=False)

        self.dataset = Dataset(
            user_id=self.user.id,
            name="chart dataset",
            task_type="multi_output_classification",
            file_path=self.temp_file.name,
            file_type="csv",
            sample_count=4,
            feature_count=4,
            target_columns=["M", "E"],
        )
        self.session.add(self.dataset)
        self.session.commit()
        self.session.refresh(self.dataset)
        self.session.add_all(dataset_service.build_column_summaries(self.dataset.id, frame, ["M", "E"]))
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_missing_values_chart_counts_missing_values(self) -> None:
        result = dataset_service.get_missing_values_chart(self.session, self.user, self.dataset.id)
        missing_by_column = {item["column_name"]: item["missing_count"] for item in result["items"]}

        self.assertEqual(result["total_rows"], 4)
        self.assertEqual(missing_by_column["age"], 1)

    def test_label_distribution_chart_returns_igan_targets(self) -> None:
        result = dataset_service.get_label_distribution_chart(self.session, self.user, self.dataset.id)

        self.assertEqual(result["distributions"]["M"], {"M0": 2, "M1": 2})
        self.assertEqual(result["distributions"]["E"], {"E0": 3, "E1": 1})

    def test_correlation_matrix_chart_returns_numeric_columns(self) -> None:
        result = dataset_service.get_correlation_matrix_chart(self.session, self.user, self.dataset.id)

        self.assertEqual(result["columns"], ["age", "creatinine"])
        self.assertEqual(len(result["matrix"]), 2)
        self.assertEqual(result["matrix"][0][0], 1.0)


if __name__ == "__main__":
    unittest.main()
