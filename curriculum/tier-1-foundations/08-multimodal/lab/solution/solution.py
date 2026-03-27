"""Lab 08: Multimodal — Describe Images via API (SOLUTION)
----------------------------------------------------------
Reference implementation. Try the starter version first!
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import base64
from pathlib import Path as FilePath
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

# Map of file extensions to MIME types
MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def encode_image_base64(image_path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    image_bytes = FilePath(image_path).read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def describe_image(image_path: str, question: str = "What is in this image?") -> str:
    """Send an image to Claude and ask a question about it."""
    client = get_anthropic_client()

    image_data = encode_image_base64(image_path)
    extension = FilePath(image_path).suffix.lower()
    media_type = MEDIA_TYPES.get(extension, "image/jpeg")

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            }
        ],
    )
    return response.content[0].text


def extract_text_from_image(image_path: str) -> str:
    """Extract all text visible in an image (OCR-like)."""
    return describe_image(
        image_path,
        question="Please extract and return all text visible in this image. Return only the text, no commentary.",
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python solution.py <image_path> [question]")
        print("Example: python solution.py photo.jpg 'What is in this image?'")
        sys.exit(1)

    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "What is in this image?"

    print(f"Image: {image_path}")
    print(f"Question: {question}")
    print("-" * 40)
    result = describe_image(image_path, question)
    print(result)
