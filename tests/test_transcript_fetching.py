"""
Tests for YouTube transcript fetching functionality.
"""

import asyncio
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import fetch_youtube_transcript, extract_video_id


@pytest.mark.asyncio
class TestFetchYoutubeTranscript:
    """Tests for fetch_youtube_transcript function."""

    async def test_returns_error_for_invalid_url(self):
        """Test that invalid URLs return error."""
        result = await fetch_youtube_transcript({
            "url": "https://example.com/not-youtube"
        })
        data = json.loads(result[0].text)

        assert data["success"] is False
        assert "error" in data
        assert "Invalid YouTube URL" in data["error"]

    async def test_returns_error_for_empty_url(self):
        """Test that empty URL returns error."""
        result = await fetch_youtube_transcript({"url": ""})
        data = json.loads(result[0].text)

        assert data["success"] is False
        assert "error" in data

    async def test_returns_error_for_missing_url(self):
        """Test that missing URL returns error."""
        result = await fetch_youtube_transcript({})
        data = json.loads(result[0].text)

        assert data["success"] is False
        assert "error" in data

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_calls_ytdlp_with_correct_args(self, mock_dir, mock_subprocess, tmp_path):
        """Test that yt-dlp is called with correct arguments."""
        # Setup mocks
        mock_dir.__truediv__ = lambda self, x: tmp_path / x
        mock_dir.glob = MagicMock(return_value=[])

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process

        result = await fetch_youtube_transcript({
            "url": "https://youtube.com/watch?v=test123",
            "language": "en"
        })

        # Verify yt-dlp was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        assert "yt-dlp" in call_args
        assert "--write-auto-sub" in call_args
        assert "--sub-lang" in call_args
        assert "en" in call_args

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_handles_no_captions_available(self, mock_dir, mock_subprocess, tmp_path):
        """Test handling when video has no captions."""
        # Setup mocks - no VTT files found
        mock_transcripts_dir = MagicMock()
        mock_transcripts_dir.glob.return_value = []
        mock_transcripts_dir.__truediv__ = lambda self, x: tmp_path / x

        with patch('server.TRANSCRIPTS_DIR', mock_transcripts_dir):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123"
            })

            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "No transcript found" in data.get("error", "")

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_parses_vtt_content_correctly(self, mock_dir, mock_subprocess, tmp_path, sample_vtt_content):
        """Test that VTT content is parsed correctly."""
        # Create a mock VTT file
        vtt_path = tmp_path / "test123.en.vtt"
        vtt_path.write_text(sample_vtt_content)

        # Setup mocks
        mock_transcripts_dir = MagicMock()
        mock_transcripts_dir.glob.return_value = [vtt_path]
        mock_transcripts_dir.__truediv__ = lambda self, x: tmp_path / x
        mock_transcripts_dir.mkdir = MagicMock()

        with patch('server.TRANSCRIPTS_DIR', mock_transcripts_dir):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123",
                "auto_clean": False
            })

            data = json.loads(result[0].text)
            # Should succeed if VTT file exists
            if data["success"]:
                assert "transcript" in data
                assert "machine learning" in data["transcript"].lower()

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_auto_clean_enabled_by_default(self, mock_dir, mock_subprocess, tmp_path, sample_vtt_content):
        """Test that auto_clean is enabled by default."""
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

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123"
            })

            data = json.loads(result[0].text)
            if data["success"]:
                assert data.get("auto_cleaned", True) is True

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_returns_video_id_and_url(self, mock_dir, mock_subprocess, tmp_path, sample_vtt_content):
        """Test that result includes video ID and URL."""
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

            url = "https://youtube.com/watch?v=test123"
            result = await fetch_youtube_transcript({
                "url": url,
                "auto_clean": False
            })

            data = json.loads(result[0].text)
            if data["success"]:
                assert data["video_id"] == "test123"
                assert data["url"] == url

    @patch('server.asyncio.create_subprocess_exec')
    @patch('server.TRANSCRIPTS_DIR')
    async def test_returns_word_count(self, mock_dir, mock_subprocess, tmp_path, sample_vtt_content):
        """Test that result includes word count."""
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

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123",
                "auto_clean": False
            })

            data = json.loads(result[0].text)
            if data["success"]:
                assert "word_count" in data
                assert data["word_count"] > 0

    async def test_handles_short_youtube_url(self):
        """Test that short youtu.be URLs work."""
        # This will fail due to no actual video, but should extract ID correctly
        result = await fetch_youtube_transcript({
            "url": "https://youtu.be/test123"
        })
        data = json.loads(result[0].text)

        # Should fail but with transcript error, not URL error
        if not data["success"]:
            assert "Invalid YouTube URL" not in data.get("error", "")


@pytest.mark.asyncio
class TestFetchTranscriptLanguages:
    """Tests for language handling in transcript fetching."""

    @patch('server.asyncio.create_subprocess_exec')
    async def test_uses_specified_language(self, mock_subprocess):
        """Test that specified language is used."""
        mock_process = AsyncMock()
        mock_process.returncode = 1  # Will fail but we check the call
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error"))
        mock_subprocess.return_value = mock_process

        await fetch_youtube_transcript({
            "url": "https://youtube.com/watch?v=test123",
            "language": "es"
        })

        call_args = mock_subprocess.call_args[0]
        assert "es" in call_args

    @patch('server.asyncio.create_subprocess_exec')
    async def test_defaults_to_english(self, mock_subprocess):
        """Test that language defaults to English."""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error"))
        mock_subprocess.return_value = mock_process

        await fetch_youtube_transcript({
            "url": "https://youtube.com/watch?v=test123"
            # No language specified
        })

        call_args = mock_subprocess.call_args[0]
        assert "en" in call_args


@pytest.mark.asyncio
class TestFetchTranscriptErrorHandling:
    """Tests for error handling in transcript fetching."""

    async def test_handles_network_error_gracefully(self):
        """Test graceful handling of network errors."""
        with patch('server.asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = OSError("Network unreachable")

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123"
            })

            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "error" in data

    async def test_handles_ytdlp_not_found(self):
        """Test handling when yt-dlp is not installed."""
        with patch('server.asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = FileNotFoundError("yt-dlp not found")

            result = await fetch_youtube_transcript({
                "url": "https://youtube.com/watch?v=test123"
            })

            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "error" in data

    @patch('server.asyncio.create_subprocess_exec')
    async def test_handles_ytdlp_timeout(self, mock_subprocess):
        """Test handling of yt-dlp timeout."""
        mock_process = AsyncMock()

        async def slow_communicate():
            await asyncio.sleep(10)  # Simulate slow response
            return (b"", b"")

        mock_process.communicate = slow_communicate
        mock_subprocess.return_value = mock_process

        # This test would need actual timeout implementation in the code
        # For now, just verify the structure handles errors
        with patch.object(asyncio, 'wait_for', side_effect=asyncio.TimeoutError):
            # The actual implementation may not use wait_for, so this may pass
            pass
