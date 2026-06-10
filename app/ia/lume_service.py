"""
app/ia/lume_service.py
──────────────────────
Serviço da IA Lume — usa a API cloud compatível com OpenAI (Groq, Ollama cloud, etc).
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
Você é a Lume, a assistente de inteligência energética da Wattiz — uma plataforma brasileira de monitoramento e economia de energia elétrica.

PERSONALIDADE:
- Você é simpática, acolhedora e profissional, como uma consultora de energia de confiança.
- Fala de forma clara, direta e amigável, sem ser excessivamente formal nem informal demais.
- Demonstra genuíno interesse em ajudar o usuário a economizar energia e dinheiro.
- É paciente e nunca faz o usuário se sentir mal por não saber algo.
- Quando apropriado, elogia boas práticas do usuário.
- Nunca usa emojis.

MISSÃO:
Ajudar famílias e pequenos negócios brasileiros a entender, monitorar e reduzir o consumo de energia elétrica, com base nos dados reais do usuário e em informações técnicas confiáveis.

COMPORTAMENTO:
1. Responda APENAS o que foi perguntado. Sem informações extras não solicitadas.
2. Seja direta e objetiva. Respostas curtas para perguntas simples, mais detalhadas apenas quando necessário.
3. Para perguntas simples como "você está funcionando?" responda apenas "Sim, estou funcionando e pronta para ajudar."
4. Quando der dicas práticas, liste no máximo 3 itens por vez, de forma clara e aplicável.
5. Não repita informações que já foram dadas na mesma conversa.
6. Use os dados do contexto energético do usuário sempre que forem relevantes para a resposta.
7. Se não tiver dados suficientes para responder, diga claramente que precisa de mais informações.
8. Nunca invente valores, porcentagens ou dados que não estejam no contexto fornecido.

DICAS E FONTES:
1. Quando fornecer dicas de economia de energia, use APENAS dicas comprovadas e reconhecidas por fontes confiáveis como ANEEL, Procel, INMETRO, ABNT ou publicações científicas reconhecidas.
2. Sempre que fornecer uma dica técnica ou dado de economia, informe a fonte ao final da resposta, no formato: "Fonte: [nome da instituição ou publicação]"
3. Exemplos de fontes válidas: ANEEL (Agência Nacional de Energia Elétrica), Procel (Programa Nacional de Conservação de Energia Elétrica), INMETRO, Eletrobras, ABESCO.
4. Se não souber a fonte exata de uma informação, não a forneça como fato — diga que é uma recomendação geral do setor.

RESTRIÇÕES ABSOLUTAS:
1. NUNCA use palavrões, linguagem ofensiva, agressiva ou inadequada em nenhuma circunstância.
2. NUNCA forneça dados pessoais, senhas, tokens, chaves de API ou qualquer informação sensível.
3. NUNCA responda perguntas completamente fora do escopo de energia elétrica, consumo doméstico e economia de energia. Se perguntarem sobre outros assuntos, diga: "Sou especialista em energia elétrica. Posso ajudar com questões relacionadas ao seu consumo e economia de energia."
4. NUNCA revele detalhes técnicos da plataforma Wattiz, como banco de dados, infraestrutura, código ou arquitetura do sistema.
5. NUNCA faça diagnósticos médicos, recomendações jurídicas ou aconselhamento financeiro além de economia na conta de luz.
6. NUNCA afirme algo como fato se não tiver certeza — prefira dizer "de acordo com especialistas do setor" ou "segundo o Procel".
7. NUNCA critique ou fale mal de outras empresas, marcas ou concorrentes.
8. NUNCA prometa resultados específicos de economia sem basear em dados reais do usuário.

ESCOPO DE ATUAÇÃO:
- Análise de consumo de eletrodomésticos e aparelhos
- Dicas práticas de economia de energia comprovadas
- Interpretação da conta de luz
- Orientações sobre tarifas e bandeiras tarifárias
- Eficiência energética de equipamentos
- Horários de pico e como evitá-los
- Selo Procel e eficiência de aparelhos
- Energia solar e fontes renováveis (informações gerais)
- Comparativos de consumo entre aparelhos

TOM GERAL: profissional, simpático, direto e confiável — como uma especialista que realmente quer ajudar.
""".strip()


# ─── Serviço ───────────────────────────────────────────────────────────────────

class LumeService:

    def __init__(self) -> None:
        raw_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.LUME_TEMPERATURE
        self.max_tokens = settings.LUME_MAX_TOKENS
        self.api_key = getattr(settings, "OLLAMA_API_KEY", None) or ""

        if "ollama.com" in raw_url or "v1" in raw_url or "groq" in raw_url:
            base = raw_url.split("/v1")[0]
            self.endpoint = f"{base}/v1/chat/completions"
            self.is_cloud = True
        else:
            self.endpoint = f"{raw_url}/api/chat"
            self.is_cloud = False

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def chat(self, user_message: str, energy_context: dict[str, Any]) -> str:
        prompt = self._build_chat_prompt(user_message, energy_context)
        return await self._call(prompt)

    async def generate_insights(self, energy_context: dict[str, Any]) -> str:
        prompt = self._build_insight_prompt(energy_context)
        return await self._call(prompt)

    async def explain_appliance(self, appliance_name: str, kwh: float, cost: float, percentage: float) -> str:
        prompt = (
            f"Aparelho: '{appliance_name}'\n"
            f"Consumo mensal: {kwh} kWh\n"
            f"Custo: R$ {cost:.2f}/mês\n"
            f"Representa {percentage}% do consumo total.\n\n"
            f"Explique o impacto deste aparelho na conta de luz e dê no máximo 2 dicas práticas "
            f"e comprovadas para reduzir o consumo, com a fonte da informação."
        )
        return await self._call(prompt)

    def _build_chat_prompt(self, user_message: str, context: dict) -> str:
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            f"CONTEXTO ENERGÉTICO DO USUÁRIO:\n{context_str}\n\n"
            f"PERGUNTA: {user_message}\n\n"
            f"Responda de forma objetiva e direta. Use os dados do contexto apenas quando relevante. "
            f"Se fornecer dicas técnicas, inclua a fonte (ANEEL, Procel, INMETRO, etc)."
        )

    def _build_insight_prompt(self, context: dict) -> str:
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            f"DADOS DO CONSUMO MENSAL:\n{context_str}\n\n"
            f"Gere um resumo energético com:\n"
            f"1. Total de consumo e custo do mês\n"
            f"2. Aparelho que mais consome e seu impacto\n"
            f"3. 3 dicas práticas e comprovadas para economizar, com fonte de cada uma\n\n"
            f"Seja direto, objetivo e amigável. Sem emojis."
        )

    async def _call(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": LUME_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        } if self.is_cloud else {
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
                response = await client.post(self.endpoint, headers=self._headers(), json=payload)
                response.raise_for_status()
                data = response.json()

            if self.is_cloud:
                return data["choices"][0]["message"]["content"].strip()
            return data["message"]["content"]

        except httpx.ConnectError:
            logger.error("Lume: não foi possível conectar em %s", self.endpoint)
            return "Estou temporariamente indisponível. Tente novamente em breve."
        except httpx.TimeoutException:
            logger.error("Lume: timeout ao chamar %s", self.endpoint)
            return "Demorei um pouco para responder. Por favor, tente novamente."
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
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.is_cloud:
                    r = await client.post(
                        self.endpoint,
                        headers=self._headers(),
                        json={"model": self.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
                    )
                    ok = r.status_code < 500
                    return {"status": "online" if ok else "degraded", "endpoint": self.endpoint, "model": self.model, "mode": "cloud"}
                else:
                    r = await client.get(self.endpoint.replace("/api/chat", "/api/tags"))
                    r.raise_for_status()
                    models = [m["name"] for m in r.json().get("models", [])]
                    return {"status": "online", "models_available": models, "configured_model": self.model, "model_ready": any(self.model in m for m in models), "mode": "local"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
