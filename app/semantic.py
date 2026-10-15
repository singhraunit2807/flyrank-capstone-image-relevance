from __future__ import annotations

import math
import os
from typing import Any

import httpx

from .core import Image, Suggestion, rank_images


class EmbeddingProviderError(RuntimeError):
    pass


def _embed_batch(texts: list[str]) -> list[list[float]]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise EmbeddingProviderError("GEMINI_API_KEY is not configured.")
    model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
    payload: dict[str, Any] = {
        "requests": [
            {"model": f"models/{model}", "content": {"parts": [{"text": text}]},
             "taskType": "RETRIEVAL_DOCUMENT" if index else "RETRIEVAL_QUERY",
             "outputDimensionality": 768}
            for index, text in enumerate(texts)
        ]
    }
    try:
        response = httpx.post(url, headers={"x-goog-api-key": key}, json=payload, timeout=35)
        response.raise_for_status()
        data = response.json()
        embeddings = [item["values"] for item in data["embeddings"]]
        if len(embeddings) != len(texts) or any(not vector for vector in embeddings):
            raise EmbeddingProviderError("Embedding provider returned an incomplete response.")
        return embeddings
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            raise EmbeddingProviderError(
                f"Gemini embedding API returned HTTP {status}. Check API key permissions, embedding model access, quota, and billing."
            ) from exc
        if isinstance(exc, httpx.TimeoutException):
            raise EmbeddingProviderError("Gemini embedding API timed out. Retry later and check provider status.") from exc
        raise EmbeddingProviderError("Gemini embedding API returned an invalid or incomplete response. Check model output and provider status.") from exc


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def rank_with_semantic_embeddings(
    post_text: str, images: list[Image], threshold: float = 0.20
) -> list[Suggestion]:
    """Rank metadata with Gemini semantic text embeddings, retaining hard safety guards."""
    texts = [post_text] + [
        " ".join((image.subject, image.category, *image.attributes, image.caption))
        for image in images
    ]
    vectors = _embed_batch(texts)
    subject_ranked = rank_images(post_text, images, threshold=0.0)
    guards = {item.image_id: item for item in subject_ranked}
    results: list[Suggestion] = []
    for image, vector in zip(images, vectors[1:]):
        guard = guards[image.id]
        score = max(0.0, min(1.0, _cosine(vectors[0], vector)))
        if guard.reason.startswith("Subject mismatch"):
            result = Suggestion(image.id, score, "rejected", guard.reason)
        elif image.confidence < 0.70:
            result = Suggestion(image.id, score, "rejected",
                                f"Low image confidence: {image.confidence:.2f} is below 0.70")
        elif score < threshold:
            result = Suggestion(image.id, score, "rejected",
                                f"Semantic similarity {score:.3f} is below threshold {threshold:.3f}")
        else:
            result = Suggestion(image.id, score, "accepted",
                                "Passed Gemini semantic similarity, confidence, and subject checks.")
        results.append(result)
    return sorted(results, key=lambda item: (item.decision == "accepted", item.score), reverse=True)
