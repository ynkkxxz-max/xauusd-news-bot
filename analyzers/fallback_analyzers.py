import json
import logging
import os
import requests

from analyzers.gemini_analyzer import (
    _SYSTEM_RULES, actual_prompt, breaking_prompt, normalize_analysis, summary_prompt, smc_setup_prompt,
    signal_validation_prompt,
)
from analyzers.macro_analyzer import MacroAnalyzer

logger = logging.getLogger(__name__)

# OpenAI-compatible chat-completions endpoints. Any provider exposing this
# API can be enabled by setting <NAME>_API_KEY (and optionally <NAME>_MODEL).
OPENAI_COMPAT_PROVIDERS = {
    "deepseek": (os.getenv("DEEPSEEK_BASE_URL", "https://api-cdn.thehive.ai/api/v3"), os.getenv("DEEPSEEK_MODEL", "deepseek-ai/deepseek-v4.1-flash")),
    "openrouter": ("https://openrouter.ai/api/v1", "deepseek/deepseek-chat"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "qwen": ("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "grok": ("https://api.x.ai/v1", "grok-4-fast"),
    "kimi": ("https://api.moonshot.ai/v1", "moonshot-v1-8k"),
    "glm": ("https://api.z.ai/api/paas/v4", "glm-4.5-air"),
}


class OpenAICompatAnalyzer:
    """Talks to any OpenAI-compatible chat-completions API."""

    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = (api_key or "").strip()
        self.model = model
        self.cooldown_until = 0.0

    def is_available(self) -> bool:
        import time
        return bool(self.api_key) and time.time() > self.cooldown_until

    def _chat(self, prompt: str, json_mode: bool) -> str:
        import time
        payload = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": _SYSTEM_RULES},
                {"role": "user", "content": prompt},
            ],
        }
        if json_mode and not ("thehive.ai" in self.base_url):
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        is_hive = "thehive.ai" in self.base_url
        if is_hive:
            headers["Accept"] = "text/event-stream"
            payload["stream"] = True
            payload["reasoning_effort"] = "none"

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=is_hive,
                timeout=30.0,
            )
            if resp.status_code in (400, 401, 402, 403, 404, 429):
                self.cooldown_until = time.time() + 600.0  # 10m cooldown
            resp.raise_for_status()

            if is_hive:
                full_text = ""
                for line in resp.iter_lines():
                    if line:
                        s = line.decode("utf-8")
                        if s.startswith("data: ") and s[6:].strip() != "[DONE]":
                            try:
                                c = json.loads(s[6:])
                                if c.get("choices"):
                                    full_text += c["choices"][0]["delta"].get("content", "")
                            except Exception:
                                pass
                return full_text or ""

            return resp.json()["choices"][0]["message"]["content"] or ""
        except Exception:
            self.cooldown_until = time.time() + 300.0
            raise

    @staticmethod
    def _clean_json(text: str) -> dict:
        if not text:
            return {}
        clean = text.strip()
        if "```" in clean:
            import re
            m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
            if m:
                clean = m.group(1).strip()
            else:
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean).strip()
        try:
            return json.loads(clean)
        except Exception:
            import re
            m = re.search(r"\{[\s\S]*\}", clean)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {}

    def analyze_breaking_news(self, title: str, description: str = "") -> dict:
        raw = self._clean_json(self._chat(breaking_prompt(title, description), True))
        return normalize_analysis(raw)

    def analyze_actual_vs_forecast(self, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        raw = self._clean_json(self._chat(actual_prompt(event_name, actual, forecast, previous), True))
        return normalize_analysis(raw)

    def summarize_daily_price(self, price_data: dict) -> str:
        return self._chat(summary_prompt(price_data), False).strip() or None

    def generate_smart_smc_setup(self, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        try:
            return self._clean_json(self._chat(smc_setup_prompt(current_price, key_levels, macro_data, order_book), True))
        except Exception as e:
            logger.warning(f"[{self.name}] generate_smart_smc_setup failed: {e}")
            return None

    def analyze_and_validate_sniper_signal(self, raw_signal: dict, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        try:
            return self._clean_json(self._chat(signal_validation_prompt(raw_signal, current_price, key_levels, macro_data, order_book), True))
        except Exception as e:
            logger.warning(f"[{self.name}] analyze_and_validate_sniper_signal failed: {e}")
            return None


class ClaudeAnalyzer:
    """Talks to the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str):
        self.name = "claude"
        self.api_key = (api_key or "").strip()
        self.model = model
        self.cooldown_until = 0.0

    def is_available(self) -> bool:
        import time
        return bool(self.api_key) and time.time() > self.cooldown_until

    def _chat(self, prompt: str) -> str:
        import time
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        ws_id = os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip()
        if ws_id:
            headers["anthropic-workspace-id"] = ws_id
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": _SYSTEM_RULES,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=4.0,
            )
            if resp.status_code in (400, 401, 402, 403, 404, 429):
                self.cooldown_until = time.time() + 600.0
            resp.raise_for_status()
            return "".join(b.get("text", "") for b in resp.json().get("content", []))
        except Exception:
            self.cooldown_until = time.time() + 300.0
            raise

    def analyze_breaking_news(self, title: str, description: str = "") -> dict:
        return normalize_analysis(json.loads(self._chat(breaking_prompt(title, description))))

    def analyze_actual_vs_forecast(self, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        return normalize_analysis(json.loads(self._chat(actual_prompt(event_name, actual, forecast, previous))))

    def summarize_daily_price(self, price_data: dict) -> str:
        return self._chat(summary_prompt(price_data)).strip() or None

    def generate_smart_smc_setup(self, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        try:
            prompt = smc_setup_prompt(current_price, key_levels, macro_data, order_book) + "\n\nOutput strictly valid JSON with no markdown wrapping."
            content = self._chat(prompt).strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except Exception as e:
            logger.warning(f"[claude] generate_smart_smc_setup failed: {e}")
            return None

    def analyze_and_validate_sniper_signal(self, raw_signal: dict, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        try:
            prompt = signal_validation_prompt(raw_signal, current_price, key_levels, macro_data, order_book) + "\n\nOutput strictly valid JSON with no markdown wrapping."
            content = self._chat(prompt).strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except Exception as e:
            logger.warning(f"[claude] analyze_and_validate_sniper_signal failed: {e}")
            return None


class AnalyzerChain:
    """Tries each configured analyzer in order; rules-based MacroAnalyzer last."""

    def __init__(self, analyzers: list):
        self.analyzers = analyzers

    def is_available(self) -> bool:
        return any(a.is_available() for a in self.analyzers)

    def _first_result(self, method: str, *args):
        for a in self.analyzers:
            if not a.is_available():
                continue
            if not hasattr(a, method):
                continue
            try:
                fn = getattr(a, method)
                res = fn(*args)
                if res:
                    logger.info(f"[AnalyzerChain] {getattr(a, 'name', a.__class__.__name__)} answered {method}")
                    return res
            except Exception as e:
                logger.warning(f"[AnalyzerChain] {getattr(a, 'name', a.__class__.__name__)} failed {method}: {e}")
        return None

    def analyze_breaking_news(self, title: str, description: str = "") -> dict:
        return self._first_result("analyze_breaking_news", title, description) \
            or MacroAnalyzer.analyze_breaking_news(title, description)

    def analyze_actual_vs_forecast(self, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        return self._first_result("analyze_actual_vs_forecast", event_name, actual, forecast, previous) \
            or MacroAnalyzer.analyze_actual_vs_forecast(event_name, actual, forecast, previous)

    def summarize_daily_price(self, price_data: dict) -> str:
        return self._first_result("summarize_daily_price", price_data) or ""

    def generate_smart_smc_setup(self, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        # 1. Hedge Fund-Grade Multi-AI Council Consensus Engine (Gemini + Claude + GPT/DeepSeek)
        try:
            from analyzers.consensus_engine import MultiAIConsensusEngine
            consensus_engine = MultiAIConsensusEngine(self.analyzers)
            consensus_res = consensus_engine.generate_consensus_setup(
                current_price=current_price,
                key_levels=key_levels,
                macro_data=macro_data,
                order_book=order_book,
                timeout=25.0
            )
            if consensus_res:
                return consensus_res
        except Exception as e:
            logger.warning(f"[AnalyzerChain] MultiAIConsensusEngine failed: {e}")

        # 2. Sequential AI Fallback if consensus engine encounters issue
        return self._first_result("generate_smart_smc_setup", current_price, key_levels, macro_data, order_book) \
            or MacroAnalyzer.generate_smart_smc_setup(current_price, key_levels, macro_data, order_book)

    def analyze_chart_image(self, image_bytes: bytes, current_price: float, key_levels: dict = None) -> dict:
        return self._first_result("analyze_chart_image", image_bytes, current_price, key_levels)

    def analyze_and_validate_sniper_signal(self, raw_signal: dict, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        return self._first_result("analyze_and_validate_sniper_signal", raw_signal, current_price, key_levels, macro_data, order_book) \
            or MacroAnalyzer.analyze_and_validate_sniper_signal(raw_signal, current_price, key_levels, macro_data, order_book)


def build_fallback_analyzers() -> list:
    """Instantiates fallback analyzers for every provider with a configured key.

    Order follows AI_FALLBACKS (comma-separated names), e.g. "groq,deepseek".
    """
    chain = []
    wanted = [n.strip().lower() for n in os.getenv("AI_FALLBACKS", "").split(",") if n.strip()]
    for name in wanted:
        if name == "claude":
            chain.append(ClaudeAnalyzer(
                os.getenv("ANTHROPIC_API_KEY", ""),
                os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            ))
            continue
        if name not in OPENAI_COMPAT_PROVIDERS:
            logger.warning(f"[AnalyzerChain] unknown fallback provider '{name}' ignored")
            continue
        base_url, default_model = OPENAI_COMPAT_PROVIDERS[name]
        chain.append(OpenAICompatAnalyzer(
            name,
            base_url,
            os.getenv(f"{name.upper()}_API_KEY", ""),
            os.getenv(f"{name.upper()}_MODEL", default_model),
        ))
    return [a for a in chain if a.is_available()]
