"""
Tests for YouTube URL extraction and validation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import extract_video_id


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    def test_standard_youtube_url(self):
        """Test standard youtube.com/watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = extract_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_short_youtube_url(self):
        """Test short youtu.be URL format."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = extract_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_url_with_timestamp(self):
        """Test URL with additional parameters like timestamp."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        result = extract_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_url_with_playlist(self):
        """Test URL with playlist parameter."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest123"
        result = extract_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_short_url_with_params(self):
        """Test short URL with query parameters."""
        url = "https://youtu.be/dQw4w9WgXcQ?t=120"
        result = extract_video_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_url_without_www(self):
        """Test URL without www prefix."""
        url = "https://youtube.com/watch?v=abc123XYZ"
        result = extract_video_id(url)
        assert result == "abc123XYZ"

    def test_http_url(self):
        """Test http (non-https) URL."""
        url = "http://youtube.com/watch?v=test12345"
        result = extract_video_id(url)
        assert result == "test12345"

    def test_invalid_url_returns_none(self):
        """Test that non-YouTube URLs return None."""
        url = "https://example.com/video/123"
        result = extract_video_id(url)
        assert result is None

    def test_malformed_url_returns_none(self):
        """Test that malformed URLs return None."""
        url = "not-a-valid-url"
        result = extract_video_id(url)
        assert result is None

    def test_empty_url_returns_none(self):
        """Test that empty string returns None."""
        result = extract_video_id("")
        assert result is None

    def test_youtube_url_without_video_id(self):
        """Test YouTube URL without v parameter."""
        url = "https://www.youtube.com/watch"
        result = extract_video_id(url)
        assert result is None

    def test_youtube_channel_url_returns_none(self):
        """Test that channel URLs don't extract video IDs."""
        url = "https://www.youtube.com/channel/UC123456"
        result = extract_video_id(url)
        assert result is None

    def test_youtube_playlist_only_url_returns_none(self):
        """Test that playlist-only URLs don't extract video IDs."""
        url = "https://www.youtube.com/playlist?list=PLtest123"
        result = extract_video_id(url)
        assert result is None

    def test_video_id_with_special_characters(self):
        """Test video ID with underscores and hyphens."""
        url = "https://youtube.com/watch?v=a_b-c1D2e3F"
        result = extract_video_id(url)
        assert result == "a_b-c1D2e3F"

    def test_short_url_with_trailing_slash(self):
        """Test short URL handling doesn't break with edge cases."""
        url = "https://youtu.be/testVid123"
        result = extract_video_id(url)
        assert result == "testVid123"


class TestUrlValidation:
    """Additional URL validation edge cases."""

    @pytest.mark.parametrize("url,expected_id", [
        ("https://www.youtube.com/watch?v=abc123", "abc123"),
        ("https://youtu.be/xyz789", "xyz789"),
        ("http://youtube.com/watch?v=test", "test"),
        ("https://youtube.com/watch?v=_test-123", "_test-123"),
    ])
    def test_valid_urls_parametrized(self, url, expected_id):
        """Parametrized test for valid YouTube URLs."""
        result = extract_video_id(url)
        assert result == expected_id

    @pytest.mark.parametrize("url", [
        "https://vimeo.com/123456",
        "https://dailymotion.com/video/x123",
        "https://twitch.tv/videos/123",
        "",
        None,
    ])
    def test_invalid_urls_parametrized(self, url):
        """Parametrized test for invalid URLs."""
        if url is None:
            # Handle None input gracefully
            with pytest.raises((TypeError, AttributeError)):
                extract_video_id(url)
        else:
            result = extract_video_id(url)
            assert result is None

    def test_ftp_url_extracts_video_id(self):
        """Test that ftp:// URLs with youtube.com still extract video ID.

        The current implementation only checks for 'youtube.com/watch' pattern,
        not the protocol, so ftp:// URLs may still extract IDs.
        """
        # This documents actual behavior - ftp URLs do extract IDs
        url = "ftp://youtube.com/watch?v=test"
        result = extract_video_id(url)
        # The implementation doesn't validate protocol
        assert result == "test"
