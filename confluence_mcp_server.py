#!/usr/bin/env python3
"""MCP Server for Confluence Attachment Operations."""

import logging
import logging.config
import os
import sys
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.endpoints import HTTPEndpoint

from config import settings, logging_config
from confluence_client import ConfluenceAttachmentClient

# Configure logging
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("Confluence Attachments MCP")


def log(message: str, level: str = "info"):
    """Helper function for consistent logging."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)


def resolve_output_path(path: str) -> str:
    """Resolve output path for Docker container environment.

    When running in Docker with a mounted /output directory, this function
    ensures that relative paths are written to /output instead of /app.

    Args:
        path: The path provided by the user (relative or absolute)

    Returns:
        Resolved absolute path appropriate for the environment
    """
    # If path is already absolute, use it as-is
    if os.path.isabs(path):
        return path

    # Check if we're in a Docker container by seeing if /output exists
    # and we're running from /app (the container's WORKDIR)
    if os.path.exists('/output') and os.getcwd() == '/app':
        # Prepend /output/ to relative paths
        return os.path.join('/output', path)

    # For local development, use the path as provided (relative to current directory)
    return path


def get_confluence_client():
    """Get configured Confluence client."""
    if not settings.CONFLUENCE_URL:
        raise ValueError("CONFLUENCE_URL environment variable not set")
    if not settings.CONFLUENCE_PERSONAL_TOKEN:
        raise ValueError("CONFLUENCE_PERSONAL_TOKEN environment variable not set")

    return ConfluenceAttachmentClient(
        settings.CONFLUENCE_URL,
        settings.CONFLUENCE_PERSONAL_TOKEN
    )


@mcp.tool(description="""
    [STEP 1] List all attachments for a Confluence page.

    Retrieves metadata for all attachments on a specified Confluence page,
    excluding temporary and draft files. This is typically the first step
    in the attachment workflow - use this to see what's available before
    downloading.

    Args:
        page_id (str): The Confluence page ID (numeric)

    Returns:
        dict: Status and list of attachments with metadata including:
            - id: Attachment ID
            - title: Attachment filename
            - mediaType: MIME type
            - fileSize: Size in bytes
            - isImage: Boolean indicating if it's an image
            - isDiagram: Boolean indicating if it's a draw.io diagram
    """)
def list_attachments(page_id: str):
    """List all attachments for a Confluence page."""
    page_id = str(page_id)

    log(f"Listing attachments for page {page_id}")

    try:
        client = get_confluence_client()
        attachments = client.list_attachments(page_id)

        return {
            "status": "success",
            "page_id": page_id,
            "count": len(attachments),
            "attachments": attachments
        }
    except ValueError as e:
        log(f"Configuration error: {str(e)}", "error")
        return {
            "status": "error",
            "error": "configuration_error",
            "message": str(e)
        }
    except Exception as e:
        log(f"Error listing attachments: {str(e)}", "error")
        return {
            "status": "error",
            "error": "api_error",
            "message": f"Failed to list attachments: {str(e)}"
        }


@mcp.tool(description="""
    [STEP 2] Get detailed metadata for a specific attachment.

    Retrieves complete metadata for a single attachment by its ID.
    Use this to inspect details before downloading.

    Args:
        page_id (str): The Confluence page ID
        attachment_id (str): The attachment ID

    Returns:
        dict: Status and attachment metadata or error
    """)
def get_attachment_metadata(page_id: str, attachment_id: str):
    """Get metadata for a specific attachment."""
    page_id = str(page_id)
    attachment_id = str(attachment_id)

    log(f"Getting metadata for attachment {attachment_id} on page {page_id}")

    try:
        client = get_confluence_client()
        metadata = client.get_attachment_metadata(page_id, attachment_id)

        if metadata is None:
            return {
                "status": "error",
                "error": "not_found",
                "message": f"Attachment {attachment_id} not found on page {page_id}"
            }

        return {
            "status": "success",
            "attachment": metadata
        }
    except ValueError as e:
        log(f"Configuration error: {str(e)}", "error")
        return {
            "status": "error",
            "error": "configuration_error",
            "message": str(e)
        }
    except Exception as e:
        log(f"Error getting attachment metadata: {str(e)}", "error")
        return {
            "status": "error",
            "error": "api_error",
            "message": f"Failed to get attachment metadata: {str(e)}"
        }


@mcp.tool(description="""
    [STEP 3] Download all attachments from a Confluence page.

    Downloads all (or filtered) attachments from a page to a specified
    directory. Images are saved to the root output directory, while
    draw.io diagrams are saved to output_dir/diagrams/.

    Args:
        page_id (str): The Confluence page ID
        output_dir (str): Local directory path to save files
        download_images (bool): Whether to download image files (default: True)
        download_diagrams (bool): Whether to download draw.io diagrams (default: True)

    Returns:
        dict: Status and list of download results for each attachment
    """)
def download_all_attachments(page_id: str, output_dir: str,
                            download_images: bool = True,
                            download_diagrams: bool = True):
    """Download all attachments from a Confluence page."""
    page_id = str(page_id)
    output_dir = str(output_dir)

    # Resolve the output directory for Docker environment
    resolved_output_dir = resolve_output_path(output_dir)

    log(f"Downloading attachments from page {page_id} to {output_dir}")
    log(f"Resolved path: {resolved_output_dir}")
    log(f"Filters - images: {download_images}, diagrams: {download_diagrams}")

    try:
        client = get_confluence_client()
        results = client.download_attachments(
            page_id,
            resolved_output_dir,
            download_images,
            download_diagrams
        )

        success_count = sum(1 for r in results if r['status'] == 'success')

        return {
            "status": "success",
            "page_id": page_id,
            "output_dir": output_dir,
            "total_attachments": len(results),
            "downloaded": success_count,
            "results": results
        }
    except ValueError as e:
        log(f"Configuration error: {str(e)}", "error")
        return {
            "status": "error",
            "error": "configuration_error",
            "message": str(e)
        }
    except Exception as e:
        log(f"Error downloading attachments: {str(e)}", "error")
        return {
            "status": "error",
            "error": "download_error",
            "message": f"Failed to download attachments: {str(e)}"
        }


@mcp.tool(description="""
    [STEP 4] Download a specific attachment by ID.

    Downloads a single attachment to a specified file path. You must
    provide the full output path including filename.

    Args:
        page_id (str): The Confluence page ID
        attachment_id (str): The attachment ID
        output_path (str): Full local file path (including filename) to save to

    Returns:
        dict: Status and download details (file size, path) or error
    """)
def download_specific_attachment(page_id: str, attachment_id: str, output_path: str):
    """Download a specific attachment by ID."""
    page_id = str(page_id)
    attachment_id = str(attachment_id)
    output_path = str(output_path)

    # Resolve the output path for Docker environment
    resolved_output_path = resolve_output_path(output_path)

    log(f"Downloading attachment {attachment_id} from page {page_id} to {output_path}")
    log(f"Resolved path: {resolved_output_path}")

    try:
        client = get_confluence_client()

        # First get the attachment metadata to get download URL
        metadata = client.get_attachment_metadata(page_id, attachment_id)
        if metadata is None:
            return {
                "status": "error",
                "error": "not_found",
                "message": f"Attachment {attachment_id} not found on page {page_id}"
            }

        # Download the attachment
        result = client.download_attachment(
            attachment_id,
            metadata['downloadUrl'],
            resolved_output_path
        )
        result['title'] = metadata['title']

        return {
            "status": "success",
            "attachment": result
        }
    except ValueError as e:
        log(f"Configuration error: {str(e)}", "error")
        return {
            "status": "error",
            "error": "configuration_error",
            "message": str(e)
        }
    except Exception as e:
        log(f"Error downloading attachment: {str(e)}", "error")
        return {
            "status": "error",
            "error": "download_error",
            "message": f"Failed to download attachment: {str(e)}"
        }


# Tools endpoint for HTTP/SSE mode
class ToolsEndpoint(HTTPEndpoint):
    """Endpoint to list available tools."""
    async def get(self, request):
        tools = mcp.list_tools()
        return JSONResponse(tools)


# Starlette app for HTTP/SSE transport
app = Starlette(routes=[
    Route("/tools", ToolsEndpoint),
])

# Mount MCP SSE app
app.mount("/", mcp.sse_app())


def get_application():
    """Get Starlette application for Uvicorn."""
    return app


if __name__ == "__main__":
    transport = settings.MCP_TRANSPORT.lower()

    if transport == 'stdio':
        log(f"Starting Confluence Attachments MCP Server with stdio transport")
        log(f"Confluence URL: {settings.CONFLUENCE_URL}")
        log(f"Debug mode: {'ON' if settings.MCP_DEBUG else 'OFF'}")

        try:
            mcp.run(transport="stdio")
        except KeyboardInterrupt:
            log("Server stopped by user", "info")
        except Exception as e:
            log(f"Server error: {e}", "error")
            sys.exit(1)

    elif transport in ('sse', 'http'):
        log(f"Starting Confluence Attachments MCP Server at http://{settings.MCP_HOST}:{settings.MCP_PORT}")
        log(f"SSE Endpoint: http://{settings.MCP_HOST}:{settings.MCP_PORT}/sse")
        log(f"Tools Endpoint: http://{settings.MCP_HOST}:{settings.MCP_PORT}/tools")
        log(f"Confluence URL: {settings.CONFLUENCE_URL}")
        log(f"Debug mode: {'ON' if settings.MCP_DEBUG else 'OFF'}")
        log(f"Auto-reload: {'ENABLED' if settings.MCP_RELOAD else 'DISABLED'}")

        uvicorn_config = {
            "app": "confluence_mcp_server:get_application",
            "host": settings.MCP_HOST,
            "port": settings.MCP_PORT,
            "reload": settings.MCP_RELOAD,
            "log_level": "debug" if settings.MCP_DEBUG else settings.LOG_LEVEL.lower()
        }

        logger.debug(f"Uvicorn config: {uvicorn_config}")
        uvicorn.run(**uvicorn_config)

    else:
        logger.error(f"Unknown transport: {transport}")
        sys.exit(1)
