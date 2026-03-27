# Lab 08 — Describe an Image via API

## Problem Statement

You're building a document processing service that needs to handle images. Your task is to implement three functions that use the Claude Vision API to process images programmatically.

## Functions to Implement

### 1. `encode_image_base64(image_path: str) -> str`

Read an image file from disk and return it as a base64-encoded string suitable for sending to the Anthropic API.

- Open the file in binary mode
- Read the raw bytes
- Encode with `base64.b64encode()`
- Decode the result to a UTF-8 string and return it

### 2. `describe_image(image_path: str, question: str = "What is in this image?") -> str`

Send an image to Claude and ask a question about it. Return the text response.

- Use `encode_image_base64` to get the image data
- Detect the correct media type from the file extension:
  - `.jpg` or `.jpeg` → `image/jpeg`
  - `.png` → `image/png`
  - `.gif` → `image/gif`
  - `.webp` → `image/webp`
- Build an Anthropic message with two content blocks:
  1. An `"image"` block with `source.type = "base64"`, `source.media_type`, and `source.data`
  2. A `"text"` block containing the question
- Return `response.content[0].text`

### 3. `extract_text_from_image(image_path: str) -> str`

Extract all visible text from an image (OCR-style behaviour).

- Call `describe_image` with a specific prompt:
  `"Please extract and return all text visible in this image. Return only the text, no commentary."`
- Return the result

## Constraints

- Use model: `claude-3-haiku-20240307`
- Max tokens: 1024
- Use the `get_anthropic_client()` helper from `shared/utils.py`

## Acceptance Criteria

- [ ] `encode_image_base64("test.png")` returns a non-empty string
- [ ] The returned string is valid base64 (can be decoded with `base64.b64decode()`)
- [ ] `describe_image("test.png")` returns a non-empty string
- [ ] `describe_image` sends the image in the correct Anthropic message format
- [ ] `describe_image("test.jpg")` sets `media_type` to `image/jpeg`
- [ ] `describe_image("test.png")` sets `media_type` to `image/png`
- [ ] `extract_text_from_image` calls `describe_image` with an OCR-style prompt
- [ ] All 8 tests in `tests/test_solution.py` pass

## What Makes This Interesting

Base64 encoding is the universal "packaging" format for binary data in APIs. Understanding how to encode, send, and structure image payloads gives you the foundation for any multimodal API integration — not just Anthropic, but OpenAI, Google Gemini, and others follow the same pattern.

## Extension (optional)

Add URL support to `describe_image`: if `image_path` starts with `http://` or `https://`, use `{"type": "url", "url": image_path}` instead of base64 encoding. This avoids the overhead of downloading and re-uploading publicly accessible images.
