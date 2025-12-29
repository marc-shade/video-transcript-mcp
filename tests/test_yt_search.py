"""
Tests for YouTube search functionality (yt_search.py).
"""

import asyncio
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from yt_search import (
    VideoResult,
    _format_duration,
    _parse_entry,
    run_ytdlp,
    search_youtube,
    get_channel_videos,
    get_playlist_videos,
    get_trending,
    get_video_metadata
)


class TestFormatDuration:
    """Tests for _format_duration helper function."""

    def test_formats_seconds_only(self):
        """Test formatting for less than a minute."""
        result = _format_duration(45)
        assert result == "0:45"

    def test_formats_minutes_and_seconds(self):
        """Test formatting for minutes and seconds."""
        result = _format_duration(185)  # 3:05
        assert result == "3:05"

    def test_formats_hours_minutes_seconds(self):
        """Test formatting for hours, minutes, and seconds."""
        result = _format_duration(3725)  # 1:02:05
        assert result == "1:02:05"

    def test_handles_none(self):
        """Test handling of None input."""
        result = _format_duration(None)
        assert result is None

    def test_handles_zero(self):
        """Test handling of zero seconds."""
        result = _format_duration(0)
        assert result == "0:00"

    def test_pads_seconds_correctly(self):
        """Test that seconds are zero-padded."""
        result = _format_duration(65)  # 1:05
        assert result == "1:05"

    def test_pads_minutes_in_hours_format(self):
        """Test that minutes are zero-padded in hour format."""
        result = _format_duration(3665)  # 1:01:05
        assert result == "1:01:05"

    def test_handles_float_input(self):
        """Test handling of float duration (yt-dlp sometimes returns floats)."""
        result = _format_duration(125.5)
        assert result == "2:05"


class TestParseEntry:
    """Tests for _parse_entry function."""

    def test_parses_basic_entry(self, mock_yt_dlp_json_response):
        """Test parsing of basic video entry."""
        entry = mock_yt_dlp_json_response["entries"][0]
        result = _parse_entry(entry)

        assert isinstance(result, VideoResult)
        assert result.id == "video123"
        assert result.title == "Introduction to AI"
        assert result.channel == "Tech Channel"

    def test_uses_uploader_as_fallback(self, mock_yt_dlp_json_response):
        """Test that uploader is used when channel is missing."""
        entry = mock_yt_dlp_json_response["entries"][1]
        result = _parse_entry(entry)

        assert result.channel == "ML Expert"

    def test_generates_url_from_id(self, mock_yt_dlp_json_response):
        """Test that URL is generated from video ID."""
        entry = mock_yt_dlp_json_response["entries"][0]
        result = _parse_entry(entry)

        assert result.url == "https://youtube.com/watch?v=video123"

    def test_handles_missing_duration(self):
        """Test handling of missing duration."""
        entry = {"id": "test", "title": "Test"}
        result = _parse_entry(entry)

        assert result.duration is None
        assert result.duration_string is None

    def test_extracts_thumbnail(self, mock_yt_dlp_json_response):
        """Test thumbnail extraction from thumbnails array."""
        entry = mock_yt_dlp_json_response["entries"][0]
        result = _parse_entry(entry)

        assert result.thumbnail is not None
        assert "youtube.com" in result.thumbnail

    def test_handles_empty_entry(self):
        """Test handling of minimal entry."""
        entry = {"id": "", "title": ""}
        result = _parse_entry(entry)

        assert result.id == ""
        assert result.title == ""

    def test_to_dict_method(self, mock_yt_dlp_json_response):
        """Test VideoResult.to_dict() method."""
        entry = mock_yt_dlp_json_response["entries"][0]
        result = _parse_entry(entry)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["id"] == "video123"
        assert result_dict["title"] == "Introduction to AI"
        assert "url" in result_dict


@pytest.mark.asyncio
class TestRunYtdlp:
    """Tests for run_ytdlp function."""

    async def test_returns_json_on_success(self, mock_yt_dlp_json_response):
        """Test successful JSON parsing."""
        with patch('yt_search.asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(json.dumps(mock_yt_dlp_json_response).encode(), b"")
            )
            mock_exec.return_value = mock_process

            result = await run_ytdlp("ytsearch5:test", max_results=5)

            assert "entries" in result
            assert len(result["entries"]) == 2

    async def test_handles_timeout(self):
        """Test handling of timeout."""
        with patch('yt_search.asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()

            async def slow_communicate():
                await asyncio.sleep(100)
                return (b"", b"")

            mock_process.communicate = slow_communicate
            mock_exec.return_value = mock_process

            with patch('yt_search.asyncio.wait_for', side_effect=asyncio.TimeoutError):
                with pytest.raises(Exception) as exc_info:
                    await run_ytdlp("ytsearch5:test")

                assert "timed out" in str(exc_info.value).lower()

    async def test_handles_json_decode_error(self):
        """Test handling of invalid JSON response."""
        with patch('yt_search.asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(b"not valid json", b"")
            )
            mock_exec.return_value = mock_process

            with pytest.raises(Exception) as exc_info:
                await run_ytdlp("ytsearch5:test")

            assert "Invalid response" in str(exc_info.value)

    async def test_uses_cookies_by_default(self):
        """Test that browser cookies are used by default."""
        with patch('yt_search.asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"{}", b""))
            mock_exec.return_value = mock_process

            await run_ytdlp("ytsearch5:test", use_cookies=True)

            call_args = mock_exec.call_args[0]
            assert "--cookies-from-browser" in call_args

    async def test_skips_cookies_when_disabled(self):
        """Test that cookies are skipped when disabled."""
        with patch('yt_search.asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"{}", b""))
            mock_exec.return_value = mock_process

            await run_ytdlp("ytsearch5:test", use_cookies=False)

            call_args = mock_exec.call_args[0]
            assert "--cookies-from-browser" not in call_args


@pytest.mark.asyncio
class TestSearchYoutube:
    """Tests for search_youtube function."""

    async def test_builds_correct_search_url(self, mock_yt_dlp_json_response):
        """Test that search URL is built correctly."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await search_youtube("machine learning", max_results=5)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "ytsearch5:machine learning" in call_args

    async def test_returns_video_results(self, mock_yt_dlp_json_response):
        """Test that VideoResult objects are returned."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            results = await search_youtube("test query")

            assert all(isinstance(r, VideoResult) for r in results)
            assert len(results) == 2

    async def test_handles_empty_results(self):
        """Test handling of empty search results."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = {"entries": []}

            results = await search_youtube("very specific query")

            assert results == []

    async def test_filters_invalid_entries(self):
        """Test that entries without IDs are filtered out."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = {
                "entries": [
                    {"id": "valid", "title": "Valid Video"},
                    {"id": None, "title": "Invalid"},
                    None,
                    {"id": "", "title": "Empty ID"}
                ]
            }

            results = await search_youtube("test")

            # Should only include entry with valid ID
            assert len(results) == 1
            assert results[0].id == "valid"


@pytest.mark.asyncio
class TestGetChannelVideos:
    """Tests for get_channel_videos function."""

    async def test_normalizes_handle_format(self, mock_yt_dlp_json_response):
        """Test that @handle format is normalized."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_channel_videos("@testchannel")

            call_args = mock_run.call_args[0][0]
            assert "youtube.com/@testchannel/videos" in call_args

    async def test_normalizes_channel_id(self, mock_yt_dlp_json_response):
        """Test that channel ID is normalized."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_channel_videos("UC123456")

            call_args = mock_run.call_args[0][0]
            assert "channel/UC123456/videos" in call_args

    async def test_adds_videos_path_to_url(self, mock_yt_dlp_json_response):
        """Test that /videos is added to URL if missing."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_channel_videos("https://youtube.com/channel/UC123")

            call_args = mock_run.call_args[0][0]
            assert "/videos" in call_args


@pytest.mark.asyncio
class TestGetPlaylistVideos:
    """Tests for get_playlist_videos function."""

    async def test_normalizes_playlist_id(self, mock_yt_dlp_json_response):
        """Test that playlist ID is normalized to URL."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_playlist_videos("PLtest123")

            call_args = mock_run.call_args[0][0]
            assert "playlist?list=PLtest123" in call_args

    async def test_uses_full_url(self, mock_yt_dlp_json_response):
        """Test that full URL is used directly."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            full_url = "https://youtube.com/playlist?list=PLtest"
            await get_playlist_videos(full_url)

            call_args = mock_run.call_args[0][0]
            assert call_args == full_url


@pytest.mark.asyncio
class TestGetTrending:
    """Tests for get_trending function."""

    async def test_uses_trending_path_for_now(self, mock_yt_dlp_json_response):
        """Test that 'now' category uses trending path."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_trending(category="now")

            call_args = mock_run.call_args[0][0]
            assert "trending" in call_args

    async def test_uses_gaming_path(self, mock_yt_dlp_json_response):
        """Test that 'gaming' category uses gaming path."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = mock_yt_dlp_json_response

            await get_trending(category="gaming")

            call_args = mock_run.call_args[0][0]
            assert "gaming" in call_args


@pytest.mark.asyncio
class TestGetVideoMetadata:
    """Tests for get_video_metadata function."""

    async def test_normalizes_video_id(self):
        """Test that video ID is normalized to URL."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = {
                "id": "test123",
                "title": "Test Video",
                "channel": "Test Channel",
                "duration": 300
            }

            result = await get_video_metadata("test123")

            call_args = mock_run.call_args[0][0]
            assert "watch?v=test123" in call_args
            assert result is not None
            assert result.id == "test123"

    async def test_uses_full_url(self):
        """Test that full URL is used directly."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = {
                "id": "test123",
                "title": "Test",
                "channel": "Channel"
            }

            full_url = "https://youtube.com/watch?v=test123"
            await get_video_metadata(full_url)

            call_args = mock_run.call_args[0][0]
            assert call_args == full_url

    async def test_returns_none_on_empty_result(self):
        """Test that None is returned when no result."""
        with patch('yt_search.run_ytdlp') as mock_run:
            mock_run.return_value = {}

            result = await get_video_metadata("nonexistent")

            assert result is None
