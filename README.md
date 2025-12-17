# Video Transcript MCP Server

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Part of Agentic System](https://img.shields.io/badge/Part_of-Agentic_System-brightgreen)](https://github.com/marc-shade/agentic-system-oss)

> **Autonomous knowledge acquisition from technical videos and talks via YouTube transcript processing.**

Part of the [Agentic System](https://github.com/marc-shade/agentic-system-oss) - a 24/7 autonomous AI framework with persistent memory.

## Features

- **YouTube Transcript Fetching**: Get transcripts from any YouTube video using yt-dlp
- **Transcript Cleaning**: Remove repetition, formatting artifacts, and stutters
- **Concept Extraction**: Identify key technical concepts discussed
- **Methodology Extraction**: Extract techniques and approaches described
- **Speaker Analysis**: Identify and separate multiple speakers
- **Memory Integration**: Store extracted knowledge in enhanced-memory system

## MCP Tools

| Tool | Description |
|------|-------------|
| `fetch_youtube_transcript` | Fetch transcript from YouTube URL |
| `clean_transcript` | Clean and structure raw transcript text |
| `extract_concepts` | Identify key technical concepts and terms |
| `extract_methodologies` | Extract techniques and best practices |
| `analyze_speakers` | Separate multiple speakers in transcript |
| `store_video_knowledge` | Store extracted knowledge in memory |

## Requirements

- Python 3.10+
- yt-dlp (for YouTube transcript fetching)
- mcp SDK

## Installation

```bash
pip install -r requirements.txt

# Install yt-dlp if not present
pip install yt-dlp
```

## Usage

```bash
# Run as MCP server
python server.py
```

## Configuration

Set `AGENTIC_SYSTEM_PATH` environment variable to configure the transcripts storage directory (defaults to `${AGENTIC_SYSTEM_PATH:-/opt/agentic}`).

## Integration

This MCP integrates with:
- **enhanced-memory-mcp**: For storing extracted knowledge
- **research-paper-mcp**: Complements academic paper research with video learning

## License

MIT
