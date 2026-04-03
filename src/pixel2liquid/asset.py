"""
Asset Classifier Module - Classifies and categorizes web assets for local download.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


# Domains that should be downloaded
DOWNLOAD_DOMAINS = {
    "cdn.shopify.com",
    "fonts.shopifycdn.com",
    "assets.gemcommerce.com",
}

# Domains that should be skipped
SKIP_DOMAINS = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
}

# Source labels for downloaded assets
DOMAIN_SOURCE_LABELS = {
    "cdn.shopify.com": "shopify_cdn",
    "fonts.shopifycdn.com": "shopify_cdn",
    "assets.gemcommerce.com": "gemcommerce",
}


@dataclass
class AssetInfo:
    """Single asset information."""
    url: str
    local_path: str
    source: str


@dataclass
class ClassificationResult:
    """Result of asset classification."""
    to_download: dict = field(default_factory=lambda: {
        "css": [],
        "js": [],
        "images": [],
        "fonts": [],
    })
    skip: dict = field(default_factory=lambda: {
        "google_fonts": [],
    })
    summary: dict = field(default_factory=lambda: {
        "total": 0,
        "to_download": 0,
        "to_skip": 0,
    })


def get_asset_type(url: str) -> Optional[str]:
    """Determine asset type from URL extension."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    if path.endswith(".css"):
        return "css"
    elif path.endswith(".js"):
        return "js"
    elif path.endswith((".woff2", ".woff", ".ttf", ".otf", ".eot")):
        return "fonts"
    elif path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".avif", ".avifs")):
        return "images"
    else:
        return None


def get_local_path(url: str, asset_type: str) -> str:
    """Generate local path for an asset URL."""
    parsed = urlparse(url)
    path = parsed.path
    
    # Extract filename from path
    filename = path.split("/")[-1]
    
    if not filename:
        return None
    
    if asset_type == "css":
        return f"assets/css/{filename}"
    elif asset_type == "js":
        return f"assets/js/{filename}"
    elif asset_type == "fonts":
        return f"assets/fonts/{filename}"
    elif asset_type == "images":
        return f"assets/images/{filename}"
    else:
        return None


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


class AssetClassifier:
    """Classifies web assets for local download based on domain rules."""
    
    def __init__(self):
        self.result = ClassificationResult()
    
    def _get_local_dir(self, url: str) -> str:
        """Get local directory path based on source domain and asset type."""
        domain = get_domain(url)
        source = DOMAIN_SOURCE_LABELS.get(domain, "other")
        asset_type = get_asset_type(url) or "other"
        return f"assets/{source}/{asset_type}"
    
    def get_local_path(self, url: str) -> str:
        """
        Generate local path for an asset URL.
        
        Strips query params from URL and extracts filename from base URL.
        Directory structure: assets/{source}/{asset_type}/{filename}
        
        Example:
            URL: https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/product.jpg?v=xxx&width=1066
            Returns: assets/shopify_cdn/images/product.jpg
        """
        # Strip query params - key fix for duplicate file issue
        base_url = url.split('?')[0]
        
        # Extract filename from base URL
        filename = os.path.basename(base_url)
        
        if not filename:
            return None
        
        # Get directory based on source and asset type
        local_dir = self._get_local_dir(url)
        
        return os.path.join(local_dir, filename)
    
    def classify_asset(self, url: str) -> Optional[AssetInfo]:
        """
        Classify a single asset URL.
        
        Returns AssetInfo if asset should be downloaded, None otherwise.
        """
        if not url or not url.startswith("http"):
            return None
        
        domain = get_domain(url)
        asset_type = get_asset_type(url)
        
        if asset_type is None:
            return None
        
        # Check skip domains
        if domain in SKIP_DOMAINS:
            return None
        
        # Check download domains
        if domain in DOWNLOAD_DOMAINS:
            local_path = self.get_local_path(url)
            source = DOMAIN_SOURCE_LABELS.get(domain, "unknown")
            
            return AssetInfo(
                url=url,
                local_path=local_path,
                source=source,
            )
        
        # For other domains, also try to download
        local_path = self.get_local_path(url)
        return AssetInfo(
            url=url,
            local_path=local_path,
            source="other",
        )
    
    def classify_assets(self, asset_links: dict) -> ClassificationResult:
        """
        Classify all assets from a crawl_state asset_links dict.
        
        Args:
            asset_links: dict with keys 'css', 'js', 'images', 'fonts' containing lists of URLs
            
        Returns:
            ClassificationResult with categorized assets
        """
        result = ClassificationResult()
        
        asset_types = ["css", "js", "images", "fonts"]
        
        for asset_type in asset_types:
            urls = asset_links.get(asset_type, [])
            
            for url in urls:
                # Skip data URLs
                if url.startswith("data:"):
                    result.skip.setdefault("google_fonts", []).append(url)
                    result.summary["total"] += 1
                    result.summary["to_skip"] += 1
                    continue
                
                domain = get_domain(url)
                
                # Check skip domains
                if domain in SKIP_DOMAINS:
                    result.skip.setdefault("google_fonts", []).append(url)
                    result.summary["total"] += 1
                    result.summary["to_skip"] += 1
                    continue
                
                # Check download domains
                if domain in DOWNLOAD_DOMAINS:
                    local_path = self.get_local_path(url)
                    source = DOMAIN_SOURCE_LABELS.get(domain, "unknown")
                    
                    asset_info = {
                        "url": url,
                        "local_path": local_path,
                        "source": source,
                    }
                    result.to_download[asset_type].append(asset_info)
                    result.summary["total"] += 1
                    result.summary["to_download"] += 1
                    continue
                
                # Other HTTP URLs - also download
                if url.startswith("http"):
                    local_path = self.get_local_path(url)
                    asset_info = {
                        "url": url,
                        "local_path": local_path,
                        "source": "other",
                    }
                    result.to_download[asset_type].append(asset_info)
                    result.summary["total"] += 1
                    result.summary["to_download"] += 1
        
        return result
    
    def classify_from_crawl_state(self, crawl_state: dict, page_keys: list[str] = None) -> ClassificationResult:
        """
        Classify assets from a full crawl_state dict.
        
        Args:
            crawl_state: Full crawl_state.json dict
            page_keys: Optional list of specific page keys to process. 
                      If None, processes all pages.
        
        Returns:
            ClassificationResult aggregated from all pages
        """
        result = ClassificationResult()
        pages = crawl_state.get("pages", {})
        
        if page_keys is None:
            page_keys = list(pages.keys())
        
        for page_key in page_keys:
            page = pages.get(page_key)
            if not page:
                continue
            
            asset_links = page.get("asset_links", {})
            page_result = self.classify_assets(asset_links)
            
            # Merge into result
            result.summary["total"] += page_result.summary["total"]
            result.summary["to_download"] += page_result.summary["to_download"]
            result.summary["to_skip"] += page_result.summary["to_skip"]
            
            for asset_type in ["css", "js", "images", "fonts"]:
                result.to_download[asset_type].extend(
                    page_result.to_download.get(asset_type, [])
                )
            
            for skip_type, items in page_result.skip.items():
                result.skip.setdefault(skip_type, []).extend(items)
        
        return result


# =============================================================================
# AssetDownloader - Async concurrent asset downloader
# =============================================================================

import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class DownloadRecord:
    url: str
    local_path: str
    source: str
    size: int = 0
    status: str = "pending"
    error: Optional[str] = None
    content_length: Optional[int] = None
    downloaded_at: Optional[str] = None


@dataclass
class DownloadResult:
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    records: list = field(default_factory=list)
    total_bytes: int = 0
    duration_seconds: float = 0.0


class AssetDownloader:
    MAX_CONCURRENCY = 10
    FILE_TIMEOUT_SEC = 30
    TASK_TIMEOUT_SEC = 300
    CHUNK_SIZE = 8192
    # Batch download settings
    BATCH_SIZE = 50
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    def __init__(
        self,
        output_dir: str = "downloads",
        manifest_path: str = "manifest.json",
        verify_ssl: bool = True,
        batch_size: int = 50,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.output_dir: Path = Path(output_dir)
        self.manifest_path: Path = Path(manifest_path)
        self.verify_ssl: bool = verify_ssl
        self.batch_size: int = batch_size
        self.max_retries: int = max_retries
        self.retry_delay: int = retry_delay
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._started_at: Optional[datetime] = None
        self._downloaded_urls: set = set()

    def _is_already_downloaded(self, url: str, local_path: str) -> bool:
        """Check if file already exists and is valid (incremental download)."""
        abs_path = self.output_dir / local_path
        if not abs_path.exists():
            return False
        # Check file is not empty
        if abs_path.stat().st_size == 0:
            return False
        return True

    async def download_all(
        self,
        to_download: dict,
        limit: Optional[int] = None,
        incremental: bool = True,
    ) -> DownloadResult:
        # Build flat task list
        tasks = []
        for asset_type in ["css", "js", "images", "fonts"]:
            for item in to_download.get(asset_type, []):
                tasks.append((asset_type, item))

        if limit:
            tasks = tasks[:limit]

        if not tasks:
            return DownloadResult()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        result = DownloadResult(total=len(tasks))
        self._started_at = datetime.now()

        connector = aiohttp.TCPConnector(
            limit=self.MAX_CONCURRENCY,
            ssl=False if not self.verify_ssl else None,
        )
        timeout_cfg = aiohttp.ClientTimeout(total=self.FILE_TIMEOUT_SEC)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_cfg,
        )
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)

        try:
            # Process in batches
            for batch_start in range(0, len(tasks), self.batch_size):
                batch = tasks[batch_start:batch_start + self.batch_size]
                batch_num = batch_start // self.batch_size + 1
                total_batches = (len(tasks) + self.batch_size - 1) // self.batch_size
                print(f"\n  [Batch {batch_num}/{total_batches}] Processing {len(batch)} items...")

                batch_records = await self._download_batch(batch, result, incremental)

                # Force garbage collection after each batch
                import gc
                gc.collect()

                print(f"  [Batch {batch_num}/{total_batches}] Done. "
                      f"Success: {sum(1 for r in batch_records if r.status == 'success')}, "
                      f"Failed: {sum(1 for r in batch_records if r.status == 'failed')}, "
                      f"Skipped: {sum(1 for r in batch_records if r.status == 'skipped')}")
        except Exception:
            pass
        finally:
            await self._session.close()
            self._session = None

        if self._started_at:
            result.duration_seconds = (datetime.now() - self._started_at).total_seconds()

        await self._save_manifest(result)
        return result

    async def _download_batch(
        self,
        tasks: list,
        result: DownloadResult,
        incremental: bool,
    ) -> list:
        """Download a batch of assets concurrently."""
        async def download_one(asset_type: str, item: dict) -> DownloadRecord:
            return await self._download_file(asset_type, item, incremental)

        coros = [download_one(at, item) for at, item in tasks]
        records = await asyncio.wait_for(
            asyncio.gather(*coros, return_exceptions=True),
            timeout=self.TASK_TIMEOUT_SEC,
        )

        batch_records = []
        for rec_or_exc in records:
            if isinstance(rec_or_exc, Exception):
                rec = DownloadRecord(
                    url="<unknown>",
                    local_path="<unknown>",
                    source="unknown",
                    status="failed",
                    error=str(rec_or_exc),
                )
                result.failed += 1
                result.records.append(rec)
                batch_records.append(rec)
            elif isinstance(rec_or_exc, DownloadRecord):
                result.records.append(rec_or_exc)
                batch_records.append(rec_or_exc)
                if rec_or_exc.status == "downloaded":
                    result.success += 1
                    result.total_bytes += rec_or_exc.size
                elif rec_or_exc.status == "failed":
                    result.failed += 1
                elif rec_or_exc.status == "skipped":
                    result.skipped += 1

        return batch_records

    def download_all_sync(
        self,
        to_download: dict,
        limit: Optional[int] = None,
    ) -> DownloadResult:
        return asyncio.run(self.download_all(to_download, limit=limit))

    async def _download_file(
        self,
        asset_type: str,
        item: dict,
        incremental: bool = True,
    ) -> DownloadRecord:
        url = item["url"]
        local_path = item["local_path"]
        source = item["source"]

        record = DownloadRecord(
            url=url,
            local_path=local_path,
            source=source,
            status="pending",
        )

        # Incremental: skip if already downloaded
        if incremental and self._is_already_downloaded(url, local_path):
            record.status = "skipped"
            record.downloaded_at = datetime.now().isoformat()
            abs_path = self.output_dir / local_path
            record.size = abs_path.stat().st_size
            return record

        async with self._semaphore:
            try:
                record = await self.download_with_retry(record)
            except asyncio.TimeoutError:
                record.status = "failed"
                record.error = "Timeout"
            except Exception as exc:
                record.status = "failed"
                record.error = str(exc)

        return record

    async def download_with_retry(self, record: DownloadRecord) -> DownloadRecord:
        """Download a single file with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                return await self._do_download(record)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"    [Retry {attempt + 1}/{self.max_retries}] "
                          f"Failed to download {record.url}: {e}. "
                          f"Waiting {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    record.status = "failed"
                    record.error = f"Failed after {self.max_retries} attempts: {e}"
                    raise

    async def _do_download(self, record: DownloadRecord) -> DownloadRecord:
        url = record.url
        local_path = record.local_path
        abs_path = self.output_dir / local_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        content_length = None
        actual_size = 0

        async with self._session.get(url) as resp:
            if resp.status != 200:
                record.status = "failed"
                record.error = f"HTTP {resp.status}"
                return record

            content_length = resp.content_length
            record.content_length = content_length

            with open(abs_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
                    f.write(chunk)
                    actual_size += len(chunk)

        record.size = actual_size

        # 智能验证下载结果
        is_valid, msg = self._validate_download(content_length, actual_size, abs_path)
        if not is_valid:
            record.status = "failed"
            record.error = msg
            abs_path.unlink(missing_ok=True)
            return record

        # Check: file must contain valid content (not HTML error page)
        if not self._is_valid_content(record.url, abs_path):
            record.status = "failed"
            record.error = "Invalid content (likely HTML error page)"
            abs_path.unlink(missing_ok=True)
            return record

        record.status = "downloaded"
        record.downloaded_at = datetime.now().isoformat()
        return record

    def _is_valid_content(self, url: str, abs_path: Path) -> bool:
        """Check if downloaded file contains valid content, not an HTML error page.
        
        Returns True if the file appears to be a valid resource (JS/CSS/image),
        False if it appears to be an HTML error page.
        """
        try:
            with open(abs_path, "rb") as f:
                header = f.read(256)
            
            if not header:
                return False
            
            # Check for HTML doctype or html tag (common error page signatures)
            if b"<!DOCTYPE" in header or b"<html" in header or b"<HTML" in header:
                return False
            
            # Check for common HTML error patterns
            lower_header = header.lower()
            if b"<head>" in lower_header or b"<title>" in lower_header:
                return False
            if b"charset=" in lower_header and b"text/html" in lower_header:
                return False
            
            return True
        except Exception:
            # If we can't read the file, assume it's valid (other checks will catch issues)
            return True

    def _validate_download(self, content_length, actual_size, abs_path):
        """智能验证下载结果。

        Args:
            content_length: Content-Length header value (may be None)
            actual_size: Actual downloaded file size in bytes
            abs_path: Path to downloaded file

        Returns:
            (is_valid: bool, message: str)
        """
        # Case 1: 完全匹配 - OK
        if content_length and actual_size == content_length:
            return True, "OK"

        # Case 2: actual > content 且比例符合压缩特征 - OK (gzip解压)
        if content_length and actual_size > content_length:
            ratio = actual_size / content_length
            if 1.5 < ratio < 5:  # gzip 压缩比通常在 2-3x
                return True, f"OK (gzip解压后: {actual_size} vs {content_length})"
            # actual > content 但比例异常
            return False, f"异常大小: got {actual_size}, expected {content_length} (ratio={ratio:.1f})"

        # Case 3: actual < content - 真正截断
        if content_length and actual_size < content_length:
            return False, f"截断: got {actual_size}, expected {content_length}"

        # Case 4: 空文件
        if actual_size == 0:
            return False, "空文件"

        # Case 5: 无 content-length，只验证非空
        return True, "OK (无长度校验)"

    async def _save_manifest(self, result: DownloadResult) -> None:
        manifest = {}
        for rec in result.records:
            manifest[rec.url] = {
                "local_path": rec.local_path,
                "source": rec.source,
                "size": rec.size,
                "status": rec.status,
                "error": rec.error,
                "content_length": rec.content_length,
                "downloaded_at": rec.downloaded_at,
            }

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def verify_downloaded_files(self, result: DownloadResult) -> dict:
        """Verify downloaded files are valid (not empty, not HTML error pages).
        
        Note: Does NOT check Content-Length because CDN compression causes
        decompressed size to differ from Content-Length header.
        """
        ok = []
        corrupt = []
        for rec in result.records:
            if rec.status != "downloaded":
                continue
            abs_path = self.output_dir / rec.local_path
            if not abs_path.exists():
                corrupt.append(rec.local_path)
                continue
            size = abs_path.stat().st_size
            if size == 0:
                corrupt.append(rec.local_path)
                continue
            # Check for HTML content (error pages)
            try:
                with open(abs_path, "rb") as f:
                    header = f.read(256)
                if b"<!DOCTYPE" in header or b"<html" in header or b"<HTML" in header:
                    corrupt.append(rec.local_path)
                    continue
            except Exception:
                pass  # If we can't read, skip this check
            ok.append(rec.local_path)
        return {"ok": ok, "corrupt": corrupt}
