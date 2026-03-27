"""
Tests for Lab 08 — Describe Images via API
These tests verify function behaviour WITHOUT making real API calls.
"""

import sys
import os
import struct
import zlib
import base64
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add starter (or solution for CI) to path so we test the learner's code
# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))


def create_test_png(path):
    """Create a minimal valid 1x1 white PNG file."""
    # PNG signature
    sig = b'\x89PNG\r\n\x1a\n'
    # IHDR chunk: width=1, height=1, 8-bit depth, RGB colour type
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    # IDAT chunk: minimal image data (filter byte + RGB white pixel)
    raw_data = b'\x00\xFF\xFF\xFF'
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    # IEND chunk
    iend_crc = zlib.crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + iend)


def make_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


@pytest.fixture
def test_png(tmp_path):
    """Fixture: a minimal valid PNG file at a temp path."""
    png_path = tmp_path / "test.png"
    create_test_png(str(png_path))
    return str(png_path)


@pytest.fixture
def test_jpg(tmp_path):
    """Fixture: a tiny JPEG-named PNG file (sufficient for media type detection tests)."""
    jpg_path = tmp_path / "test.jpg"
    create_test_png(str(jpg_path))
    return str(jpg_path)


class TestEncodeImageBase64:
    def test_returns_nonempty_string(self, test_png):
        """encode_image_base64 must return a non-empty string."""
        from solution import encode_image_base64

        result = encode_image_base64(test_png)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_valid_base64(self, test_png):
        """encode_image_base64 must return valid base64 that decodes without error."""
        from solution import encode_image_base64

        result = encode_image_base64(test_png)
        # Should not raise
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_round_trips_file_contents(self, test_png):
        """Decoded base64 must match original file bytes."""
        from solution import encode_image_base64

        original_bytes = Path(test_png).read_bytes()
        result = encode_image_base64(test_png)
        decoded = base64.b64decode(result)
        assert decoded == original_bytes


class TestDescribeImage:
    def test_returns_string(self, test_png):
        """describe_image must return a string."""
        from solution import describe_image

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("A white square.")

            result = describe_image(test_png)
            assert isinstance(result, str)
            assert result == "A white square."

    def test_sends_image_in_correct_format(self, test_png):
        """describe_image must send the image as a base64 content block."""
        from solution import describe_image

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            describe_image(test_png)

            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs.get('messages') or call_args.args[0] if call_args.args else None
            if messages is None:
                # try positional
                messages = call_args[1].get('messages')

            assert messages is not None, "messages argument not found in call"
            content = messages[0]['content']

            # Find the image block
            image_blocks = [b for b in content if b.get('type') == 'image']
            assert len(image_blocks) == 1, "Expected exactly one image content block"

            image_block = image_blocks[0]
            source = image_block.get('source', {})
            assert source.get('type') == 'base64', "source.type must be 'base64'"
            assert 'media_type' in source, "source must include media_type"
            assert 'data' in source, "source must include data"

    def test_media_type_png(self, test_png):
        """describe_image must set media_type to image/png for .png files."""
        from solution import describe_image

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            describe_image(test_png)

            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs.get('messages')
            content = messages[0]['content']
            image_block = next(b for b in content if b.get('type') == 'image')
            assert image_block['source']['media_type'] == 'image/png'

    def test_media_type_jpg(self, test_jpg):
        """describe_image must set media_type to image/jpeg for .jpg files."""
        from solution import describe_image

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            describe_image(test_jpg)

            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs.get('messages')
            content = messages[0]['content']
            image_block = next(b for b in content if b.get('type') == 'image')
            assert image_block['source']['media_type'] == 'image/jpeg'

    def test_passes_question_as_text_block(self, test_png):
        """describe_image must include the question as a text content block."""
        from solution import describe_image

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            describe_image(test_png, question="What colour is the background?")

            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs.get('messages')
            content = messages[0]['content']
            text_blocks = [b for b in content if b.get('type') == 'text']
            assert len(text_blocks) == 1
            assert "What colour is the background?" in text_blocks[0]['text']


class TestExtractTextFromImage:
    def test_calls_describe_image_with_ocr_prompt(self, test_png):
        """extract_text_from_image must call describe_image with an OCR-style prompt."""
        from solution import extract_text_from_image

        with patch('solution.describe_image', return_value="HELLO WORLD") as mock_describe:
            result = extract_text_from_image(test_png)

            assert mock_describe.call_count == 1
            call_args = mock_describe.call_args
            # First positional arg should be the image path
            assert call_args.args[0] == test_png or call_args.kwargs.get('image_path') == test_png
            # The question/prompt should mention text extraction
            question_arg = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get('question', '')
            question_lower = question_arg.lower()
            assert any(word in question_lower for word in ['text', 'extract', 'visible']), (
                f"OCR prompt should mention text extraction, got: '{question_arg}'"
            )

    def test_returns_string(self, test_png):
        """extract_text_from_image must return a string."""
        from solution import extract_text_from_image

        with patch('solution.describe_image', return_value="Some extracted text"):
            result = extract_text_from_image(test_png)
            assert isinstance(result, str)
