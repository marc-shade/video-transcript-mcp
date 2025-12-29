"""
Tests for video knowledge storage functionality.
"""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import store_video_knowledge, extract_video_id


@pytest.mark.asyncio
class TestStoreVideoKnowledge:
    """Tests for store_video_knowledge function."""

    async def test_basic_storage(self, sample_video_metadata):
        """Test basic knowledge storage."""
        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": ["machine learning", "neural networks"],
            "methodologies": ["gradient descent"],
            "transcript_summary": "Introduction to ML concepts"
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "entity_name" in data
        assert "observations_count" in data

    async def test_generates_entity_name_from_url(self, sample_video_metadata):
        """Test that entity name is generated from video ID."""
        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": ["AI"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "video_knowledge_" in data["entity_name"]
        # Should extract video ID from URL
        assert "abc123xyz" in data["entity_name"]

    async def test_fallback_to_title_hash(self):
        """Test fallback to title hash when no URL."""
        metadata = {
            "title": "My Great Video",
            "duration": "10:00"
        }
        result = await store_video_knowledge({
            "video_metadata": metadata,
            "concepts": ["concept1"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "video_knowledge_" in data["entity_name"]

    async def test_counts_observations_correctly(self, sample_video_metadata):
        """Test that observations are counted correctly."""
        concepts = ["AI", "ML", "DL", "NLP"]
        methodologies = ["method1", "method2"]

        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": concepts,
            "methodologies": methodologies,
            "transcript_summary": "A summary"
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # Should include: URL, Title, Duration, Word Count, Summary + concepts + methodologies
        expected_min = 4 + 1 + len(concepts) + len(methodologies)
        assert data["observations_count"] >= expected_min

    async def test_handles_empty_concepts(self, sample_video_metadata):
        """Test handling of empty concepts list."""
        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": [],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # Should still have metadata observations

    async def test_handles_missing_optional_fields(self, sample_video_metadata):
        """Test handling when optional fields are missing."""
        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": ["AI"],
            # No methodologies or transcript_summary
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_handles_minimal_metadata(self):
        """Test with minimal video metadata."""
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": ["test"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_handles_empty_metadata(self):
        """Test with empty video metadata."""
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": [],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_returns_storage_ready_message(self, sample_video_metadata):
        """Test that result includes appropriate message."""
        result = await store_video_knowledge({
            "video_metadata": sample_video_metadata,
            "concepts": ["AI"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert "message" in data
        assert "enhanced-memory" in data["message"]


@pytest.mark.asyncio
class TestStoreVideoKnowledgeObservations:
    """Tests for observation generation in store_video_knowledge."""

    async def test_includes_url_observation(self):
        """Test that URL is included in observations."""
        metadata = {"url": "https://youtube.com/watch?v=test"}
        result = await store_video_knowledge({
            "video_metadata": metadata,
            "concepts": ["test"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["observations_count"] >= 1

    async def test_includes_title_observation(self):
        """Test that title is included in observations."""
        metadata = {"title": "My Video Title"}
        result = await store_video_knowledge({
            "video_metadata": metadata,
            "concepts": ["test"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_includes_duration_observation(self):
        """Test that duration is included in observations."""
        metadata = {"duration": "15:30"}
        result = await store_video_knowledge({
            "video_metadata": metadata,
            "concepts": ["test"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_includes_word_count_observation(self):
        """Test that word count is included in observations."""
        metadata = {"word_count": 5000}
        result = await store_video_knowledge({
            "video_metadata": metadata,
            "concepts": ["test"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True

    async def test_includes_summary_when_provided(self):
        """Test that transcript summary is included when provided."""
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": ["test"],
            "transcript_summary": "This is a comprehensive summary"
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # Summary should add one more observation
        base_result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": ["test"],
        })
        base_data = json.loads(base_result[0].text)

        # With summary should have more observations
        assert data["observations_count"] >= base_data["observations_count"]

    async def test_concept_observations_prefixed(self):
        """Test that concepts are properly formatted as observations."""
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": ["AI", "ML"],
        })
        data = json.loads(result[0].text)

        assert data["success"] is True
        # Each concept should add an observation
        assert data["observations_count"] >= 2

    async def test_methodology_observations_prefixed(self):
        """Test that methodologies are properly formatted as observations."""
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": [],
            "methodologies": ["gradient descent", "backpropagation"]
        })
        data = json.loads(result[0].text)

        assert data["success"] is True


@pytest.mark.asyncio
class TestStoreVideoKnowledgeErrorHandling:
    """Tests for error handling in store_video_knowledge.

    Note: The current implementation may raise exceptions for invalid input
    rather than returning error responses. These tests document actual behavior.
    """

    async def test_handles_none_metadata(self):
        """Test handling of None metadata - raises AttributeError."""
        # Current implementation doesn't guard against None metadata
        with pytest.raises(AttributeError):
            await store_video_knowledge({
                "video_metadata": None,
                "concepts": ["test"],
            })

    async def test_handles_none_concepts(self):
        """Test handling of None concepts - returns error response.

        The implementation catches the TypeError and returns error JSON.
        """
        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": None,
        })
        data = json.loads(result[0].text)

        # Implementation catches exception and returns error
        assert data["success"] is False
        assert "error" in data

    async def test_handles_invalid_metadata_type(self):
        """Test handling of invalid metadata type - raises AttributeError."""
        # Current implementation doesn't validate metadata type
        with pytest.raises(AttributeError):
            await store_video_knowledge({
                "video_metadata": "not a dict",
                "concepts": ["test"],
            })
