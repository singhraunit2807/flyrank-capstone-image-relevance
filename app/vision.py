from __future__ import annotations

import base64
import json
import os
import re

import httpx


class VisionProviderError(RuntimeError):
    pass


def analyze_image(image_bytes: bytes, mime_type: str) -> dict:
    """Use Gemini vision to return validated structured metadata.

    Requires GEMINI_API_KEY. No API key is hard-coded or persisted.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise VisionProviderError(
            "GEMINI_API_KEY is not configured. Add it to your local .env to enable image AI analysis."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = (
        "Analyze this image for a content-relevance catalogue. Return ONLY JSON with keys: "
        "subject (short concrete primary subject), category (broad category), "
        "attributes (array of short visible attributes), caption (one factual sentence), "
        "confidence (number 0 to 1 reflecting confidence in the description). "
        "Do not infer sensitive personal traits. If uncertain, lower confidence."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    try:
        response = httpx.post(url, params={"key": api_key}, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as exc:
        raise VisionProviderError(f"Vision provider request failed: {exc}") from exc

    subject = str(result.get("subject", "")).strip()
    category = str(result.get("category", "")).strip()
    caption = str(result.get("caption", "")).strip()
    attributes = result.get("attributes", [])
    try:
        confidence = float(result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    if not subject or not category or not caption or not isinstance(attributes, list):
        raise VisionProviderError("Vision provider returned incomplete metadata.")
    if not 0 <= confidence <= 1:
        confidence = max(0.0, min(1.0, confidence))
    return {
        "subject": subject[:100], "category": category[:100],
        "attributes": [str(x)[:100] for x in attributes[:30]],
        "caption": caption[:1000], "confidence": confidence,
    }
