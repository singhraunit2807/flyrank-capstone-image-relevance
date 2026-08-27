from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Image:
    id: str
    subject: str
    category: str
    attributes: tuple[str, ...]
    caption: str
    confidence: float


@dataclass(frozen=True)
class Suggestion:
    image_id: str
    score: float
    decision: str
    reason: str


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def embedding(text: str, dimensions: int = 64) -> list[float]:
    """Small deterministic fallback embedding for local development.

    This is deliberately not presented as a trained semantic model. It gives the
    API a reproducible ranking signal until a real embedding provider is wired in.
    """
    vector = [0.0] * dimensions
    for token in tokenize(text):
        idx = hash(token) % dimensions
        vector[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    av, bv = list(a), list(b)
    return sum(x * y for x, y in zip(av, bv))


def rank_images(post_text: str, images: list[Image], threshold: float = 0.20) -> list[Suggestion]:
    post_tokens = tokenize(post_text)
    post_vector = embedding(post_text)
    results: list[Suggestion] = []

    for image in images:
        image_text = " ".join((image.subject, image.category, *image.attributes, image.caption))
        score = cosine(post_vector, embedding(image_text))
        candidate_tokens = tokenize(image_text)

        # Explicit subject guard: a fox post must not accept a wolf merely because
        # both are visually/semantically close.
        expected_subject = next((s for s in ("fox", "wolf", "dog", "bear", "deer") if s in post_tokens), None)
        if expected_subject and expected_subject not in candidate_tokens:
            results.append(Suggestion(image.id, score, "rejected", f"Subject mismatch: expected {expected_subject}, detected {image.subject}"))
            continue

        if image.confidence < 0.70:
            results.append(Suggestion(image.id, score, "rejected", f"Low image confidence: {image.confidence:.2f}"))
            continue

        if score < threshold:
            results.append(Suggestion(image.id, score, "rejected", f"Similarity {score:.3f} is below threshold {threshold:.3f}"))
            continue

        results.append(Suggestion(image.id, score, "accepted", "Candidate passed similarity, confidence, and mismatch checks."))

    return sorted(results, key=lambda item: item.score, reverse=True)
