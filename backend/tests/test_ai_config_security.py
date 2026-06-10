import unittest

from fastapi import HTTPException
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.ai_config import cfg_to_dict
from app.database import Base
from app.db_models.user import User
from app.services import ai_config_service


class AIConfigSecurityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.user = User(username="ai_user", email="ai@example.com", password_hash="hash")
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)

    def tearDown(self) -> None:
        self.session.close()

    def test_ai_config_serializer_never_returns_full_api_key(self) -> None:
        config = ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "DeepSeek",
                "provider": "deepseek",
                "api_base": "https://api.deepseek.com/v1",
                "api_key": "sk-secret-value",
                "model_name": "deepseek-chat",
            },
        )

        serialized = cfg_to_dict(config)

        self.assertNotIn("api_key", serialized)
        self.assertNotIn("api_key_full", serialized)
        self.assertTrue(serialized["has_api_key"])

    def test_update_with_blank_api_key_keeps_existing_secret(self) -> None:
        config = ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "OpenAI",
                "provider": "openai",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-existing-secret",
                "model_name": "gpt-4o",
            },
        )

        updated = ai_config_service.update_ai_config(
            self.session,
            self.user,
            config.id,
            {"name": "OpenAI Updated", "api_key": "  "},
        )

        self.assertEqual(updated.name, "OpenAI Updated")
        self.assertEqual(updated.api_key, "sk-existing-secret")

    def test_create_requires_non_blank_api_key(self) -> None:
        with self.assertRaises(HTTPException):
            ai_config_service.create_ai_config(
                self.session,
                self.user,
                {
                    "name": "Missing Key",
                    "provider": "custom",
                    "api_base": "https://example.com/v1",
                    "api_key": " ",
                    "model_name": "custom-model",
                },
            )

    def test_only_one_ai_config_can_be_default(self) -> None:
        first = ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "First",
                "provider": "openai",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-first",
                "model_name": "gpt-4o",
                "is_active": True,
            },
        )
        second = ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "Second",
                "provider": "deepseek",
                "api_base": "https://api.deepseek.com/v1",
                "api_key": "sk-second",
                "model_name": "deepseek-chat",
            },
        )

        ai_config_service.update_ai_config(self.session, self.user, second.id, {"is_active": True})
        self.session.refresh(first)
        self.session.refresh(second)

        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)

    def test_model_name_must_be_unique(self) -> None:
        ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "First GPT",
                "provider": "openai",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-first",
                "model_name": "gpt-4o",
            },
        )

        with self.assertRaises(HTTPException) as ctx:
            ai_config_service.create_ai_config(
                self.session,
                self.user,
                {
                    "name": "Second GPT",
                    "provider": "openai",
                    "api_base": "https://api.openai.com/v1",
                    "api_key": "sk-second",
                    "model_name": "gpt-4o",
                },
            )

        self.assertEqual(ctx.exception.status_code, 409)

    def test_extract_ai_error_message_returns_message_only(self) -> None:
        response = httpx.Response(
            401,
            json={"error": {"message": "Invalid API key", "type": "authentication_error"}},
            request=httpx.Request("POST", "https://example.com"),
        )

        self.assertEqual(ai_config_service._extract_ai_error_message(response), "Invalid API key")


if __name__ == "__main__":
    unittest.main()
