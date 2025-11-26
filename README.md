# MCP Confluence Attachments

A Docker-based tool to download attachments (images and draw.io diagrams) from Confluence pages.

## Prerequisites

- Docker
- Confluence Personal Access Token (PAT)

## Building the Docker Image

```bash
docker build -t mcp-confluence-attachments .
```

## Usage

### Basic Usage

```bash
docker run --rm \
  -v $(pwd)/output:/output \
  -e CONFLUENCE_URL="https://confluence.derivco.co.za/" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  mcp-confluence-attachments <page_id> /output
```

### Example

Download all attachments from page 1142972070:

```bash
docker run --rm \
  -v $(pwd)/output:/output \
  -e CONFLUENCE_URL="https://confluence.derivco.co.za/" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  mcp-confluence-attachments 1142972070 /output
```

This will create:
- Images in `/output/` (e.g., `output/Site Design.png`)
- Draw.io diagrams in `/output/diagrams/` (e.g., `output/diagrams/Site Design.drawio`)

## What It Downloads

The tool downloads:
- **Images**: PNG, JPG, GIF, etc. (saved to root output directory)
- **Draw.io Diagrams**: `.drawio` files (saved to `diagrams/` subdirectory)

It automatically skips:
- Temporary/draft files (starting with `~`)
- Other file types (Word docs, PDFs, etc.)

## Future Plans

This tool is being developed as an MCP (Model Context Protocol) server to integrate with the `mcp-atlassian` package for seamless attachment downloading alongside Confluence page content.
