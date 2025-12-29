"""
Tests for MCP server tool handling.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import handle_list_tools, handle_call_tool


@pytest.mark.asyncio
class TestListTools:
    """Tests for handle_list_tools function."""

    async def test_returns_list_of_tools(self):
        """Test that list_tools returns a list."""
        tools = await handle_list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

    async def test_contains_required_tools(self):
        """Test that all required tools are present."""
        tools = await handle_list_tools()
        tool_names = [tool.name for tool in tools]

        required_tools = [
            "fetch_youtube_transcript",
            "clean_transcript",
            "extract_concepts",
            "extract_methodologies",
            "analyze_speakers",
            "store_video_knowledge"
        ]

        for required in required_tools:
            assert required in tool_names, f"Missing tool: {required}"

    async def test_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        tools = await handle_list_tools()

        for tool in tools:
            assert tool.description, f"Tool {tool.name} missing description"
            assert len(tool.description) > 10  # Meaningful description

    async def test_tools_have_input_schemas(self):
        """Test that all tools have input schemas."""
        tools = await handle_list_tools()

        for tool in tools:
            assert tool.inputSchema, f"Tool {tool.name} missing inputSchema"
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    async def test_fetch_youtube_transcript_schema(self):
        """Test fetch_youtube_transcript tool schema."""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "fetch_youtube_transcript")

        schema = tool.inputSchema
        assert "url" in schema["properties"]
        assert "url" in schema["required"]
        assert "language" in schema["properties"]
        assert "auto_clean" in schema["properties"]

    async def test_clean_transcript_schema(self):
        """Test clean_transcript tool schema."""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "clean_transcript")

        schema = tool.inputSchema
        assert "transcript" in schema["properties"]
        assert "transcript" in schema["required"]
        assert "remove_timestamps" in schema["properties"]
        assert "deduplicate" in schema["properties"]

    async def test_extract_concepts_schema(self):
        """Test extract_concepts tool schema."""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "extract_concepts")

        schema = tool.inputSchema
        assert "transcript" in schema["properties"]
        assert "transcript" in schema["required"]
        assert "min_frequency" in schema["properties"]
        assert "focus_domains" in schema["properties"]

    async def test_store_video_knowledge_schema(self):
        """Test store_video_knowledge tool schema."""
        tools = await handle_list_tools()
        tool = next(t for t in tools if t.name == "store_video_knowledge")

        schema = tool.inputSchema
        assert "video_metadata" in schema["properties"]
        assert "concepts" in schema["properties"]
        assert "video_metadata" in schema["required"]
        assert "concepts" in schema["required"]


@pytest.mark.asyncio
class TestCallTool:
    """Tests for handle_call_tool function."""

    async def test_routes_to_fetch_youtube_transcript(self):
        """Test routing to fetch_youtube_transcript."""
        with patch('server.fetch_youtube_transcript') as mock_fetch:
            mock_fetch.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("fetch_youtube_transcript", {"url": "test"})

            mock_fetch.assert_called_once_with({"url": "test"})

    async def test_routes_to_clean_transcript(self):
        """Test routing to clean_transcript."""
        with patch('server.clean_transcript') as mock_clean:
            mock_clean.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("clean_transcript", {"transcript": "test"})

            mock_clean.assert_called_once_with({"transcript": "test"})

    async def test_routes_to_extract_concepts(self):
        """Test routing to extract_concepts."""
        with patch('server.extract_concepts') as mock_extract:
            mock_extract.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("extract_concepts", {"transcript": "test"})

            mock_extract.assert_called_once_with({"transcript": "test"})

    async def test_routes_to_extract_methodologies(self):
        """Test routing to extract_methodologies."""
        with patch('server.extract_methodologies') as mock_extract:
            mock_extract.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("extract_methodologies", {"transcript": "test"})

            mock_extract.assert_called_once_with({"transcript": "test"})

    async def test_routes_to_analyze_speakers(self):
        """Test routing to analyze_speakers."""
        with patch('server.analyze_speakers') as mock_analyze:
            mock_analyze.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("analyze_speakers", {"transcript": "test"})

            mock_analyze.assert_called_once_with({"transcript": "test"})

    async def test_routes_to_store_video_knowledge(self):
        """Test routing to store_video_knowledge."""
        with patch('server.store_video_knowledge') as mock_store:
            mock_store.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("store_video_knowledge", {"video_metadata": {}, "concepts": []})

            mock_store.assert_called_once()

    async def test_raises_for_unknown_tool(self):
        """Test that unknown tool raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await handle_call_tool("unknown_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    async def test_handles_none_arguments(self):
        """Test handling of None arguments."""
        with patch('server.clean_transcript') as mock_clean:
            mock_clean.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("clean_transcript", None)

            # Should pass empty dict when arguments are None
            mock_clean.assert_called_once_with({})

    async def test_handles_empty_arguments(self):
        """Test handling of empty arguments dict."""
        with patch('server.extract_concepts') as mock_extract:
            mock_extract.return_value = [{"type": "text", "text": "{}"}]

            await handle_call_tool("extract_concepts", {})

            mock_extract.assert_called_once_with({})


@pytest.mark.asyncio
class TestToolReturnTypes:
    """Tests for tool return types."""

    async def test_clean_transcript_returns_text_content(self):
        """Test that clean_transcript returns TextContent."""
        from server import clean_transcript
        import mcp.types as types

        result = await clean_transcript({"transcript": "test"})

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].type == "text"

    async def test_extract_concepts_returns_text_content(self):
        """Test that extract_concepts returns TextContent."""
        from server import extract_concepts
        import mcp.types as types

        result = await extract_concepts({"transcript": "AI machine learning"})

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

    async def test_analyze_speakers_returns_text_content(self):
        """Test that analyze_speakers returns TextContent."""
        from server import analyze_speakers
        import mcp.types as types

        result = await analyze_speakers({"transcript": "test"})

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

    async def test_store_video_knowledge_returns_text_content(self):
        """Test that store_video_knowledge returns TextContent."""
        from server import store_video_knowledge
        import mcp.types as types

        result = await store_video_knowledge({
            "video_metadata": {},
            "concepts": []
        })

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)


@pytest.mark.asyncio
class TestToolResultParsing:
    """Tests for parsing tool results as JSON."""

    async def test_clean_transcript_result_is_valid_json(self):
        """Test that clean_transcript result is valid JSON."""
        from server import clean_transcript

        result = await clean_transcript({"transcript": "test transcript"})
        data = json.loads(result[0].text)

        assert "success" in data
        assert isinstance(data["success"], bool)

    async def test_extract_concepts_result_is_valid_json(self):
        """Test that extract_concepts result is valid JSON."""
        from server import extract_concepts

        result = await extract_concepts({"transcript": "AI and machine learning"})
        data = json.loads(result[0].text)

        assert "success" in data
        assert "concepts" in data

    async def test_analyze_speakers_result_is_valid_json(self):
        """Test that analyze_speakers result is valid JSON."""
        from server import analyze_speakers

        result = await analyze_speakers({"transcript": "test"})
        data = json.loads(result[0].text)

        assert "success" in data
        assert "speaker_count" in data

    async def test_store_video_knowledge_result_is_valid_json(self):
        """Test that store_video_knowledge result is valid JSON."""
        from server import store_video_knowledge

        result = await store_video_knowledge({
            "video_metadata": {"url": "test"},
            "concepts": ["AI"]
        })
        data = json.loads(result[0].text)

        assert "success" in data
        assert "entity_name" in data
