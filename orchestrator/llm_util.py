import os

from dotenv import load_dotenv

from orchestrator.policy_composer import PolicyComposer
from schemas.prompt_inputs import PromptIntent

# This tells Python to look for your local .env file
load_dotenv()


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.endpoint = os.getenv("LLM_ENDPOINT")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        fallback = os.getenv("LLM_FALLBACK_MODELS", "")
        self.fallback_models = [m.strip() for m in fallback.split(",") if m.strip()]
        self.timeout_s = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    @staticmethod
    def _is_unsupported_model_error(response) -> bool:
        if getattr(response, "status_code", None) != 400:
            return False
        try:
            payload = response.json()
            message = str(payload.get("error", {}).get("message", "")).lower()
        except Exception:
            message = str(getattr(response, "text", "")).lower()
        return "model is not supported" in message or "requested model is not supported" in message

    @staticmethod
    def _legacy_to_intent(prompt: str, system_prompt: str | None) -> PromptIntent:
        return PromptIntent(
            user_input=prompt,
            workflow_constraints=[system_prompt] if system_prompt else [],
        )

    def call_llm(
        self,
        prompt: str | None = None,
        system_prompt: str = "You are a helpful coding assistant.",
        prompt_intent: PromptIntent | None = None,
    ):
        if not self.api_key or not self.endpoint:
            raise ValueError("API Key or Endpoint missing from your local .env file!")

        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        errors = []

        intent = prompt_intent or self._legacy_to_intent(prompt or "", system_prompt)
        system_message = PolicyComposer.compose_system_prompt(intent)
        user_message = PolicyComposer.compose_user_payload(intent)

        payload = {
            "model": "codestral-latest",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        }

        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
