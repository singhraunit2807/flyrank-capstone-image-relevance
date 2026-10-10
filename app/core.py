from __future__ import annotations

import hashlib
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


_SUBJECTS = ("fox", "wolf", "dog", "bear", "deer", "cat", "bird", "horse", "car", "person")


def tokenize(text: str) -> set[str]:
    """Tokenize text and normalize a few common English plural forms."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    normalized: set[str] = set()
    irregular = {"wolves": "wolf", "foxes": "fox", "geese": "goose", "mice": "mouse"}
    for token in tokens:
        token = irregular.get(token, token)
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("es") and token[:-2].endswith(("s", "x", "z", "ch", "sh")):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
            token = token[:-1]
        normalized.add(token)
    return normalized


def embedding(text: str, dimensions: int = 256) -> list[float]:
    """Stable feature-hashing vector for reproducible, offline development.

    This is a lightweight lexical baseline, not a trained semantic embedding model.
    """
    vector = [0.0] * dimensions
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest, "big") % dimensions
        vector[idx] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    av, bv = list(a), list(b)
    return sum(x * y for x, y in zip(av, bv))


def expected_subject(post_text: str) -> str | None:
    tokens = tokenize(post_text)
    return next((subject for subject in _SUBJECTS if subject in tokens), None)


def rank_images(post_text: str, images: list[Image], threshold: float = 0.20) -> list[Suggestion]:
    """Rank candidate metadata, rejecting subject mismatches and weak confidence."""
    post_vector = embedding(post_text)
    subject = expected_subject(post_text)
    results: list[Suggestion] = []

    for image in images:
        image_text = " ".join((image.subject, image.category, *image.attributes, image.caption))
        score = max(0.0, min(1.0, cosine(post_vector, embedding(image_text))))
        candidate_tokens = tokenize(image_text)

        if subject and subject not in candidate_tokens:
            result = Suggestion(image.id, score, "rejected",
                f"Subject mismatch: expected {subject}, detected {image.subject}")
        elif image.confidence < 0.70:
            result = Suggestion(image.id, score, "rejected",
                f"Low image confidence: {image.confidence:.2f} is below 0.70")
        elif score < threshold:
            result = Suggestion(image.id, score, "rejected",
                f"Similarity {score:.3f} is below threshold {threshold:.3f}")
        else:
            result = Suggestion(image.id, score, "accepted",
                "Candidate passed similarity, confidence, and mismatch checks.")
        results.append(result)

    return sorted(results, key=lambda item: (item.decision == "accepted", item.score), reverse=True)
