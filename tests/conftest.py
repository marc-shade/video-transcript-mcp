"""
Pytest fixtures for video-transcript-mcp tests.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_vtt_content():
    """Sample VTT transcript content."""
    return """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello everyone, welcome to this talk about machine learning.

00:00:05.000 --> 00:00:10.000
Today we'll discuss neural networks and deep learning.

00:00:10.000 --> 00:00:15.000
Let's start with the fundamentals of AI.

00:00:15.000 --> 00:00:20.000
First, we need to understand what an algorithm is.

00:00:20.000 --> 00:00:25.000
[Music]

00:00:25.000 --> 00:00:30.000
The model training process involves several steps.
"""


@pytest.fixture
def sample_transcript():
    """Sample cleaned transcript text."""
    return """Hello everyone, welcome to this talk about machine learning.
Today we'll discuss neural networks and deep learning.
Let's start with the fundamentals of AI.
First, we need to understand what an algorithm is.
The model training process involves several steps.
We use a transformer architecture for this approach.
The attention mechanism helps with performance.
This method is implemented using a framework called PyTorch.
We apply optimization techniques to improve accuracy.
The benchmark results show significant improvement.
Machine learning is transforming many industries.
Neural networks learn patterns from data.
Training requires large datasets for better results."""


@pytest.fixture
def sample_transcript_with_speakers():
    """Sample transcript with speaker markers."""
    return """John: Welcome to our discussion about artificial intelligence.
John: Today we have experts joining us.
Sarah: Thank you for having me. I work on neural networks.
Sarah: The transformer architecture has been revolutionary.
John: Can you explain how attention works?
Sarah: Attention allows models to focus on relevant parts of input.
Mike: I'd like to add that optimization is crucial here.
Mike: We've seen significant performance gains with new techniques."""


@pytest.fixture
def sample_transcript_with_methodology():
    """Sample transcript containing methodology descriptions."""
    return """In this video, we implement a new approach to model training.
First, we prepare the dataset by cleaning the data.
Then, we apply normalization to the inputs.
Next, we build the neural network architecture.
Finally, we train the model using gradient descent.
The approach is to use mini-batch training for efficiency.
Our method involves splitting data into train and test sets.
We use a technique called dropout for regularization.
Step 1: Initialize the model weights.
Step 2: Forward pass through the network.
Phase 1: Data collection and preprocessing.
Phase 2: Model training and validation."""


@pytest.fixture
def sample_video_metadata():
    """Sample video metadata for storage tests."""
    return {
        "url": "https://youtube.com/watch?v=abc123xyz",
        "title": "Introduction to Machine Learning",
        "duration": "15:30",
        "channel": "Tech Talks",
        "word_count": 2500
    }


@pytest.fixture
def mock_yt_dlp_success():
    """Mock successful yt-dlp subprocess execution."""
    async def mock_communicate():
        return (b"", b"")

    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = mock_communicate
    return mock_process


@pytest.fixture
def mock_yt_dlp_failure():
    """Mock failed yt-dlp subprocess execution."""
    async def mock_communicate():
        return (b"", b"ERROR: Video unavailable")

    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = mock_communicate
    return mock_process


@pytest.fixture
def mock_yt_dlp_json_response():
    """Mock yt-dlp JSON response for search."""
    return {
        "entries": [
            {
                "id": "video123",
                "title": "Introduction to AI",
                "channel": "Tech Channel",
                "channel_id": "UC123",
                "duration": 900,
                "view_count": 10000,
                "upload_date": "20240101",
                "description": "A great intro to AI",
                "thumbnails": [{"url": "https://img.youtube.com/vi/video123/0.jpg"}]
            },
            {
                "id": "video456",
                "title": "Deep Learning Tutorial",
                "uploader": "ML Expert",
                "uploader_id": "UC456",
                "duration": 1800,
                "view_count": 50000,
                "upload_date": "20240115",
                "description": "Deep dive into DL"
            }
        ]
    }


@pytest.fixture
def youtube_urls():
    """Sample YouTube URLs for testing URL extraction."""
    return {
        "standard": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "short": "https://youtu.be/dQw4w9WgXcQ",
        "with_params": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120",
        "playlist": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest",
        "invalid": "https://example.com/video/123",
        "malformed": "not-a-url"
    }


@pytest.fixture
def temp_transcripts_dir(tmp_path):
    """Temporary directory for transcript files."""
    transcripts_dir = tmp_path / "video-transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    return transcripts_dir


@pytest.fixture
def mock_vtt_file(temp_transcripts_dir, sample_vtt_content):
    """Create a mock VTT file for testing."""
    def _create_vtt(video_id: str = "test123"):
        vtt_path = temp_transcripts_dir / f"{video_id}.en.vtt"
        vtt_path.write_text(sample_vtt_content)
        return vtt_path
    return _create_vtt
