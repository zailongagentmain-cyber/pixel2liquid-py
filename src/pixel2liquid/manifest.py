"""
ManifestManager Module - Maintains resource manifest for pixel2liquid.

Handles:
- Saving/loading manifest JSON (URL → local path mapping)
- Incremental updates (resume interrupted downloads)
- Recording asset source classification
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_MANIFEST_PATH = "manifest.json"


class ManifestManager:
    """Manages resource manifest for local asset storage."""
    
    def __init__(self, manifest_path: str = DEFAULT_MANIFEST_PATH):
        self.manifest_path = Path(manifest_path)
        self._lock = threading.Lock()
        self._data: Optional[dict] = None
    
    def _ensure_loaded(self) -> dict:
        """Ensure manifest is loaded into memory."""
        if self._data is None:
            self._data = self.load()
        return self._data
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    
    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        from urllib.parse import urlparse
        path = urlparse(url).path
        return path.split("/")[-1] if path else ""
    
    def _get_default_manifest(self) -> dict:
        """Create a new empty manifest structure."""
        return {
            "version": "1.0",
            "site": "",
            "assets": {},
            "pages": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    
    def save(self, manifest_data: dict) -> None:
        """Save manifest to JSON file.
        
        Args:
            manifest_data: Complete manifest dict to save
        """
        manifest_data["updated_at"] = datetime.now().isoformat()
        with self._lock:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, ensure_ascii=False, indent=2)
            self._data = manifest_data.copy()
    
    def load(self) -> dict:
        """Load manifest from JSON file.
        
        Returns:
            Manifest dict, or empty manifest if file doesn't exist.
        """
        if not self.manifest_path.exists():
            return self._get_default_manifest()
        
        with self._lock:
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._data = data
                return data
            except (json.JSONDecodeError, IOError):
                return self._get_default_manifest()
    
    def initialize(self, site: str) -> dict:
        """Initialize a new manifest for a site.
        
        Args:
            site: Website domain (e.g., 'www.fandomara.com')
            
        Returns:
            Initialized manifest dict
        """
        manifest = self._get_default_manifest()
        manifest["site"] = site
        self.save(manifest)
        return manifest
    
    def update_asset(self, source: str, filename: str, data: dict) -> None:
        """Update status of a single asset.
        
        Args:
            source: Asset source domain (e.g., 'cdn.shopify.com')
            filename: Asset filename (e.g., 'base.css')
            data: Asset data dict with keys: url, local_path, size, status, etc.
        """
        manifest = self._ensure_loaded()
        
        if source not in manifest["assets"]:
            manifest["assets"][source] = {
                "type": data.get("source_type", "unknown"),
                "local_dir": data.get("local_dir", ""),
                "skip": data.get("skip", False),
                "files": {},
            }
        
        asset_source = manifest["assets"][source]
        
        # Update type info if provided
        if "source_type" in data:
            asset_source["type"] = data["source_type"]
        if "local_dir" in data:
            asset_source["local_dir"] = data["local_dir"]
        if "skip" in data:
            asset_source["skip"] = data["skip"]
        
        # Update file entry
        if "files" not in asset_source:
            asset_source["files"] = {}
        
        existing = asset_source["files"].get(filename, {})
        existing.update(data)
        asset_source["files"][filename] = existing
        
        self.save(manifest)
    
    def add_asset(
        self,
        url: str,
        local_path: str,
        source_type: str,
        local_dir: str = "",
        size: int = 0,
        status: str = "pending",
    ) -> None:
        """Add a new asset to the manifest.
        
        Args:
            url: Full asset URL
            local_path: Local file path
            source_type: Source type (e.g., 'shopify_cdn', 'google_fonts')
            local_dir: Local directory for this source
            size: File size in bytes
            status: Initial status ('pending', 'downloading', 'downloaded', 'failed')
        """
        domain = self._extract_domain(url)
        filename = self._extract_filename(url)
        
        data = {
            "url": url,
            "local_path": local_path,
            "size": size,
            "status": status,
            "source_type": source_type,
            "local_dir": local_dir,
            "downloaded_at": datetime.now().isoformat() if status == "downloaded" else None,
        }
        
        self.update_asset(domain, filename, data)
    
    def mark_downloaded(self, url: str, local_path: str, size: int) -> None:
        """Mark an asset as successfully downloaded.
        
        Args:
            url: Asset URL that was downloaded
            local_path: Local file path where saved
            size: Actual file size in bytes
        """
        domain = self._extract_domain(url)
        filename = self._extract_filename(url)
        
        data = {
            "url": url,
            "local_path": local_path,
            "size": size,
            "status": "downloaded",
            "downloaded_at": datetime.now().isoformat(),
        }
        
        self.update_asset(domain, filename, data)
    
    def mark_failed(self, url: str, error: str) -> None:
        """Mark an asset download as failed.
        
        Args:
            url: Asset URL that failed
            error: Error message
        """
        domain = self._extract_domain(url)
        filename = self._extract_filename(url)
        
        manifest = self._ensure_loaded()
        if domain in manifest["assets"] and filename in manifest["assets"][domain].get("files", {}):
            file_entry = manifest["assets"][domain]["files"][filename]
            file_entry["status"] = "failed"
            file_entry["error"] = error
            self.save(manifest)
    
    def mark_skip(self, source: str, source_type: str, reason: str = "") -> None:
        """Mark an entire source domain as skipped.
        
        Args:
            source: Source domain (e.g., 'fonts.googleapis.com')
            source_type: Type label (e.g., 'google_fonts')
            reason: Skip reason
        """
        manifest = self._ensure_loaded()
        
        manifest["assets"][source] = {
            "type": source_type,
            "skip": True,
            "skip_reason": reason,
            "local_dir": "",
            "files": {},
        }
        
        self.save(manifest)
    
    def add_page(self, url: str, html_path: str, assets_used: list[str]) -> None:
        """Add a page to the manifest.
        
        Args:
            url: Full page URL
            html_path: Local HTML file path
            assets_used: List of asset filenames used by this page
        """
        manifest = self._ensure_loaded()
        
        manifest["pages"][url] = {
            "html_path": html_path,
            "assets_used": assets_used,
            "localized": False,
            "added_at": datetime.now().isoformat(),
        }
        
        self.save(manifest)
    
    def update_page(self, url: str, data: dict) -> None:
        """Update page data in manifest.
        
        Args:
            url: Page URL
            data: Dict with fields to update
        """
        manifest = self._ensure_loaded()
        
        if url in manifest["pages"]:
            manifest["pages"][url].update(data)
        else:
            manifest["pages"][url] = data
        
        self.save(manifest)
    
    def get_pending_assets(self) -> list[dict]:
        """Get all assets with 'pending' status for resume/interrupt handling.
        
        Returns:
            List of asset dicts with pending status
        """
        manifest = self._ensure_loaded()
        pending = []
        
        for source, source_data in manifest["assets"].items():
            if source_data.get("skip"):
                continue
            
            for filename, file_data in source_data.get("files", {}).items():
                if file_data.get("status") == "pending":
                    pending.append({
                        "source": source,
                        "filename": filename,
                        "url": file_data.get("url"),
                        "local_path": file_data.get("local_path"),
                        "size": file_data.get("size", 0),
                    })
        
        return pending
    
    def get_downloading_assets(self) -> list[dict]:
        """Get all assets currently being downloaded.
        
        Returns:
            List of asset dicts with 'downloading' status
        """
        manifest = self._ensure_loaded()
        downloading = []
        
        for source, source_data in manifest["assets"].items():
            if source_data.get("skip"):
                continue
            
            for filename, file_data in source_data.get("files", {}).items():
                if file_data.get("status") == "downloading":
                    downloading.append({
                        "source": source,
                        "filename": filename,
                        "url": file_data.get("url"),
                        "local_path": file_data.get("local_path"),
                    })
        
        return downloading
    
    def get_stats(self) -> dict:
        """Get download statistics.
        
        Returns:
            Dict with counts and sizes for each status
        """
        manifest = self._ensure_loaded()
        
        stats = {
            "total_assets": 0,
            "by_status": {
                "pending": 0,
                "downloading": 0,
                "downloaded": 0,
                "failed": 0,
            },
            "by_source": {},
            "skipped_sources": [],
            "total_size_bytes": 0,
            "downloaded_size_bytes": 0,
            "total_pages": len(manifest["pages"]),
        }
        
        for source, source_data in manifest["assets"].items():
            source_type = source_data.get("type", "unknown")
            
            if source_data.get("skip"):
                stats["skipped_sources"].append(source)
                continue
            
            stats["by_source"][source] = {
                "type": source_type,
                "total": 0,
                "downloaded": 0,
            }
            
            for filename, file_data in source_data.get("files", {}).items():
                stats["total_assets"] += 1
                status = file_data.get("status", "unknown")
                
                if status in stats["by_status"]:
                    stats["by_status"][status] += 1
                
                size = file_data.get("size", 0)
                stats["total_size_bytes"] += size
                
                if status == "downloaded":
                    stats["downloaded_size_bytes"] += size
                    stats["by_source"][source]["downloaded"] += 1
                
                stats["by_source"][source]["total"] += 1
        
        return stats
    
    def get_asset_by_url(self, url: str) -> Optional[dict]:
        """Get asset entry by URL.
        
        Args:
            url: Asset URL
            
        Returns:
            Asset dict or None if not found
        """
        manifest = self._ensure_loaded()
        domain = self._extract_domain(url)
        filename = self._extract_filename(url)
        
        if domain not in manifest["assets"]:
            return None
        
        source_data = manifest["assets"][domain]
        if filename not in source_data.get("files", {}):
            return None
        
        return source_data["files"][filename]
    
    def reset(self) -> None:
        """Reset manifest to empty state."""
        self._data = None
        if self.manifest_path.exists():
            self.manifest_path.unlink()

    def sync_with_filesystem(self, assets_dir: str) -> dict:
        """
        Scan assets directory and update manifest status to match actual files.
        
        This reconciles the manifest with reality:
        - Files that exist but are marked 'skipped' → update to 'downloaded'
        - Files marked 'downloaded' but missing → keep status, mark as orphaned
        - Files in manifest that don't exist on disk → orphaned records
        - Files on disk but not in manifest → untracked files
        
        Args:
            assets_dir: Path to assets directory to scan
            
        Returns:
            Sync report dict with:
            - confirmed_downloaded: entries correctly marked as downloaded
            - needs_status_update: skipped entries that now have files
            - orphaned_records: entries whose files are missing
            - untracked_files: files on disk not in manifest
            - updated_manifest: whether manifest was modified
        """
        manifest = self._ensure_loaded()
        assets_path = Path(assets_dir)
        
        # Build URL→local_path lookup for URL-keyed manifest
        # The manifest keys ARE URLs, values have local_path
        url_to_local_path = {}
        local_path_to_url = {}
        for url, data in manifest.items():
            if isinstance(data, dict) and "local_path" in data:
                local_path = data["local_path"]
                url_to_local_path[url] = local_path
                local_path_to_url[local_path] = url
        
        # Scan actual files on disk
        disk_files = set()
        for f in assets_path.rglob("*"):
            if f.is_file():
                rel_path = str(f.relative_to(assets_path))
                disk_files.add(rel_path)
        
        # Initialize report
        report = {
            "confirmed_downloaded": 0,
            "needs_status_update": 0,
            "orphaned_records": 0,
            "untracked_files": 0,
            "untracked_file_list": [],
            "updated_manifest": False,
        }
        
        # Check each manifest entry
        for url, data in list(manifest.items()):
            if not isinstance(data, dict):
                continue
            
            local_path = data.get("local_path", "")
            status = data.get("status", "unknown")
            file_exists = (assets_path / local_path).exists() if local_path else False
            
            if status == "downloaded":
                if file_exists:
                    report["confirmed_downloaded"] += 1
                else:
                    # File was marked downloaded but doesn't exist
                    report["orphaned_records"] += 1
            
            elif status == "skipped":
                if file_exists:
                    # File exists but marked as skipped - update to downloaded
                    data["status"] = "downloaded"
                    data["downloaded_at"] = datetime.now().isoformat()
                    report["needs_status_update"] += 1
                    report["updated_manifest"] = True
                else:
                    # Skipped and file doesn't exist
                    report["orphaned_records"] += 1
            
            elif status == "failed":
                # Check if file now exists
                if file_exists:
                    data["status"] = "downloaded"
                    data["downloaded_at"] = datetime.now().isoformat()
                    report["needs_status_update"] += 1
                    report["updated_manifest"] = True
                else:
                    report["orphaned_records"] += 1
        
        # Find untracked files (on disk but not in manifest)
        manifest_local_paths = set(local_path_to_url.keys())
        untracked = disk_files - manifest_local_paths
        report["untracked_files"] = len(untracked)
        report["untracked_file_list"] = sorted(list(untracked))[:50]  # Limit to 50 for readability
        
        # Save if updated
        if report["updated_manifest"]:
            self.save(manifest)
        
        return report
