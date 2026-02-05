"""
AI Handler for Meshtastic AI DM Bot (standalone for meshbotservus).
Manages Google Gemini API interactions and response generation with per-user chat context.
"""

import logging
import time
from typing import Optional, Dict, List
import google.genai as genai

logger = logging.getLogger(__name__)

class AIHandler:
    """Handles AI interactions using Google Gemini with per-user chat sessions."""
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        self.max_retries = 3
        self.retry_delay = 1.0
        self.min_chars = 200
        self.max_chars = 600
        self.ideal_low = 250
        self.ideal_high = 450
        self.generation_config = {
            "temperature": 0.6,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 200,
        }
        self._chats: Dict[str, any] = {}
        self._brevity_preamble = (
            "You are a Meshtastic DM bot with strict brevity rules.\n"
            "- Aim for ~250–450 characters total.\n"
            "- Never under 200 chars; never over 600 chars.\n"
            "- 1–3 short bullet points OR one concise paragraph.\n"
            "- No greetings/preamble/fluff; deliver facts/steps.\n"
            "- If listing steps, use '- <step>'."
        )
        self._setup_model()

    def _setup_model(self):
        try:
            import ssl
            import os

            # Check if SSL verification should be disabled (for corporate proxies/firewalls)
            disable_ssl = os.getenv('DISABLE_SSL_VERIFY', 'false').lower() == 'true'

            if disable_ssl:
                # Disable SSL verification for environments with self-signed certificates
                # WARNING: This is insecure and should only be used for testing
                logger.warning("SSL verification disabled (DISABLE_SSL_VERIFY=true)")

                # Comprehensive SSL bypass for corporate proxies
                os.environ['CURL_CA_BUNDLE'] = ''
                os.environ['REQUESTS_CA_BUNDLE'] = ''
                os.environ['SSL_CERT_FILE'] = ''
                os.environ['SSL_CERT_DIR'] = ''

                # Patch ssl context globally
                ssl._create_default_https_context = ssl._create_unverified_context

                # Disable urllib3 SSL warnings
                try:
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                except:
                    pass

                # Patch httpx if available (used by google-genai)
                try:
                    import httpx
                    # Create a custom transport that doesn't verify SSL
                    original_client_init = httpx.Client.__init__
                    def patched_init(self, *args, **kwargs):
                        kwargs['verify'] = False
                        original_client_init(self, *args, **kwargs)
                    httpx.Client.__init__ = patched_init

                    original_async_client_init = httpx.AsyncClient.__init__
                    def patched_async_init(self, *args, **kwargs):
                        kwargs['verify'] = False
                        original_async_client_init(self, *args, **kwargs)
                    httpx.AsyncClient.__init__ = patched_async_init
                except:
                    pass

            self.client = genai.Client(api_key=self.api_key)

            # List available models and pick the first supported one for free accounts
            available_models = [m for m in self.client.models.list() if hasattr(m, 'name')]
            logger.info("Available Gemini models:")
            for m in available_models:
                logger.info(f"  - {m.name}")

            # Force use of gemini-2.5-flash
            self.model_name = "gemini-2.5-flash"
            ssl_status = "SSL verification disabled" if disable_ssl else "SSL verification enabled"
            logger.info(f"Gemini client initialized successfully; using model '{self.model_name}' ({ssl_status})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def _get_or_create_chat(self, user_id: str):
        # For google.genai, chat history is not supported in the same way. We'll use user_id for context, but send prompt directly.
        return user_id

    @staticmethod
    def _extract_text(response) -> str:
        try:
            if hasattr(response, "text") and response.text:
                return response.text
        except Exception:
            pass
        try:
            cand0 = getattr(response, "candidates", [None])[0]
            if cand0 and hasattr(cand0, "content"):
                parts = getattr(cand0.content, "parts", []) or []
                texts: List[str] = []
                for p in parts:
                    t = getattr(p, "text", None)
                    if not t and isinstance(p, dict):
                        t = p.get("text")
                    if t:
                        texts.append(t)
                if texts:
                    return "\n".join(texts)
        except Exception:
            pass
        return str(response)

    def _clean_whitespace(self, s: str) -> str:
        return " ".join(s.split())

    def _trim_to_max_chars(self, s: str) -> str:
        s = s.strip()
        if len(s) <= self.max_chars:
            return s
        cutoff = self.max_chars
        candidates = []
        for p in [". ", "! ", "? ", "\n", " - "]:
            idx = s.rfind(p, 0, cutoff)
            if idx != -1:
                candidates.append(idx + len(p.strip()))
        if candidates:
            return s[:max(candidates)].strip()
        return s[:self.max_chars].rstrip()

    def _ensure_length_bounds(self, chat, base_prompt: str, first_try_text: str) -> str:
        text = self._clean_whitespace(first_try_text)
        if len(text) < self.min_chars:
            try:
                expand_prompt = (
                    "Please expand the previous answer to roughly "
                    f"{self.ideal_low}–{self.ideal_high} characters. "
                    "Do not add fluff; add only essential specifics."
                )
                resp = chat.send_message(expand_prompt)
                expanded = self._extract_text(resp).strip()
                expanded = self._clean_whitespace(expanded) or text
                text = expanded
            except Exception as e:
                logger.warning(f"Expansion step failed: {e}")
        if len(text) > self.max_chars:
            text = self._trim_to_max_chars(text)
        return text

    def chat_respond(self, user_id: str, prompt: str) -> str:
        if not self.client:
            raise Exception("AI model not initialized")
        concise_prompt = (
            f"{prompt}\n\n"
            "(Reply concisely per rules: ~250–450 chars total; never under 200 or over 600; "
            "use 1–3 short bullets or a compact paragraph; no fluff.)"
        )
        for attempt in range(self.max_retries):
            try:
                resp = self.client.models.generate_content(model=self.model_name, contents=concise_prompt)
                raw = self._extract_text(resp).strip()
                if raw:
                    bounded = self._ensure_length_bounds(user_id, concise_prompt, raw)
                    logger.info(
                        f"AI chat response (attempt {attempt + 1}) len={len(bounded)}"
                    )
                    return bounded
                logger.warning(f"Empty AI chat response (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"AI chat attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error("All AI chat attempts failed")
                    raise Exception(f"AI generation failed after {self.max_retries} attempts: {e}")
        return "I’m having trouble responding right now. Please try again."
