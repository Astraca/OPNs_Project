import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.db_models.dataset import Dataset
from app.db_models.ml_model import ModelMetric
from app.db_models.user import User
from app.ml.opns_transformer import OPNsTransformer
from app.schemas.model_schema import ModelTrainRequest
from app.services import dataset_service, prediction_service, training_service


class OPNsTrainingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.exit_stack = ExitStack()
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.user = User(username="trainer", email="trainer@example.com", password_hash="hash")
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)

        frame = pd.DataFrame(
            {
                "age": [20, 22, 35, 37, 50, 52, 65, 67, 40, 42],
                "编号": list(range(1, 11)),
                "albumin": [40, 41, 35, 36, 32, 33, 28, 29, 34, 35],
                "creatinine": [0.8, 0.9, 1.0, 1.1, 1.3, 1.4, 1.7, 1.8, 1.2, 1.25],
                "uric_acid": [300, 310, 330, 340, 360, 370, 390, 400, 350, 355],
                "out-M": [0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                "out-E": [0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                "out-S": [0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                "out-T": [0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                "out-C": [0, 0, 1, 1, 0, 0, 1, 1, 0, 1],
            }
        )
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.model_dir = Path(self.exit_stack.enter_context(tempfile.TemporaryDirectory()))
        self.original_model_storage_dir = training_service.MODEL_STORAGE_DIR
        training_service.MODEL_STORAGE_DIR = self.model_dir
        self.temp_file.close()
        frame.to_csv(self.temp_file.name, index=False)
        self.dataset = Dataset(
            user_id=self.user.id,
            name="igan training",
            task_type="multi_output_classification",
            file_path=self.temp_file.name,
            file_type="csv",
            sample_count=len(frame),
            feature_count=len(frame.columns),
            target_columns=["out-M", "out-E", "out-S", "out-T", "out-C"],
        )
        self.session.add(self.dataset)
        self.session.commit()
        self.session.refresh(self.dataset)
        self.session.add_all(dataset_service.build_column_summaries(self.dataset.id, frame, self.dataset.target_columns))
        self.session.commit()

    def tearDown(self) -> None:
        training_service.MODEL_STORAGE_DIR = self.original_model_storage_dir
        self.session.close()
        Path(self.temp_file.name).unlink(missing_ok=True)
        self.exit_stack.close()

    def test_opns_transformer_generates_structural_features(self) -> None:
        transformer = OPNsTransformer(pairing_method="adjacent")
        transformed = transformer.fit_transform(pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": [7, 8]}))

        self.assertEqual(transformer.pairs_, [("a", "b"), ("c", "d")])
        self.assertIn("a__plus__b", transformed.columns)
        self.assertEqual(transformed.shape[1], 10)

    def test_train_opns_svm_persists_model_and_metrics(self) -> None:
        model = training_service.train_classification_model(
            self.session,
            self.user,
            ModelTrainRequest(
                dataset_id=self.dataset.id,
                model_name="test opns svm",
                algorithm="OPNs-SVM",
                target_columns=["out-M", "out-E", "out-S", "out-T", "out-C"],
                pairing_method="adjacent",
                test_size=0.3,
                random_state=7,
            ),
        )
        metrics = self.session.query(ModelMetric).filter(ModelMetric.model_id == model.id).all()

        self.assertTrue(model.opns_enabled)
        self.assertTrue(model.model_file_path)
        self.assertNotIn("编号", model.feature_columns)
        self.assertEqual(len(metrics), 20)

    def test_single_prediction_uses_out_prefixed_targets(self) -> None:
        model = training_service.train_classification_model(
            self.session,
            self.user,
            ModelTrainRequest(
                dataset_id=self.dataset.id,
                model_name="test prediction model",
                algorithm="OPNs-SVM",
                target_columns=["out-M", "out-E", "out-S", "out-T", "out-C"],
                pairing_method="adjacent",
                test_size=0.3,
                random_state=7,
            ),
        )

        result = prediction_service.run_single_prediction(
            self.session,
            self.user,
            model.id,
            {
                "age": 45,
                "albumin": None,
                "creatinine": 1.2,
                "uric_acid": 350,
            },
        )

        self.assertEqual(set(result["result"].keys()), {"M", "E", "S", "T", "C"})
        self.assertIn(result["result"]["M"]["label"], {"M0", "M1"})


if __name__ == "__main__":
    unittest.main()
