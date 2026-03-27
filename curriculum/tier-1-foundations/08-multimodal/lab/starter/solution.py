"""Lab 08: Multimodal — Describe Images via API"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import base64
from pathlib import Path as FilePath
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def encode_image_base64(image_path: str) -> str:
    """
    Read an image file and return its base64-encoded string.

    # TODO: Open image_path in binary mode, read bytes, encode with base64.b64encode(),
    # decode to string with .decode('utf-8'), return the result
    """
    raise NotImplementedError("Implement encode_image_base64")


def describe_image(image_path: str, question: str = "What is in this image?") -> str:
    """
    Send an image to Claude and ask a question about it.

    # TODO:
    # 1. Encode the image using encode_image_base64
    # 2. Detect media type from file extension:
    #    .jpg or .jpeg → "image/jpeg"
    #    .png          → "image/png"
    #    .gif          → "image/gif"
    #    .webp         → "image/webp"
    # 3. Call the Anthropic client with a message that includes two content blocks:
    #    - {"type": "image", "source": {"type": "base64", "media_type": ..., "data": ...}}
    #    - {"type": "text", "text": question}
    # 4. Return response.content[0].text
    """
    raise NotImplementedError("Implement describe_image")


def extract_text_from_image(image_path: str) -> str:
    """
    Extract all text visible in an image (OCR-like).

    # TODO: Call describe_image with a specific OCR prompt:
    # "Please extract and return all text visible in this image. Return only the text, no commentary."
    """
    raise NotImplementedError("Implement extract_text_from_image")


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
