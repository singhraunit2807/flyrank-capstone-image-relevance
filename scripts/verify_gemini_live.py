from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live smoke test for FlyRank Gemini image upload and semantic matching."
    )
    parser.add_argument("--image", required=True, help="Path to a real local JPEG, PNG, WEBP, or GIF image")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running FlyRank API base URL")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        print(f"ERROR: image file not found: {image_path}", file=sys.stderr)
        return 2
    mime_type = mimetypes.guess_type(image_path.name)[0]
    if mime_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        print("ERROR: use a JPEG, PNG, WEBP, or GIF image.", file=sys.stderr)
        return 2
    if not os.getenv("GEMINI_API_KEY", "").strip():
        print("ERROR: GEMINI_API_KEY is missing from this shell's environment.", file=sys.stderr)
        return 2

    base_url = args.base_url.rstrip("/")
    try:
        with httpx.Client(timeout=90) as client:
            health = client.get(f"{base_url}/health")
            health.raise_for_status()
            if health.json().get("vision_provider") != "gemini":
                print("ERROR: the running API does not report Gemini configured.", file=sys.stderr)
                return 2

            with image_path.open("rb") as stream:
                upload = client.post(
                    f"{base_url}/images/upload",
                    files={"file": (image_path.name, stream, mime_type)},
                )
            upload.raise_for_status()
            uploaded = upload.json()
            metadata = uploaded["metadata"]
            post_text = f"{metadata['subject']}. {metadata['caption']}. {' '.join(metadata['attributes'])}"
            post_id = f"live-gemini-{uploaded['id']}"
            match = client.post(
                f"{base_url}/posts/{post_id}/match",
                json={"post_id": post_id, "text": post_text, "threshold": 0.0},
            )
            match.raise_for_status()
            result = match.json()
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        print(
            "ERROR: live Gemini verification failed. Check that the server is running, "
            "GEMINI_API_KEY is configured in the server process, and the key has API access/quota. "
            f"Details: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1

    summary = {
        "status": "live_gemini_calls_succeeded",
        "uploaded_image_id": uploaded["id"],
        "metadata": metadata,
        "ranking_mode": health.json().get("ranking_mode"),
        "match_message": result.get("message"),
        "suggestion": result.get("suggestion"),
        "ranked_candidates": len(result.get("ranked", [])),
    }
    print(json.dumps(summary, indent=2))
    print("PASS: real Gemini vision upload and semantic ranking endpoint completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
