"""
Integration tests for video-transcript-mcp.

These tests verify end-to-end workflows combining multiple functions.
Some tests are marked as slow or require network access.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import (
    fetch_youtube_transcript,
    clean_transcript,
    extract_concepts,
    extract_methodologies,
    analyze_speakers,
    store_video_knowledge,
    extract_video_id
)


@pytest.mark.asyncio
class TestTranscriptProcessingWorkflow:
    """Tests for complete transcript processing workflow."""

    async def test_clean_then_extract_concepts(self, sample_transcript):
        """Test cleaning a transcript and then extracting concepts."""
        # Step 1: Clean the transcript
        clean_result = await clean_transcript({
            "transcript": sample_transcript,
            "remove_timestamps": True,
            "deduplicate": True
        })
        clean_data = json.loads(clean_result[0].text)

        assert clean_data["success"] is True
        cleaned_text = clean_data["cleaned_transcript"]

        # Step 2: Extract concepts from cleaned transcript
        concepts_result = await extract_concepts({
            "transcript": cleaned_text,
            "min_frequency": 1
        })
        concepts_data = json.loads(concepts_result[0].text)

        assert concepts_data["success"] is True
        # Should have found some technical concepts

    async def test_clean_then_extract_methodologies(self, sample_transcript_with_methodology):
        """Test cleaning and extracting methodologies."""
        # Step 1: Clean
        clean_result = await clean_transcript({
            "transcript": sample_transcript_with_methodology
        })
        clean_data = json.loads(clean_result[0].text)

        assert clean_data["success"] is True

        # Step 2: Extract methodologies
        methods_result = await extract_methodologies({
            "transcript": clean_data["cleaned_transcript"]
        })
        methods_data = json.loads(methods_result[0].text)

        assert methods_data["success"] is True

    async def test_clean_then_analyze_speakers(self, sample_transcript_with_speakers):
        """Test cleaning and analyzing speakers."""
        # Step 1: Clean (preserving speaker markers)
        clean_result = await clean_transcript({
            "transcript": sample_transcript_with_speakers,
            "remove_timestamps": True,
            "deduplicate": False  # Keep speaker lines
        })
        clean_data = json.loads(clean_result[0].text)

        assert clean_data["success"] is True

        # Step 2: Analyze speakers
        speakers_result = await analyze_speakers({
            "transcript": sample_transcript_with_speakers  # Use original with markers
        })
        speakers_data = json.loads(speakers_result[0].text)

        assert speakers_data["success"] is True

    async def test_full_knowledge_extraction_workflow(
        self, sample_transcript, sample_video_metadata
    ):
        """Test complete knowledge extraction and storage workflow."""
        # Step 1: Clean transcript
        clean_result = await clean_transcript({"transcript": sample_transcript})
        clean_data = json.loads(clean_result[0].text)
        cleaned_text = clean_data["cleaned_transcript"]

        # Step 2: Extract concepts
        concepts_result = await extract_concepts({
            "transcript": cleaned_text,
            "min_frequency": 1
        })
        concepts_data = json.loads(concepts_result[0].text)
        concepts = concepts_data["concepts"]

        # Step 3: Extract methodologies
        methods_result = await extract_methodologies({"transcript": cleaned_text})
        methods_data = json.loads(methods_result[0].text)
        methodologies = methods_data["methodologies"]

        # Step 4: Store knowledge
        storage_result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": concepts,
            "methodologies": methodologies,
            "transcript_summary": "Test summary of video content"
        })
        storage_data = json.loads(storage_result[0].text)

        assert storage_data["success"] is True
        assert storage_data["observations_count"] > 0


@pytest.mark.asyncio
class TestMockedFetchWorkflow:
    """Tests for fetch + process workflows with mocked yt-dlp."""

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_fetch_and_extract_concepts(
        self, mock_dir, mock_subprocess, tmp_path, sample_vtt_content
    ):
        """Test fetching transcript and extracting concepts."""
        # Setup mock VTT file
        vtt_path = tmp_path / "test123.en.vtt"
        vtt_path.write_text(sample_vtt_content)

        mock_transcripts_dir = MagicMock()
        mock_transcripts_dir.glob.return_value = [vtt_path]
        mock_transcripts_dir.__truediv__ = lambda self, x: tmp_path / x
        mock_transcripts_dir.mkdir = MagicMock()

        with patch('server.TRANSCRIPTS_DIR', mock_transcripts_dir):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            # Step 1: Fetch transcript
            fetch_result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123",
                "auto_clean": True
            })
            fetch_data = json.loads(fetch_result[0].text)

            if fetch_data["success"]:
                transcript = fetch_data["transcript"]

                # Step 2: Extract concepts
                concepts_result = await extract_concepts({
                    "transcript": transcript,
                    "min_frequency": 1
                })
                concepts_data = json.loads(concepts_result[0].text)

                assert concepts_data["success"] is True


@pytest.mark.asyncio
class TestErrorRecoveryWorkflows:
    """Tests for error handling in workflows."""

    async def test_empty_transcript_through_workflow(self):
        """Test workflow handles empty transcript gracefully."""
        # Clean empty transcript
        clean_result = await clean_transcript({"transcript": ""})
        clean_data = json.loads(clean_result[0].text)
        assert clean_data["success"] is True

        # Extract concepts from empty
        concepts_result = await extract_concepts({
            "transcript": clean_data["cleaned_transcript"]
        })
        concepts_data = json.loads(concepts_result[0].text)
        assert concepts_data["success"] is True
        assert concepts_data["concepts"] == []

        # Extract methodologies from empty
        methods_result = await extract_methodologies({
            "transcript": clean_data["cleaned_transcript"]
        })
        methods_data = json.loads(methods_result[0].text)
        assert methods_data["success"] is True
        assert methods_data["methodologies"] == []

        # Store empty knowledge
        storage_result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": [],
            "methodologies": []
        })
        storage_data = json.loads(storage_result[0].text)
        assert storage_data["success"] is True

    async def test_workflow_with_minimal_data(self):
        """Test workflow with minimal input data."""
        transcript = "AI"  # Very minimal transcript

        # Should handle without errors
        clean_result = await clean_transcript({"transcript": transcript})
        assert json.loads(clean_result[0].text)["success"] is True

        concepts_result = await extract_concepts({"transcript": transcript})
        assert json.loads(concepts_result[0].text)["success"] is True


class TestUrlExtractionEdgeCases:
    """Edge case tests for URL extraction (synchronous tests)."""

    @pytest.mark.parametrize("url,expected", [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?v=abc123&t=100&list=PLxyz", "abc123"),
        ("http://youtube.com/watch?v=test", "test"),
        ("https://m.youtube.com/watch?v=mobile", "mobile"),
    ])
    def test_valid_url_extraction(self, url, expected):
        """Test extraction from various valid URL formats."""
        result = extract_video_id(url)
        assert result == expected

    @pytest.mark.parametrize("url", [
        "https://vimeo.com/123456",
        "https://twitch.tv/video/123",
        "",
        "not a url",
        "https://youtube.com/",
        "https://youtube.com/watch",
    ])
    def test_invalid_url_extraction(self, url):
        """Test that invalid URLs return None."""
        result = extract_video_id(url)
        assert result is None


@pytest.mark.asyncio
class TestConcurrentOperations:
    """Tests for concurrent/parallel operations."""

    async def test_parallel_concept_extraction(self, sample_transcript):
        """Test extracting concepts with different parameters concurrently."""
        import asyncio

        tasks = [
            extract_concepts({"transcript": sample_transcript, "min_frequency": 1}),
            extract_concepts({"transcript": sample_transcript, "min_frequency": 2}),
            extract_concepts({"transcript": sample_transcript, "min_frequency": 3}),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            data = json.loads(result[0].text)
            assert data["success"] is True

    async def test_parallel_different_operations(
        self, sample_transcript, sample_transcript_with_speakers
    ):
        """Test running different operations concurrently."""
        import asyncio

        tasks = [
            clean_transcript({"transcript": sample_transcript}),
            extract_concepts({"transcript": sample_transcript}),
            analyze_speakers({"transcript": sample_transcript_with_speakers}),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            data = json.loads(result[0].text)
            assert data["success"] is True


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
class TestRealNetworkOperations:
    """Tests that require network access (marked as slow/integration)."""

    @pytest.mark.skip(reason="Requires network access and yt-dlp")
    async def test_real_youtube_fetch(self):
        """Test fetching from a real YouTube video.

        This test is skipped by default as it requires network access.
        To run: pytest -m integration --run-slow
        """
        # Use a short, reliably available video
        result = await fetch_youtube_transcript({
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo"
            "language": "en",
            "auto_clean": True
        })
        data = json.loads(result[0].text)

        # May succeed or fail depending on caption availability
        assert "success" in data
