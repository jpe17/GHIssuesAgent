"""Simple config test."""

import pytest
from api.config import DEVIN_API_KEY, DEVIN_API_BASE


def test_config_basics():
    """Test basic config values."""
    assert DEVIN_API_BASE == "https://api.devin.ai/v1"
    assert DEVIN_API_KEY is not None
    assert len(DEVIN_API_KEY) > 0
    print(f"✅ API Key loaded: {DEVIN_API_KEY[:10]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 