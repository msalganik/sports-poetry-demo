"""Unit tests for poetry_agent.py"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from poetry_agent import (
    generate_haiku,
    generate_sonnet,
    count_words,
    HAIKU_TEMPLATES,
    SONNET_TEMPLATES
)


class TestTemplateMode:
    """Tests for template-based poem generation."""

    @pytest.mark.unit
    def test_generate_haiku_basketball(self):
        """Test haiku generation for basketball."""
        haiku = generate_haiku("basketball", generation_mode="template")

        assert isinstance(haiku, list)
        assert len(haiku) == 3  # Haiku has 3 lines
        assert all(isinstance(line, str) for line in haiku)
        assert all(len(line) > 0 for line in haiku)

    @pytest.mark.unit
    def test_generate_haiku_soccer(self):
        """Test haiku generation for soccer."""
        haiku = generate_haiku("soccer", generation_mode="template")

        assert len(haiku) == 3
        # Soccer haiku should be different from basketball
        basketball_haiku = generate_haiku("basketball", generation_mode="template")
        assert haiku != basketball_haiku

    @pytest.mark.unit
    def test_generate_haiku_unknown_sport(self):
        """Test haiku generation for unknown sport uses default template."""
        haiku = generate_haiku("curling", generation_mode="template")

        assert len(haiku) == 3
        # Should use default template
        assert haiku == HAIKU_TEMPLATES["default"]

    @pytest.mark.unit
    def test_generate_sonnet_basketball(self):
        """Test sonnet generation for basketball."""
        sonnet = generate_sonnet("basketball", generation_mode="template")

        assert isinstance(sonnet, list)
        assert len(sonnet) in [14, 16]  # Sonnets typically 14 lines, some templates have blank lines
        assert all(isinstance(line, str) for line in sonnet)

    @pytest.mark.unit
    def test_generate_sonnet_soccer(self):
        """Test sonnet generation for soccer."""
        sonnet = generate_sonnet("soccer", generation_mode="template")

        assert len(sonnet) in [14, 16]
        # Soccer sonnet should be different from basketball
        basketball_sonnet = generate_sonnet("basketball", generation_mode="template")
        assert sonnet != basketball_sonnet

    @pytest.mark.unit
    def test_generate_sonnet_unknown_sport(self):
        """Test sonnet generation for unknown sport uses default template."""
        sonnet = generate_sonnet("curling", generation_mode="template")

        assert len(sonnet) in [14, 16]
        # Should use default template
        assert sonnet == SONNET_TEMPLATES["default"]

    @pytest.mark.unit
    @pytest.mark.parametrize("sport", ["basketball", "soccer", "tennis", "football", "baseball"])
    def test_all_template_sports_have_poems(self, sport):
        """Test that common sports all have template poems."""
        haiku = generate_haiku(sport, generation_mode="template")
        sonnet = generate_sonnet(sport, generation_mode="template")

        assert len(haiku) == 3
        assert len(sonnet) in [14, 16]


class TestWordCounting:
    """Tests for word counting functionality."""

    @pytest.mark.unit
    def test_count_words_simple(self):
        """Test word counting with simple lines."""
        lines = ["Hello world", "This is a test"]
        assert count_words(lines) == 6

    @pytest.mark.unit
    def test_count_words_haiku(self):
        """Test word counting with actual haiku."""
        haiku = ["Orange sphere in flight,", "Swish through the net, crowd erupts—", "Victory is sweet."]
        count = count_words(haiku)
        # "Orange sphere in flight" = 4, "Swish through the net crowd erupts" = 6, "Victory is sweet" = 3
        assert count == 13

    @pytest.mark.unit
    def test_count_words_empty(self):
        """Test word counting with empty list."""
        assert count_words([]) == 0

    @pytest.mark.unit
    def test_count_words_blank_lines(self):
        """Test word counting ignores blank lines."""
        lines = ["Hello world", "", "Test"]
        assert count_words(lines) == 3


class TestLLMMode:
    """Tests for LLM-based poem generation."""

    @pytest.mark.requires_api_key
    @pytest.mark.slow
    def test_generate_haiku_llm(self, api_key):
        """Test LLM haiku generation."""
        haiku = generate_haiku(
            "cricket",
            generation_mode="llm",
            llm_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            api_token=api_key,
            llm_provider="together"
        )

        assert isinstance(haiku, list)
        assert len(haiku) >= 3  # Should have at least 3 lines
        assert all(isinstance(line, str) for line in haiku)
        assert all(len(line) > 0 for line in haiku)

        # Should NOT be the default template
        default_haiku = HAIKU_TEMPLATES["default"]
        assert haiku != default_haiku

    @pytest.mark.requires_api_key
    @pytest.mark.slow
    def test_generate_sonnet_llm(self, api_key):
        """Test LLM sonnet generation."""
        sonnet = generate_sonnet(
            "cricket",
            generation_mode="llm",
            llm_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            api_token=api_key,
            llm_provider="together"
        )

        assert isinstance(sonnet, list)
        assert len(sonnet) >= 10  # Should have reasonable number of lines
        assert all(isinstance(line, str) for line in sonnet)

        # Should NOT be the default template
        default_sonnet = SONNET_TEMPLATES["default"]
        assert sonnet != default_sonnet

    @pytest.mark.requires_api_key
    @pytest.mark.slow
    def test_llm_generates_unique_content(self, api_key):
        """Test that LLM generates different poems on multiple runs."""
        haiku1 = generate_haiku(
            "rugby",
            generation_mode="llm",
            llm_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            api_token=api_key,
            llm_provider="together"
        )

        haiku2 = generate_haiku(
            "rugby",
            generation_mode="llm",
            llm_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            api_token=api_key,
            llm_provider="together"
        )

        # Different runs should produce different poems
        # (This may occasionally fail if LLM generates same poem, but very unlikely)
        assert haiku1 != haiku2


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.unit
    def test_llm_mode_without_api_key(self):
        """Test that LLM mode without API key raises clear error."""
        with pytest.raises(ValueError, match="LLM mode requires API token"):
            generate_haiku(
                "cricket",
                generation_mode="llm",
                llm_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                api_token=None,
                llm_provider="together"
            )

    @pytest.mark.unit
    def test_llm_mode_without_model(self):
        """Test that LLM mode without model raises clear error."""
        with pytest.raises(ValueError, match="LLM mode requires llm_model"):
            generate_haiku(
                "cricket",
                generation_mode="llm",
                llm_model=None,
                api_token="fake_key",
                llm_provider="together"
            )
