"""Confluence API client wrapper for attachment operations."""

import os
from typing import List, Dict, Optional
from atlassian import Confluence


class ConfluenceAttachmentClient:
    """Client for Confluence attachment operations."""

    def __init__(self, url: str, token: str):
        """Initialize Confluence client.

        Args:
            url: Base URL of Confluence instance
            token: Personal access token
        """
        self.confluence = Confluence(url=url, token=token)
        self.base_url = url.rstrip('/')

    def list_attachments(self, page_id: str) -> List[Dict]:
        """List all attachments for a page.

        Args:
            page_id: Confluence page ID

        Returns:
            List of attachment dictionaries with metadata
        """
        attachments_response = self.confluence.get_attachments_from_content(page_id)

        if not attachments_response or 'results' not in attachments_response:
            return []

        attachments = []
        for att in attachments_response['results']:
            # Skip temporary/draft files
            media_type = att.get('metadata', {}).get('mediaType', '')
            title = att['title']

            if 'draft' in media_type.lower() or title.startswith('~'):
                continue

            attachments.append({
                'id': att['id'],
                'title': title,
                'mediaType': media_type,
                'fileSize': att.get('extensions', {}).get('fileSize', 0),
                'downloadUrl': f"{self.base_url}{att['_links']['download']}",
                'isImage': media_type.startswith('image/'),
                'isDiagram': media_type == 'application/vnd.jgraph.mxfile',
            })

        return attachments

    def get_attachment_metadata(self, page_id: str, attachment_id: str) -> Optional[Dict]:
        """Get metadata for a specific attachment.

        Args:
            page_id: Confluence page ID
            attachment_id: Attachment ID

        Returns:
            Attachment metadata dictionary or None if not found
        """
        attachments = self.list_attachments(page_id)
        for att in attachments:
            if att['id'] == attachment_id:
                return att
        return None

    def download_attachment(self, attachment_id: str, download_url: str,
                          output_path: str) -> Dict:
        """Download a single attachment.

        Args:
            attachment_id: Attachment ID
            download_url: Full download URL
            output_path: Local file path to save to

        Returns:
            Dict with download status and details
        """
        response = self.confluence._session.get(download_url, stream=True)
        response.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(output_path)

        return {
            'attachment_id': attachment_id,
            'output_path': output_path,
            'file_size': file_size,
            'status': 'success'
        }

    def download_attachments(self, page_id: str, output_dir: str,
                           download_images: bool = True,
                           download_diagrams: bool = True) -> List[Dict]:
        """Download attachments from a page with filtering.

        Args:
            page_id: Confluence page ID
            output_dir: Directory to save attachments
            download_images: Whether to download image files
            download_diagrams: Whether to download draw.io diagrams

        Returns:
            List of download results
        """
        attachments = self.list_attachments(page_id)

        if not attachments:
            return []

        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        diagrams_dir = os.path.join(output_dir, "diagrams")
        if download_diagrams:
            os.makedirs(diagrams_dir, exist_ok=True)

        results = []
        for att in attachments:
            # Apply filters
            if att['isImage'] and not download_images:
                results.append({
                    'attachment_id': att['id'],
                    'title': att['title'],
                    'status': 'skipped',
                    'reason': 'images filtered out'
                })
                continue

            if att['isDiagram'] and not download_diagrams:
                results.append({
                    'attachment_id': att['id'],
                    'title': att['title'],
                    'status': 'skipped',
                    'reason': 'diagrams filtered out'
                })
                continue

            if not att['isImage'] and not att['isDiagram']:
                results.append({
                    'attachment_id': att['id'],
                    'title': att['title'],
                    'status': 'skipped',
                    'reason': 'not an image or diagram'
                })
                continue

            # Determine output path
            if att['isDiagram']:
                filename = att['title'] if att['title'].endswith('.drawio') else f"{att['title']}.drawio"
                output_path = os.path.join(diagrams_dir, filename)
            else:
                output_path = os.path.join(output_dir, att['title'])

            try:
                result = self.download_attachment(
                    att['id'],
                    att['downloadUrl'],
                    output_path
                )
                result['title'] = att['title']
                results.append(result)
            except Exception as e:
                results.append({
                    'attachment_id': att['id'],
                    'title': att['title'],
                    'status': 'error',
                    'error': str(e)
                })

        return results
