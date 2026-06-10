import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.db_models.ai_config import PromptTemplate
from app.db_models.user import User
from app.schemas.prediction_schema import RESEARCH_DISCLAIMER
from app.services import ai_analysis_service, ai_config_service


class FakeLLMResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": "真实 AI 响应"}}]}


class FakeAsyncClient:
    last_request: dict | None = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args) -> None:
        return None

    async def post(self, url: str, headers: dict, json: dict) -> FakeLLMResponse:
        FakeAsyncClient.last_request = {"url": url, "headers": headers, "json": json}
        return FakeLLMResponse()


class AIAnalysisLLMTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.user = User(username="llm_user", email="llm@example.com", password_hash="hash")
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)

    def tearDown(self) -> None:
        self.session.close()

    def test_call_llm_requires_active_config(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                ai_analysis_service._call_llm(
                    self.session,
                    self.user,
                    "model_analysis",
                    {"model_name": "demo"},
                )
            )

        self.assertEqual(ctx.exception.status_code, 400)

    def test_call_llm_uses_latest_user_prompt_template(self) -> None:
        ai_config_service.create_ai_config(
            self.session,
            self.user,
            {
                "name": "OpenAI compatible",
                "provider": "openai",
                "api_base": "https://example.com/v1",
                "api_key": "sk-test",
                "model_name": "demo-model",
                "is_active": True,
            },
        )
        self.session.add(
            PromptTemplate(
                user_id=self.user.id,
                name="自定义模型分析",
                template_type="model_analysis",
                system_prompt="系统提示 {model_name}",
                user_prompt="模型 {model_name} 指标 {metrics}",
            )
        )
        self.session.commit()

        with patch("app.services.ai_analysis_service.httpx.AsyncClient", FakeAsyncClient):
            text = asyncio.run(
                ai_analysis_service._call_llm(
                    self.session,
                    self.user,
                    "model_analysis",
                    {"model_name": "OPNs-SVM", "metrics": "{\"M\": {\"f1\": 0.9}}"},
                )
            )

        self.assertIn("真实 AI 响应", text)
        self.assertIn(RESEARCH_DISCLAIMER, text)
        request_body = FakeAsyncClient.last_request["json"]
        self.assertEqual(request_body["model"], "demo-model")
        self.assertEqual(request_body["messages"][0]["content"], "系统提示 OPNs-SVM")
        self.assertIn("模型 OPNs-SVM 指标", request_body["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
