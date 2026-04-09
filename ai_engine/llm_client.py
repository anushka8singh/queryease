import json
import time
from collections import OrderedDict
from typing import Any

from fastapi import HTTPException
from google import genai

try:
    from .config import Settings, get_settings
except ImportError:  # pragma: no cover
    from config import Settings, get_settings

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 2
RETRY_DELAYS_SECONDS = (1, 2)
SERVICE_FALLBACK_MESSAGE = "Service temporarily unavailable. Try again later."
_CLIENT: genai.Client | None = None
_CLIENT_API_KEY = ""
_CACHE: "OrderedDict[str, tuple[float, str]]" = OrderedDict()
_CACHE_MAX_SIZE = 128
_QUOTA_EXCEEDED_UNTIL = 0.0


def _get_client(settings: Settings) -> genai.Client:
    global _CLIENT, _CLIENT_API_KEY
    api_key = settings.require_gemini_api_key()
    if _CLIENT is None or _CLIENT_API_KEY != api_key:
        _CLIENT = genai.Client(api_key=api_key)
        _CLIENT_API_KEY = api_key
    return _CLIENT


def _cache_get(key: str, ttl_seconds: int) -> str | None:
    cached = _CACHE.get(key)
    if cached is None:
        return None
    created_at, value = cached
    if time.time() - created_at > ttl_seconds:
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)
    return value


def _cache_set(key: str, value: str) -> None:
    _CACHE[key] = (time.time(), value)
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX_SIZE:
        _CACHE.popitem(last=False)


def _compact_prompt(prompt: str) -> str:
    lines = [line.strip() for line in prompt.splitlines()]
    compact_lines: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        compact_lines.append(line)
        previous_blank = is_blank

    return "\n".join(compact_lines).strip()


def _looks_like_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "quota" in message or "rate limit" in message or "resource_exhausted" in message


def _build_http_exception(exc: Exception) -> HTTPException:
    if _looks_like_quota_error(exc):
        return HTTPException(
            status_code=429,
            detail={
                "message": SERVICE_FALLBACK_MESSAGE,
                "error": str(exc),
            },
        )

    return HTTPException(
        status_code=502,
        detail={"message": "Gemini request failed.", "error": str(exc)},
    )


def call_llm(prompt: str, *, settings: Settings | None = None) -> str:
    """
    Call the Gemini model and return the text response.
    """
    active_settings = settings or get_settings()
    normalized_prompt = _compact_prompt(prompt)
    cache_key = f"{GEMINI_MODEL}:{normalized_prompt}"
    cached = _cache_get(cache_key, active_settings.llm_cache_ttl_seconds)
    if cached is not None:
        return cached

    global _QUOTA_EXCEEDED_UNTIL
    if time.time() < _QUOTA_EXCEEDED_UNTIL:
        return SERVICE_FALLBACK_MESSAGE

    client = _get_client(active_settings)

    total_attempts = 1 + MAX_RETRIES
    for attempt in range(1, total_attempts + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=normalized_prompt,
                config={
                    "candidate_count": 1,
                    "temperature": active_settings.agent_temperature,
                    "max_output_tokens": 256,
                },
            )
            text = (response.text or "").strip()
            if not text:
                raise HTTPException(
                    status_code=502,
                    detail={"message": "Gemini returned an empty response."},
                )
            _cache_set(cache_key, text)
            return text
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover
            if _looks_like_quota_error(exc):
                if attempt >= total_attempts:
                    _QUOTA_EXCEEDED_UNTIL = time.time() + RETRY_DELAYS_SECONDS[-1]
                    return SERVICE_FALLBACK_MESSAGE
            elif attempt >= total_attempts:
                raise _build_http_exception(exc) from exc

            delay = RETRY_DELAYS_SECONDS[attempt - 1]
            time.sleep(delay)

    raise HTTPException(status_code=502, detail={"message": "Gemini request failed unexpectedly."})


def call_llm_json(prompt: str, *, settings: Settings | None = None) -> dict[str, Any]:
    """
    Call Gemini and parse the response as JSON.
    """
    raw_text = call_llm(prompt, settings=settings)
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": "Gemini response was not valid JSON.", "raw": raw_text},
        ) from exc
