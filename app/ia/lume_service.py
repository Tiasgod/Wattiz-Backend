"""
app/ia/lume_service.py
──────────────────────
Serviço da IA Lume — usa a API cloud da Ollama (OpenAI-compatible endpoint).

Variáveis de ambiente necessárias:
  OLLAMA_API_KEY   → token Bearer da Ollama cloud
  OLLAMA_BASE_URL  → https://api.ollama.com  (sem trailing slash, sem path)
  OLLAMA_MODEL     → llama3  (ou outro modelo disponível na conta)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── System prompt da Lume ────────────────────────────────────────────────────
LUME_SYSTEM_PROMPT = """
Você é a Lume, assistente de inteligência energética da plataforma Wattiz.
Sua missão é ajudar famílias brasileiras a entenderem e economizarem energia elétrica.

REGRAS ABSOLUTAS:
1. Responda SEMPRE em português brasileiro, com linguagem simples e acolhedora.
2. Use APENAS os dados fornecidos no contexto. Nunca invente valores ou porcentagens.
3. Se os dados não estiverem disponíveis, diga que não tem informações suficientes.
4. Seja prática e objetiva. Dê dicas reais e aplicáveis.
5. Use emojis com moderação para tornar a leitura mais agradável.
6. Não use jargão técnico sem explicar o significado.
7. Mantenha respostas entre 3-8 parágrafos curtos.
8. Se o usuário perguntar algo fora do escopo energético, redirecione gentilmente.

TOM: empático, educativo, encorajador e direto.
""".strip()


# ─── Serviço ───────────────────────────────────────────────────────────────────

class LumeService:
    """
    Gerencia comunicação com a Ollama Cloud (endpoint compatível com OpenAI).
    Suporta tanto o endpoint /v1/chat/completions (cloud) quanto /api/chat (local).
    """

    def __init__(self) -> None:
        raw_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.LUME_TEMPERATURE
        self.max_tokens = settings.LUME_MAX_TOKENS
        self.api_key = getattr(settings, "OLLAMA_API_KEY", None) or ""

        # Detecta se é cloud (OpenAI-compatible) ou local (Ollama nativo)
        if "ollama.com" in raw_url or "v1" in raw_url:
            # Cloud: usa /v1/chat/completions
            base = raw_url.split("/v1")[0]
            self.endpoint = f"{base}/v1/chat/completions"
            self.is_cloud = True
        else:
            # Local: usa /api/chat
            self.endpoint = f"{raw_url}/api/chat"
            self.is_cloud = False

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def chat(
        self,
        user_message: str,
        energy_context: dict[str, Any],
    ) -> str:
        prompt = self._build_chat_prompt(user_message, energy_context)
        return await self._call(prompt)

    async def generate_insights(self, energy_context: dict[str, Any]) -> str:
        prompt = self._build_insight_prompt(energy_context)
        return await self._call(prompt)

    async def explain_appliance(
        self, appliance_name: str, kwh: float, cost: float, percentage: float
    ) -> str:
        prompt = (
            f"Com base nos seguintes dados sobre o aparelho '{appliance_name}':\n"
            f"- Consumo mensal: {kwh} kWh\n"
            f"- Custo estimado: R$ {cost:.2f}/mês\n"
            f"- Representa {percentage}% do consumo total da residência\n\n"
            f"Explique de forma simples o impacto deste aparelho na conta de luz "
            f"e dê dicas práticas para reduzir seu consumo."
        )
        return await self._call(prompt)

    # ─── Builders de prompt ────────────────────────────────────────────────────

    def _build_chat_prompt(self, user_message: str, context: dict) -> str:
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            f"CONTEXTO ENERGÉTICO DO USUÁRIO:\n{context_str}\n\n"
            f"PERGUNTA DO USUÁRIO: {user_message}\n\n"
            f"Responda com base EXCLUSIVAMENTE nos dados do contexto acima."
        )

    def _build_insight_prompt(self, context: dict) -> str:
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            f"DADOS DO CONSUMO MENSAL:\n{context_str}\n\n"
            f"Gere um resumo energético completo e amigável com:\n"
            f"1. Visão geral do consumo\n"
            f"2. Destaques por categoria\n"
            f"3. Aparelho que mais consome e impacto\n"
            f"4. 3 dicas práticas personalizadas para economizar\n"
            f"5. Mensagem motivacional final\n\n"
            f"Use apenas os dados fornecidos. Não invente valores."
        )

    # ─── Chamada à API ─────────────────────────────────────────────────────────

    async def _call(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": LUME_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        if self.is_cloud:
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        else:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # OpenAI-compatible (cloud)
            if self.is_cloud:
                return data["choices"][0]["message"]["content"].strip()
            # Ollama nativo (local)
            return data["message"]["content"]

        except httpx.ConnectError:
            logger.error("Lume: não foi possível conectar em %s", self.endpoint)
            return (
                "Desculpe, estou temporariamente indisponível. "
                "O serviço de IA não está acessível no momento. Tente novamente em breve."
            )
        except httpx.TimeoutException:
            logger.error("Lume: timeout ao chamar %s", self.endpoint)
            return "A IA demorou muito para responder. Por favor, tente novamente."
        except httpx.HTTPStatusError as e:
            logger.error("Lume: HTTP %s — %s", e.response.status_code, e.response.text[:300])
            return "Ocorreu um erro na comunicação com a IA. Nossa equipe foi notificada."
        except (KeyError, IndexError) as e:
            logger.error("Lume: resposta inesperada da API — %s", e)
            return "A resposta da IA veio em formato inesperado. Tente novamente."
        except Exception as e:
            logger.exception("Lume: erro inesperado — %s", e)
            return "Ocorreu um erro interno. Nossa equipe foi notificada."

    async def health_check(self) -> dict[str, Any]:
        """Verifica se o serviço de IA está disponível."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.is_cloud:
                    # Testa com um request mínimo
                    r = await client.post(
                        self.endpoint,
                        headers=self._headers(),
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 5,
                        },
                    )
                    ok = r.status_code < 500
                    return {
                        "status": "online" if ok else "degraded",
                        "endpoint": self.endpoint,
                        "model": self.model,
                        "mode": "cloud",
                    }
                else:
                    r = await client.get(
                        self.endpoint.replace("/api/chat", "/api/tags")
                    )
                    r.raise_for_status()
                    models = [m["name"] for m in r.json().get("models", [])]
                    return {
                        "status": "online",
                        "models_available": models,
                        "configured_model": self.model,
                        "model_ready": any(self.model in m for m in models),
                        "mode": "local",
                    }
        except Exception as e:
            return {"status": "offline", "error": str(e)}
