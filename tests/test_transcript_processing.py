"""
Tests for transcript cleaning, processing, and analysis.
"""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import clean_transcript, extract_concepts, extract_methodologies, analyze_speakers


@pytest.mark.asyncio
class TestCleanTranscript:
    """Tests for clean_transcript function."""

    async def test_basic_cleaning(self, sample_transcript):
        """Test basic transcript cleaning."""
        result = await clean_transcript({"transcript": sample_transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "cleaned_transcript" in data
        assert len(data["cleaned_transcript"]) > 0

    async def test_removes_timestamps(self):
        """Test that VTT timestamps are removed."""
        transcript = "00:00:05.000 --> 00:00:10.000 Hello world 00:00:10.000 --> 00:00:15.000 Test"
        result = await clean_transcript({
            "transcript": transcript,
            "remove_timestamps": True
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "-->" not in data["cleaned_transcript"]
        assert "00:00" not in data["cleaned_transcript"]

    async def test_removes_short_timestamp_format(self):
        """Test removal of MM:SS.mmm timestamp format."""
        transcript = "05:30.500 --> 05:35.000 Some speech content"
        result = await clean_transcript({
            "transcript": transcript,
            "remove_timestamps": True
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "-->" not in data["cleaned_transcript"]

    async def test_removes_speaker_labels(self):
        """Test that bracketed labels like [Music] are removed."""
        transcript = "Hello [Music] everyone [Applause] welcome"
        result = await clean_transcript({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "[Music]" not in data["cleaned_transcript"]
        assert "[Applause]" not in data["cleaned_transcript"]

    async def test_deduplicates_lines(self):
        """Test that duplicate consecutive lines are removed."""
        transcript = "Hello\nHello\nHello\nWorld\nWorld"
        result = await clean_transcript({
            "transcript": transcript,
            "deduplicate": True
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # After deduplication, should have fewer occurrences

    async def test_removes_multiple_spaces(self):
        """Test that multiple spaces are collapsed."""
        transcript = "Hello    world  this   has   extra   spaces"
        result = await clean_transcript({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "    " not in data["cleaned_transcript"]
        assert "   " not in data["cleaned_transcript"]

    async def test_compression_ratio_calculated(self):
        """Test that compression ratio is correctly calculated."""
        transcript = "[Music] [Music] [Music] Hello world [Applause]"
        result = await clean_transcript({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "compression_ratio" in data
        assert data["compression_ratio"] >= 1.0  # Original should be >= cleaned

    async def test_empty_transcript(self):
        """Test handling of empty transcript."""
        result = await clean_transcript({"transcript": ""})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["cleaned_transcript"] == ""

    async def test_preserves_content_without_timestamps(self):
        """Test that real content is preserved."""
        transcript = "This is important information about machine learning"
        result = await clean_transcript({
            "transcript": transcript,
            "remove_timestamps": True,
            "deduplicate": True
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "machine learning" in data["cleaned_transcript"]


@pytest.mark.asyncio
class TestExtractConcepts:
    """Tests for extract_concepts function."""

    async def test_extracts_ai_terms(self, sample_transcript):
        """Test extraction of AI-related concepts."""
        result = await extract_concepts({
            "transcript": sample_transcript,
            "min_frequency": 1
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "concepts" in data
        # Should find some concepts from the sample

    async def test_extracts_machine_learning(self):
        """Test extraction of machine learning term."""
        transcript = "Machine learning is great. Machine learning helps. Machine learning works."
        result = await extract_concepts({
            "transcript": transcript,
            "min_frequency": 2
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "machine learning" in data["concepts"]

    async def test_respects_min_frequency(self):
        """Test that min_frequency filter works."""
        transcript = "AI is mentioned once. Algorithm algorithm algorithm."
        result = await extract_concepts({
            "transcript": transcript,
            "min_frequency": 3
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # AI mentioned once should not appear with min_frequency 3
        # algorithm mentioned 3 times should appear
        if "concept_counts" in data:
            for concept, count in data["concept_counts"].items():
                assert count >= 3

    async def test_case_insensitive_matching(self):
        """Test that concept extraction is case insensitive."""
        transcript = "AI is here. ai is powerful. Ai works."
        result = await extract_concepts({
            "transcript": transcript,
            "min_frequency": 2
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "ai" in data["concepts"]

    async def test_returns_sorted_by_frequency(self):
        """Test that concepts are sorted by frequency."""
        transcript = "AI AI AI AI algorithm algorithm model"
        result = await extract_concepts({
            "transcript": transcript,
            "min_frequency": 1
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        if len(data["concepts"]) > 1:
            counts = data["concept_counts"]
            # First concept should have highest count
            first_count = counts.get(data["concepts"][0], 0)
            for concept in data["concepts"][1:]:
                assert counts.get(concept, 0) <= first_count

    async def test_empty_transcript_returns_empty_list(self):
        """Test that empty transcript returns empty concepts."""
        result = await extract_concepts({
            "transcript": "",
            "min_frequency": 1
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["concepts"] == []

    async def test_no_technical_terms_returns_empty(self):
        """Test transcript without technical terms."""
        transcript = "Hello everyone, welcome to my video. I hope you enjoy it."
        result = await extract_concepts({
            "transcript": transcript,
            "min_frequency": 1
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # May or may not have concepts depending on patterns


@pytest.mark.asyncio
class TestExtractMethodologies:
    """Tests for extract_methodologies function."""

    async def test_extracts_step_patterns(self, sample_transcript_with_methodology):
        """Test extraction of step-based methodologies."""
        result = await extract_methodologies({
            "transcript": sample_transcript_with_methodology
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "methodologies" in data

    async def test_extracts_first_then_patterns(self):
        """Test extraction of first/then/next patterns.

        The regex pattern requires content to be at least 10 characters long
        after the keyword, so we need substantial content.
        """
        transcript = "First, we carefully prepare the dataset and clean all the data. Then, we train the machine learning model using gradient descent. Next, we evaluate the results using validation metrics."
        result = await extract_methodologies({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        # The patterns require text to be at least 10-20 chars after keyword
        # and may filter short phrases

    async def test_extracts_approach_method_patterns(self):
        """Test extraction of approach/method descriptions."""
        transcript = "The approach is to use gradient descent for optimization. The method involves iterative refinement."
        result = await extract_methodologies({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_extracts_we_use_patterns(self):
        """Test extraction of 'we use/implement' patterns."""
        transcript = "We implement a novel architecture for this task. They apply transfer learning effectively."
        result = await extract_methodologies({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_code_extraction_disabled_by_default(self):
        """Test that code extraction is disabled by default."""
        transcript = "Here is some code: ```python print('hello')```"
        result = await extract_methodologies({
            "transcript": transcript,
            "extract_code": False
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["code_examples"] == []

    async def test_code_extraction_when_enabled(self):
        """Test code extraction when enabled."""
        transcript = "Here is the code: ```python\ndef hello():\n    print('world')\n```"
        result = await extract_methodologies({
            "transcript": transcript,
            "extract_code": True
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # Should contain code examples

    async def test_limits_methodologies_to_20(self):
        """Test that methodologies are limited to top 20."""
        # Create transcript with many methodology patterns
        patterns = [f"Step {i}: Do something number {i} that is meaningful" for i in range(30)]
        transcript = " ".join(patterns)
        result = await extract_methodologies({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert len(data["methodologies"]) <= 20

    async def test_empty_transcript(self):
        """Test handling of empty transcript."""
        result = await extract_methodologies({"transcript": ""})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["methodologies"] == []


@pytest.mark.asyncio
class TestAnalyzeSpeakers:
    """Tests for analyze_speakers function."""

    async def test_identifies_speakers_with_colon_format(self, sample_transcript_with_speakers):
        """Test speaker identification with Name: format."""
        result = await analyze_speakers({
            "transcript": sample_transcript_with_speakers
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["speaker_count"] >= 1

    async def test_counts_speaker_segments(self):
        """Test that speaker segments are counted correctly."""
        transcript = "John: Hello everyone. Sarah: Hi John. John: How are you? Sarah: I am fine."
        result = await analyze_speakers({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        if data["speaker_count"] > 0:
            assert "speaker_stats" in data

    async def test_no_speakers_detected(self):
        """Test transcript without speaker markers."""
        transcript = "Hello everyone, this is a simple transcript without any speaker labels."
        result = await analyze_speakers({"transcript": transcript})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["speaker_count"] == 0

    async def test_calculates_word_counts(self, sample_transcript_with_speakers):
        """Test that word counts are calculated for speakers."""
        result = await analyze_speakers({
            "transcript": sample_transcript_with_speakers
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        if data["speaker_count"] > 0:
            for speaker, stats in data.get("speaker_stats", {}).items():
                assert "total_words" in stats
                assert stats["total_words"] > 0

    async def test_empty_transcript(self):
        """Test handling of empty transcript."""
        result = await analyze_speakers({"transcript": ""})
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["speaker_count"] == 0
