# MCP Confluence Attachments

A Model Context Protocol (MCP) server and CLI tool for downloading images and draw.io diagrams from Confluence pages.

## Features

- **MCP Server**: Expose Confluence attachment operations as MCP tools for AI assistants
- **CLI Tool**: Standalone command-line interface for downloading attachments
- **Docker Support**: Run as a containerized application
- **Flexible Transport**: Support for stdio and HTTP/SSE communication modes
- **Smart Filtering**: Download only images, only diagrams, or both
- **Organized Storage**: Automatic directory organization (images in root, diagrams in subdirectory)

## Installation

### Local Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mcp-confluence-attachments
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Confluence credentials
```

### Docker Installation

#### Option 1: Pull from Docker Hub (Recommended)

Pull the pre-built image:
```bash
docker pull quintindk/mcp-confluence-attachments:latest
```

#### Option 2: Build Locally

Build the Docker image yourself:
```bash
docker build -t mcp-confluence-attachments .
```

### Quick Start with Claude Code (Recommended)

If you're using Claude Code, you can add the MCP server with a single command:

```bash
claude mcp add confluence-attachments -s user -- sh -c "docker run -i --rm -e MCP_DEBUG=false -v \$(pwd):/app -e LOG_LEVEL=INFO -e MCP_TRANSPORT=stdio -e CONFLUENCE_URL=https://your-instance.atlassian.net -e CONFLUENCE_PERSONAL_TOKEN=\$CONFLUENCE_TOKEN mcp-confluence-attachments"
```

**Important notes:**
- Replace `https://your-instance.atlassian.net` with your Confluence URL
- Set the `CONFLUENCE_TOKEN` environment variable in your shell before running this command:
  ```bash
  export CONFLUENCE_TOKEN="your_personal_access_token"
  ```
- The `-v $(pwd):/app` volume mount ensures downloaded files appear in your current working directory
- The `-s user` flag installs the server for your user account only

## MCP Server Usage

The MCP server exposes four tools for working with Confluence attachments:

### Available Tools

1. **list_attachments**: List all attachments on a Confluence page
   - Input: `page_id`
   - Output: List of attachment metadata (ID, title, media type, file size, etc.)

2. **get_attachment_metadata**: Get detailed metadata for a specific attachment
   - Input: `page_id`, `attachment_id`
   - Output: Complete attachment metadata

3. **download_all_attachments**: Download all (or filtered) attachments from a page
   - Input: `page_id`, `output_dir`, `download_images` (bool), `download_diagrams` (bool)
   - Output: Download results for each attachment

4. **download_specific_attachment**: Download a single attachment by ID
   - Input: `page_id`, `attachment_id`, `output_path`
   - Output: Download status and file details

### Running the MCP Server

#### Stdio Mode (for Claude Desktop/CLI integration)

```bash
python confluence_mcp_server.py
```

Or with explicit environment variables:
```bash
CONFLUENCE_URL="https://your-instance.atlassian.net" \
CONFLUENCE_PERSONAL_TOKEN="your_token" \
python confluence_mcp_server.py
```

#### HTTP/SSE Mode (for web-based clients)

```bash
MCP_TRANSPORT=sse python confluence_mcp_server.py
```

The server will start at `http://0.0.0.0:8080` with:
- SSE endpoint: `http://0.0.0.0:8080/sse`
- Tools listing: `http://0.0.0.0:8080/tools`

### Claude Desktop Configuration (Manual Method)

**Note:** If you're using Claude Code, use the `claude mcp add` command shown in the Quick Start section above instead of manually editing config files.

For Claude Desktop, add to your config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Using Docker (Recommended):
```json
{
  "mcpServers": {
    "confluence-attachments": {
      "command": "sh",
      "args": [
        "-c",
        "cd \"$(pwd)\" && docker run -i --rm -v $(pwd):/app -e MCP_TRANSPORT=stdio -e CONFLUENCE_URL=https://your-instance.atlassian.net -e CONFLUENCE_PERSONAL_TOKEN=$CONFLUENCE_TOKEN mcp-confluence-attachments"
      ]
    }
  }
}
```

Set the `CONFLUENCE_TOKEN` environment variable in your shell:
```bash
export CONFLUENCE_TOKEN="your_personal_access_token"
```

#### Using Python Directly:
```json
{
  "mcpServers": {
    "confluence-attachments": {
      "command": "python",
      "args": ["/absolute/path/to/confluence_mcp_server.py"],
      "env": {
        "CONFLUENCE_URL": "https://your-instance.atlassian.net",
        "CONFLUENCE_PERSONAL_TOKEN": "your_personal_access_token"
      }
    }
  }
}
```

### Environment Variables

#### Required
- `CONFLUENCE_URL`: Base URL of your Confluence instance (e.g., `https://your-instance.atlassian.net`)
- `CONFLUENCE_PERSONAL_TOKEN`: Personal Access Token for authentication

#### Optional MCP Server Settings
- `MCP_TRANSPORT`: Communication mode (`stdio`, `sse`, or `http`) - default: `stdio`
- `MCP_HOST`: Server host address - default: `0.0.0.0`
- `MCP_PORT`: Server port - default: `8080`
- `MCP_DEBUG`: Enable debug logging (`true`/`false`) - default: `false`
- `MCP_RELOAD`: Enable auto-reload in development - default: `false`
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) - default: `INFO`

## CLI Tool Usage

The standalone CLI tool can be used independently of the MCP server:

```bash
python download_attachments.py <page_id> [output_dir]
```

### Examples

```bash
# Download all attachments to current directory
python download_attachments.py 1142972070

# Download to specific directory
python download_attachments.py 1142972070 ./my-downloads

# View help
python download_attachments.py --help
```

### Environment Variables for CLI

Set these in your shell or `.env` file:
```bash
export CONFLUENCE_URL="https://your-instance.atlassian.net"
export CONFLUENCE_PERSONAL_TOKEN="your_token_here"
```

## Docker Usage

The Docker container runs the MCP server by default, making it easy to deploy as a service.

### Running the MCP Server (Stdio Mode with Volume Mount)

For stdio mode (used by Claude Code and Claude Desktop), you need to mount your current directory so downloaded files appear on the host:

```bash
docker run -i --rm \
  -v $(pwd):/app \
  -e MCP_TRANSPORT=stdio \
  -e CONFLUENCE_URL="https://your-instance.atlassian.net" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  mcp-confluence-attachments
```

**Why the volume mount?**
- Without `-v $(pwd):/app`, files are written inside the container and aren't accessible on your host
- The mount makes the current directory available at `/app` in the container (the container's working directory)
- Downloaded files will appear in your current directory on the host

### Running the MCP Server (HTTP/SSE Mode)

Start the MCP server in a container:

```bash
docker run --rm \
  -p 8080:8080 \
  -e CONFLUENCE_URL="https://your-instance.atlassian.net" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  mcp-confluence-attachments
```

The server will be accessible at:
- SSE endpoint: `http://localhost:8080/sse`
- Tools listing: `http://localhost:8080/tools`

#### Run in Background

```bash
docker run -d \
  --name confluence-mcp \
  -p 8080:8080 \
  -e CONFLUENCE_URL="https://your-instance.atlassian.net" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  mcp-confluence-attachments
```

View logs:
```bash
docker logs -f confluence-mcp
```

Stop the server:
```bash
docker stop confluence-mcp
```

### Using the CLI Tool in Docker

You can also use the CLI tool by overriding the entrypoint:

```bash
docker run --rm \
  -v $(pwd)/output:/output \
  -e CONFLUENCE_URL="https://your-instance.atlassian.net" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token-here" \
  --entrypoint python \
  mcp-confluence-attachments download_attachments.py 1142972070 /output
```

This will create:
- Images in `output/` (e.g., `output/Site Design.png`)
- Draw.io diagrams in `output/diagrams/` (e.g., `output/diagrams/Site Design.drawio`)

### Docker Environment Variables

All MCP server environment variables can be set when running the container:

```bash
docker run --rm \
  -p 8080:8080 \
  -e CONFLUENCE_URL="https://your-instance.atlassian.net" \
  -e CONFLUENCE_PERSONAL_TOKEN="your-token" \
  -e MCP_TRANSPORT="sse" \
  -e MCP_PORT="8080" \
  -e MCP_DEBUG="true" \
  -e LOG_LEVEL="DEBUG" \
  mcp-confluence-attachments
```

## What It Downloads

The tool downloads:
- **Images**: PNG, JPG, GIF, etc. (saved to root output directory)
- **Draw.io Diagrams**: `.drawio` files (saved to `diagrams/` subdirectory)

It automatically skips:
- Temporary/draft files (starting with `~`)
- Files with "draft" in their media type
- Other file types (Word docs, PDFs, etc.)

## Getting a Confluence Personal Access Token

1. Log in to your Confluence instance
2. Click your profile picture → **Settings**
3. Go to **Security** → **Personal Access Tokens**
4. Click **Create token**
5. Give it a name and set expiration
6. Copy the token (you won't be able to see it again!)

## Development

### Running Tests

```bash
# TODO: Add test instructions once tests are implemented
```

### Project Structure

```
mcp-confluence-attachments/
├── .github/
│   └── workflows/
│       └── docker-publish.yml    # GitHub Actions CI/CD workflow
├── confluence_mcp_server.py      # Main MCP server
├── confluence_client.py          # Confluence API client wrapper
├── config.py                     # Configuration management
├── download_attachments.py       # Standalone CLI tool
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── Dockerfile                    # Docker container definition
├── CICD_SETUP.md                 # CI/CD setup guide
└── README.md                     # This file
```

## Troubleshooting

### Configuration Errors

If you see `CONFLUENCE_URL environment variable not set`:
- Make sure your `.env` file exists and contains the required variables
- Or export them in your shell before running the server

### Authentication Errors

If you get 401 or 403 errors:
- Verify your Personal Access Token is correct and not expired
- Check that your token has permissions to access the Confluence page
- Ensure the CONFLUENCE_URL matches your instance URL exactly

### Connection Errors

If the server can't connect to Confluence:
- Verify your CONFLUENCE_URL is correct (include https://)
- Check your network connection and firewall settings
- Try accessing the Confluence URL in a web browser

## CI/CD and Publishing

This project includes automated Docker image builds and publishing to Docker Hub using GitHub Actions.

### Automated Builds

Every push to the `main` branch automatically:
- Builds a multi-platform Docker image (amd64 and arm64)
- Pushes the image to Docker Hub with the `latest` tag
- Updates the Docker Hub repository description

Version tags (e.g., `v1.0.0`) automatically create versioned images:
- `yourusername/mcp-confluence-attachments:v1.0.0`
- `yourusername/mcp-confluence-attachments:v1.0`
- `yourusername/mcp-confluence-attachments:v1`

### Setting Up CI/CD for Your Fork

If you fork this repository and want to publish to your own Docker Hub account:

1. Read the detailed setup guide: [CICD_SETUP.md](CICD_SETUP.md)
2. Create a Docker Hub access token
3. Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets to your GitHub repository
4. Push to `main` or create a version tag

The workflow file is located at `.github/workflows/docker-publish.yml`.

## License

[Add your license here]

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
