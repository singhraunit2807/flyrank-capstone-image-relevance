from __future__ import annotations

import hmac
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from . import database
from .core import Image, Suggestion, rank_images
from .vision import VisionProviderError, analyze_image as vision_analyze
from .semantic import EmbeddingProviderError, rank_with_semantic_embeddings
IMAGES: list[Image] = []
SUGGESTIONS: dict[str, Suggestion] = {}

database.init_db()


def _image_from_record(row: dict[str, Any]) -> Image:
    return Image(
        id=row["id"], subject=row["subject"], category=row["category"],
        attributes=tuple(row["attributes"]), caption=row["caption"], confidence=float(row["confidence"]),
    )


def _has_image_signature(content: bytes, mime_type: str) -> bool:
    """Reject obvious MIME-type spoofing before sending bytes to the vision provider."""
    if mime_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/gif":
        return content.startswith((b"GIF87a", b"GIF89a"))
    if mime_type == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def _persist_image(image: Image, **extra: Any) -> None:
    database.save_image({
        "id": image.id, "subject": image.subject, "category": image.category,
        "attributes": list(image.attributes), "caption": image.caption,
        "confidence": image.confidence, **extra,
    })


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    records = database.load_images()
    IMAGES.clear()
    IMAGES.extend(_image_from_record(row) for row in records)
    if not IMAGES:
        from .seed import SEED_IMAGES
        IMAGES.extend(Image(*row) for row in SEED_IMAGES)
        for image in IMAGES:
            _persist_image(image)
    yield


app = FastAPI(
    title="FlyRank AI Image Relevance API",
    description="Image metadata ingestion, optional Gemini vision analysis, relevance ranking, mismatch guards, SQLite persistence, and review APIs.",
    version="2.0.0",
)

_PUBLIC_PRODUCTION_PATHS = {"/", "/health"}


@app.middleware("http")
async def production_api_auth(request, call_next):
    """Require a bearer token for all non-health API routes in production."""
    if os.getenv("APP_ENV", "development").strip().lower() == "production":
        if request.url.path not in _PUBLIC_PRODUCTION_PATHS:
            configured_token = os.getenv("FLYRANK_API_TOKEN", "").strip()
            if not configured_token:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Production configuration error: FLYRANK_API_TOKEN is required."},
                )
            header = request.headers.get("authorization", "")
            supplied_token = header[7:].strip() if header.lower().startswith("bearer ") else ""
            if not supplied_token or not hmac.compare_digest(supplied_token, configured_token):
                return JSONResponse(
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                    content={"detail": "A valid bearer token is required."},
                )
    return await call_next(request)


class AnalyzeRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    attributes: list[str] = Field(default_factory=list, max_length=30)
    caption: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)


class PostRequest(BaseModel):
    post_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)
    threshold: float = Field(default=0.20, ge=0, le=1)


class ReviewResponse(BaseModel):
    suggestion_id: str
    status: str


def _suggestion_id(post_id: str, image_id: str) -> str:
    return f"{post_id}:{image_id}"


def _as_result(post_id: str, item: Suggestion) -> dict[str, Any]:
    suggestion_id = _suggestion_id(post_id, item.image_id)
    stored = database.get_suggestion(suggestion_id)
    return {
        "suggestion_id": suggestion_id, "image_id": item.image_id,
        "score": round(item.score, 4), "decision": item.decision, "reason": item.reason,
        "review_status": stored["review_status"] if stored else "pending",
    }


def _rank(post_id: str, text: str, threshold: float) -> list[dict[str, Any]]:
    if os.getenv("GEMINI_API_KEY", "").strip():
        try:
            ranked = rank_with_semantic_embeddings(text, IMAGES, threshold)
        except EmbeddingProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    else:
        ranked = rank_images(text, IMAGES, threshold)
    rows = []
    for item in ranked:
        suggestion_id = _suggestion_id(post_id, item.image_id)
        SUGGESTIONS[suggestion_id] = item
        rows.append({
            "suggestion_id": suggestion_id, "post_id": post_id, "image_id": item.image_id,
            "score": round(item.score, 4), "decision": item.decision, "reason": item.reason,
        })
    database.save_suggestions(rows)
    return [_as_result(post_id, item) for item in ranked]


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "FlyRank AI Image Relevance API", "version": "2.0.0", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "catalogue_count": len(IMAGES), "database": "sqlite", "vision_provider": "gemini" if os.getenv("GEMINI_API_KEY") else "not_configured", "ranking_mode": "gemini_semantic_embeddings" if os.getenv("GEMINI_API_KEY") else "offline_lexical_baseline"}


@app.get("/images")
def list_images() -> dict[str, Any]:
    records = database.load_images()
    return {"count": len(records), "images": records}


@app.post("/demo/seed")
def seed_demo() -> dict[str, Any]:
    from .seed import SEED_IMAGES
    database.clear_demo_state()
    IMAGES.clear()
    IMAGES.extend(Image(*row) for row in SEED_IMAGES)
    for image in IMAGES:
        _persist_image(image)
    SUGGESTIONS.clear()
    return {"status": "seeded", "count": len(IMAGES), "message": "Demo catalogue reset successfully."}


@app.post("/images/analyze")
def analyze_image(request: AnalyzeRequest) -> dict[str, Any]:
    image_id = f"img-{uuid.uuid4().hex[:12]}"
    image = Image(
        id=image_id, subject=request.subject.strip(), category=request.category.strip(),
        attributes=tuple(attribute.strip() for attribute in request.attributes if attribute.strip()),
        caption=request.caption.strip(), confidence=request.confidence,
    )
    IMAGES.append(image)
    _persist_image(image)
    return {"id": image.id, "metadata": image.__dict__, "storage": "sqlite"}


@app.post("/images/upload")
async def upload_and_analyze_image(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload an image and extract structured metadata using Gemini vision."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, WEBP, or GIF image.")
    content = await file.read(10 * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Maximum image size is 10 MB.")
    if not _has_image_signature(content, file.content_type):
        raise HTTPException(status_code=415, detail="The uploaded file content does not match its image type.")
    try:
        metadata = vision_analyze(content, file.content_type)
    except VisionProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    upload_dir = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}[file.content_type]
    image_id = f"img-{uuid.uuid4().hex[:12]}"
    image_path = upload_dir / f"{image_id}{suffix}"
    image_path.write_bytes(content)
    image = Image(
        id=image_id, subject=metadata["subject"], category=metadata["category"],
        attributes=tuple(metadata["attributes"]), caption=metadata["caption"],
        confidence=metadata["confidence"],
    )
    IMAGES.append(image)
    _persist_image(image, filename=Path(file.filename or "upload").name,
                   content_type=file.content_type, image_path=str(image_path))
    return {
        "id": image.id, "filename": Path(file.filename or "upload").name,
        "metadata": image.__dict__, "image_path": str(image_path),
        "vision_provider": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    }


@app.post("/posts/{post_id}/match")
def match_post(post_id: str, request: PostRequest) -> dict[str, Any]:
    if request.post_id != post_id:
        raise HTTPException(status_code=400, detail="post_id mismatch")
    ranked = _rank(post_id, request.text, request.threshold)
    accepted = next((item for item in ranked if item["decision"] == "accepted"), None)
    return {"post_id": post_id, "suggestion": accepted, "ranked": ranked,
            "message": "Match found" if accepted else "No confident match"}


@app.get("/posts/{post_id}/images")
def get_ranked_images(
    post_id: str,
    text: str = Query(min_length=1, max_length=2000),
    threshold: float = Query(default=0.20, ge=0, le=1),
) -> dict[str, Any]:
    ranked = _rank(post_id, text, threshold)
    accepted = next((item for item in ranked if item["decision"] == "accepted"), None)
    return {"post_id": post_id, "suggestion": accepted, "ranked": ranked,
            "message": "Match found" if accepted else "No confident match"}


@app.get("/review/{suggestion_id:path}/why")
def why(suggestion_id: str) -> dict[str, Any]:
    item = database.get_suggestion(suggestion_id)
    if not item:
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    return {"suggestion_id": suggestion_id, "decision": item["decision"], "reason": item["reason"],
            "score": round(item["score"], 4), "review_status": item["review_status"]}


@app.post("/review/{suggestion_id:path}/approve", response_model=ReviewResponse)
def approve(suggestion_id: str) -> ReviewResponse:
    if not database.set_review(suggestion_id, "approved"):
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    return ReviewResponse(suggestion_id=suggestion_id, status="approved")


@app.post("/review/{suggestion_id:path}/reject", response_model=ReviewResponse)
def reject(suggestion_id: str) -> ReviewResponse:
    if not database.set_review(suggestion_id, "rejected"):
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    return ReviewResponse(suggestion_id=suggestion_id, status="rejected")
