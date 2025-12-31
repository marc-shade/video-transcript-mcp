# Video Transcript MCP Server

Autonomous knowledge acquisition from technical videos and talks via YouTube transcript processing.

## Description

Video Transcript MCP enables AI systems to learn from YouTube tutorials, conference talks, technical presentations, and expert interviews. Uses yt-dlp for reliable transcript extraction with intelligent cleaning and concept extraction.

## Features

- **YouTube Transcript Fetching**: Get transcripts from any YouTube video using yt-dlp
- **Transcript Cleaning**: Remove repetition, formatting artifacts, and stutters
- **Concept Extraction**: Identify key technical concepts with frequency analysis
- **Methodology Extraction**: Extract techniques and approaches described
- **Speaker Analysis**: Identify and separate multiple speakers
- **Memory Integration**: Store extracted knowledge in enhanced-memory system

## Installation

```bash
git clone https://github.com/marc-shade/video-transcript-mcp
cd video-transcript-mcp
pip install -r requirements.txt

# Requires yt-dlp
pip install yt-dlp
```

## Configuration

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "video-transcript": {
      "command": "python3",
      "args": ["/absolute/path/to/video-transcript-mcp/server.py"],
      "env": {
        "AGENTIC_SYSTEM_PATH": "/path/to/agentic-system"
      }
    }
  }
}
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `fetch_youtube_transcript` | Fetch transcript from YouTube URL via yt-dlp |
| `clean_transcript` | Clean and structure raw transcript text |
| `extract_concepts` | Identify key technical concepts and terms |
| `extract_methodologies` | Extract techniques and best practices |
| `analyze_speakers` | Separate multiple speakers in transcript |
| `store_video_knowledge` | Store extracted knowledge in enhanced-memory |

## Usage Examples

### Fetch Transcript

```python
result = mcp__video-transcript__fetch_youtube_transcript(
    url="https://youtube.com/watch?v=abc123",
    language="en",
    auto_clean=True
)
# Returns: {
#   "transcript": "Full cleaned transcript...",
#   "video_id": "abc123",
#   "title": "Video Title",
#   "duration": "15:32"
# }
```

### Extract Concepts

```python
concepts = mcp__video-transcript__extract_concepts(
    transcript="Long transcript text...",
    min_frequency=2,
    focus_domains=["AI", "machine learning", "AGI"]
)
# Returns: {
#   "concepts": ["transformer", "attention", "self-improvement"],
#   "frequencies": {"transformer": 15, "attention": 12, ...}
# }
```

### Extract Methodologies

```python
methods = mcp__video-transcript__extract_methodologies(
    transcript="Long transcript text..."
)
# Returns: {
#   "methodologies": ["fine-tuning", "transfer learning", "RLHF"],
#   "descriptions": {...}
# }
```

### Store Video Knowledge

```python
mcp__video-transcript__store_video_knowledge(
    video_id="abc123",
    concepts=["transformers", "attention mechanisms"],
    methodologies=["fine-tuning", "transfer learning"],
    insights=["Key insight about AGI..."]
)
# Stores in enhanced-memory for later retrieval
```

## Requirements

- Python 3.10+
- yt-dlp
- mcp SDK
- Dependencies in requirements.txt

## Storage

Transcripts are saved to `$AGENTIC_SYSTEM_PATH/video-transcripts/`

## Integration

This MCP integrates with:
- **enhanced-memory-mcp**: For storing extracted knowledge
- **research-paper-mcp**: Complements academic paper research with video learning

## Links

- GitHub: https://github.com/marc-shade/video-transcript-mcp
- Issues: https://github.com/marc-shade/video-transcript-mcp/issues

## License

MIT
