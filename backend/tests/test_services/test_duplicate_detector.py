"""Unit tests for duplicate_detector — hash computation only.

detect_duplicates requires a live DB session and is covered by integration
tests. compute_image_hash is pure file I/O + PIL and is tested here.
"""
import pytest
from PIL import Image

from app.services.duplicate_detector import compute_image_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_image(path, color=(128, 64, 32), size=(200, 100), fmt="JPEG"):
    img = Image.new("RGB", size, color=color)
    img.save(path, format=fmt)
    return str(path)


# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------

def test_returns_hex_string_for_jpg(tmp_path):
    path = _save_image(tmp_path / "receipt.jpg")
    result = compute_image_hash(path)
    assert result is not None
    assert isinstance(result, str)
    # pHash with default hash_size=8 produces 64 bits = 16 hex characters
    assert len(result) == 16


def test_returns_hex_string_for_png(tmp_path):
    path = _save_image(tmp_path / "receipt.png", fmt="PNG")
    result = compute_image_hash(path)
    assert result is not None
    assert len(result) == 16


def test_same_image_content_same_hash(tmp_path):
    """Two files with identical pixel data should produce the same hash."""
    path_a = _save_image(tmp_path / "a.jpg")
    path_b = _save_image(tmp_path / "b.jpg")
    assert compute_image_hash(path_a) == compute_image_hash(path_b)


def test_different_images_different_hash(tmp_path):
    """Clearly different images should produce different hashes.

    pHash works on frequency patterns via DCT, so flat solid-color images
    hash identically (no texture = no frequency variation). Use images with
    distinct structure instead.
    """
    import random

    rng = random.Random(42)

    def _noise_image(path, seed):
        r = random.Random(seed)
        img = Image.new("RGB", (200, 200))
        pixels = [(r.randint(0, 255), r.randint(0, 255), r.randint(0, 255))
                  for _ in range(200 * 200)]
        img.putdata(pixels)
        img.save(path, format="PNG")
        return str(path)

    path_a = _noise_image(tmp_path / "a.png", seed=1)
    path_b = _noise_image(tmp_path / "b.png", seed=999)
    assert compute_image_hash(path_a) != compute_image_hash(path_b)


def test_nonexistent_file_returns_none(tmp_path):
    result = compute_image_hash(str(tmp_path / "does_not_exist.jpg"))
    assert result is None


def test_hash_is_stable_across_calls(tmp_path):
    """Same file hashed twice should return the same value."""
    path = _save_image(tmp_path / "receipt.jpg")
    assert compute_image_hash(path) == compute_image_hash(path)
