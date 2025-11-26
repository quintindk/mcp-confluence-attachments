#!/usr/bin/env python3
"""Download Confluence page attachments using the atlassian-python-api package."""

import os
import sys
from atlassian import Confluence


def download_attachments(confluence_url, token, page_id, output_dir, download_images=True, download_diagrams=True):
    """Download attachments from a Confluence page.

    Args:
        confluence_url: Base URL of Confluence instance
        token: Personal access token
        page_id: ID of the Confluence page
        output_dir: Directory to save attachments
        download_images: Whether to download image files (default: True)
        download_diagrams: Whether to download draw.io diagram files (default: True)
    """
    # Initialize Confluence client
    confluence = Confluence(
        url=confluence_url,
        token=token
    )

    # Get page attachments
    print(f"Fetching attachments for page {page_id}...")
    attachments = confluence.get_attachments_from_content(page_id)

    if not attachments or 'results' not in attachments:
        print("No attachments found.")
        return

    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    diagrams_dir = os.path.join(output_dir, "diagrams")
    if download_diagrams:
        os.makedirs(diagrams_dir, exist_ok=True)

    # Download each attachment
    for attachment in attachments['results']:
        title = attachment['title']
        attachment_id = attachment['id']
        media_type = attachment.get('metadata', {}).get('mediaType', '')

        # Skip temporary/draft files
        if 'draft' in media_type.lower() or title.startswith('~'):
            print(f"Skipping temporary file: {title} (type: {media_type})")
            continue

        # Determine if this is a file we want to download
        is_image = media_type.startswith('image/')
        is_diagram = media_type == 'application/vnd.jgraph.mxfile'

        if is_image and not download_images:
            print(f"Skipping image: {title}")
            continue
        elif is_diagram and not download_diagrams:
            print(f"Skipping diagram: {title}")
            continue
        elif not is_image and not is_diagram:
            print(f"Skipping {title} (type: {media_type})")
            continue

        # Determine output path based on file type
        if is_diagram:
            # Add .drawio extension if not present
            filename = title if title.endswith('.drawio') else f"{title}.drawio"
            output_path = os.path.join(diagrams_dir, filename)
        else:
            output_path = os.path.join(output_dir, title)

        # Construct download URL
        download_path = attachment['_links']['download']
        download_url = f"{confluence_url}{download_path}"

        print(f"Downloading {title} ({media_type})...")

        # Use the authenticated session to download
        response = confluence._session.get(download_url, stream=True)
        response.raise_for_status()

        # Save to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(output_path)
        print(f"Saved {title} ({file_size} bytes) to {output_path}")


if __name__ == "__main__":
    # Handle --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("MCP Confluence Attachments Downloader")
        print("\nUsage: python download_attachments.py <page_id> [output_dir]")
        print("\nArguments:")
        print("  page_id     Confluence page ID to download attachments from")
        print("  output_dir  Directory to save files (default: current directory)")
        print("\nEnvironment Variables:")
        print("  CONFLUENCE_URL             Base URL of Confluence instance")
        print("  CONFLUENCE_PERSONAL_TOKEN  Personal Access Token for authentication")
        print("\nExample:")
        print("  python download_attachments.py 1142972070 ./output")
        print("\nDocker Example:")
        print("  docker run --rm -v $(pwd)/output:/output \\")
        print("    -e CONFLUENCE_URL='https://your-confluence.com/' \\")
        print("    -e CONFLUENCE_PERSONAL_TOKEN='your-token' \\")
        print("    mcp-confluence-attachments 1142972070 /output")
        print("\nOutput:")
        print("  - Images are saved to the output directory")
        print("  - Draw.io diagrams are saved to output/diagrams/")
        sys.exit(0)

    # Get configuration from environment variables
    confluence_url = os.getenv("CONFLUENCE_URL", "https://confluence.derivco.co.za/")
    token = os.getenv("CONFLUENCE_PERSONAL_TOKEN")

    if not token:
        print("Error: CONFLUENCE_PERSONAL_TOKEN environment variable not set")
        print("Run with --help for usage information")
        sys.exit(1)

    # Get page ID from command line
    if len(sys.argv) < 2:
        print("Error: Missing required argument <page_id>")
        print("Run with --help for usage information")
        sys.exit(1)

    page_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    # Remove trailing slash from URL if present
    confluence_url = confluence_url.rstrip('/')

    try:
        download_attachments(confluence_url, token, page_id, output_dir)
        print("\nDownload complete!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
