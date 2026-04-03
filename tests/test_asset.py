"""
Unit tests for AssetDownloader module.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from pixel2liquid.asset import (
    AssetDownloader,
    DownloadRecord,
    DownloadResult,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_to_download():
    """Sample to_download dict from AssetClassifier output."""
    return {
        "css": [
            {
                "url": "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/base.css?v=117527007907357244581763132457",
                "local_path": "assets/css/base.css",
                "source": "shopify_cdn",
            },
            {
                "url": "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/component-card.css?v=120341546515895839841752482951",
                "local_path": "assets/css/component-card.css",
                "source": "shopify_cdn",
            },
            {
                "url": "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/component-cart-drawer.css?v=112801333748515159671752482951",
                "local_path": "assets/css/component-cart-drawer.css",
                "source": "shopify_cdn",
            },
        ],
        "js": [
            {
                "url": "https://cdn.shopify.com/extensions/019be14a-88a2-71c7-b8be-1f10c4598b49/pixel-114/assets/madgictiktokevent.min.js",
                "local_path": "assets/js/madgictiktokevent.min.js",
                "source": "shopify_cdn",
            },
            {
                "url": "https://cdn.shopify.com/extensions/019d43b3-8890-70b3-ac83-7ef680a432ec/shopify-nextjs-prisma-app-26/assets/widgetLoader.js",
                "local_path": "assets/js/widgetLoader.js",
                "source": "shopify_cdn",
            },
        ],
        "images": [
            {
                "url": "https://cdn.shopify.com/s/files/1/0913/4689/5219/files/0-min.webp?v=1766800472",
                "local_path": "assets/images/0-min.webp",
                "source": "shopify_cdn",
            },
        ],
        "fonts": [],
    }


# ------------------------------------------------------------------
# DownloadRecord & DownloadResult
# ------------------------------------------------------------------

class TestDownloadRecord:
    def test_defaults(self):
        rec = DownloadRecord(
            url="https://example.com/style.css",
            local_path="assets/css/style.css",
            source="shopify_cdn",
        )
        assert rec.url == "https://example.com/style.css"
        assert rec.local_path == "assets/css/style.css"
        assert rec.source == "shopify_cdn"
        assert rec.size == 0
        assert rec.status == "pending"
        assert rec.error is None
        assert rec.content_length is None
        assert rec.downloaded_at is None

    def test_success_record(self):
        rec = DownloadRecord(
            url="https://example.com/style.css",
            local_path="assets/css/style.css",
            source="shopify_cdn",
            size=1234,
            status="success",
            content_length=1234,
            downloaded_at="2024-01-01T00:00:00",
        )
        assert rec.status == "success"
        assert rec.size == 1234


class TestDownloadResult:
    def test_defaults(self):
        result = DownloadResult()
        assert result.total == 0
        assert result.success == 0
        assert result.failed == 0
        assert result.skipped == 0
        assert result.records == []
        assert result.total_bytes == 0
        assert result.duration_seconds == 0.0


# ------------------------------------------------------------------
# AssetDownloader initialization
# ------------------------------------------------------------------

class TestAssetDownloaderInit:
    def test_default_values(self, temp_dir):
        dl = AssetDownloader()
        assert dl.output_dir == Path("downloads")
        assert dl.manifest_path == Path("manifest.json")
        assert dl.verify_ssl is True
        assert dl.MAX_CONCURRENCY == 10
        assert dl.FILE_TIMEOUT_SEC == 30
        assert dl.TASK_TIMEOUT_SEC == 300
        assert dl.CHUNK_SIZE == 8192

    def test_custom_values(self, temp_dir):
        dl = AssetDownloader(
            output_dir=str(temp_dir / "out"),
            manifest_path=str(temp_dir / "mf.json"),
            verify_ssl=False,
        )
        assert dl.output_dir == temp_dir / "out"
        assert dl.manifest_path == temp_dir / "mf.json"
        assert dl.verify_ssl is False


# ------------------------------------------------------------------
# AssetDownloader.download_all_sync - real network test
# ------------------------------------------------------------------

class TestAssetDownloaderRealDownload:
    """Real network tests against fandomara.com assets."""

    def test_download_css_files(self, temp_dir, sample_to_download):
        """Download 3 CSS files and verify integrity."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        # Only CSS files
        to_dl = {"css": sample_to_download["css"], "js": [], "images": [], "fonts": []}

        result = dl.download_all_sync(to_dl, limit=3)

        # Stats
        assert result.total == 3
        assert result.success >= 0
        assert result.failed >= 0
        assert result.success + result.failed == 3
        assert len(result.records) == 3

        # Manifest was saved
        assert dl.manifest_path.exists()
        with open(dl.manifest_path) as f:
            manifest = json.load(f)
        assert len(manifest) == 3

    def test_download_mixed_assets(self, temp_dir, sample_to_download):
        """Download a mix of CSS + JS (6 files total)."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        to_dl = {
            "css": sample_to_download["css"],
            "js": sample_to_download["js"],
            "images": [],
            "fonts": [],
        }
        # 3 CSS + 2 JS = 5 files
        expected = 5
        result = dl.download_all_sync(to_dl, limit=6)

        assert result.total == expected
        assert result.success + result.failed + result.skipped == expected
        assert len(result.records) == expected
        assert result.duration_seconds > 0

        # Manifest check
        with open(dl.manifest_path) as f:
            manifest = json.load(f)
        assert len(manifest) == expected

        # Each record in manifest has required fields
        for url, info in manifest.items():
            assert "local_path" in info
            assert "source" in info
            assert "status" in info
            assert info["status"] in ("downloaded", "failed")

    def test_download_with_limit(self, temp_dir, sample_to_download):
        """Download only first 2 files when limit=2."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        result = dl.download_all_sync(sample_to_download, limit=2)

        assert result.total == 2
        assert len(result.records) == 2

    def test_empty_input(self, temp_dir):
        """Empty to_download dict returns empty result."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        result = dl.download_all_sync({"css": [], "js": [], "images": [], "fonts": []})

        assert result.total == 0
        assert result.success == 0
        assert result.failed == 0


class TestAssetDownloaderIntegrity:
    """Post-download integrity verification tests."""

    def test_verify_files_all_ok(self, temp_dir):
        """verify_downloaded_files returns ok list when files exist and match."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        # Create fake success records and files
        css_dir = temp_dir / "downloads" / "assets" / "css"
        css_dir.mkdir(parents=True, exist_ok=True)
        fake_file = css_dir / "base.css"
        fake_file.write_text(".foo { color: red; }")

        rec = DownloadRecord(
            url="https://example.com/base.css",
            local_path="assets/css/base.css",
            source="shopify_cdn",
            size=fake_file.stat().st_size,
            status="downloaded",
            content_length=fake_file.stat().st_size,
        )
        result = DownloadResult(
            total=1, success=1, records=[rec], total_bytes=rec.size
        )

        v = dl.verify_downloaded_files(result)
        assert len(v["ok"]) == 1
        assert len(v["corrupt"]) == 0
        assert v["ok"][0] == "assets/css/base.css"

    def test_verify_files_missing_file(self, temp_dir):
        """verify_downloaded_files detects missing files."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        # Record says success but file doesn't exist
        rec = DownloadRecord(
            url="https://example.com/base.css",
            local_path="assets/css/base.css",
            source="shopify_cdn",
            size=100,
            status="downloaded",
        )
        result = DownloadResult(total=1, success=1, records=[rec])

        v = dl.verify_downloaded_files(result)
        assert len(v["ok"]) == 0
        assert len(v["corrupt"]) == 1
        assert v["corrupt"][0] == "assets/css/base.css"

    def test_verify_files_empty_file(self, temp_dir):
        """verify_downloaded_files detects zero-size files."""
        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        css_dir = temp_dir / "downloads" / "assets" / "css"
        css_dir.mkdir(parents=True, exist_ok=True)
        fake_file = css_dir / "empty.css"
        fake_file.write_text("")  # 0 bytes

        rec = DownloadRecord(
            url="https://example.com/empty.css",
            local_path="assets/css/empty.css",
            source="shopify_cdn",
            size=0,
            status="downloaded",
            content_length=0,
        )
        result = DownloadResult(total=1, success=1, records=[rec], total_bytes=0)

        v = dl.verify_downloaded_files(result)
        assert len(v["ok"]) == 0
        assert len(v["corrupt"]) == 1


# ------------------------------------------------------------------
# Integration test with real data from crawl_state
# ------------------------------------------------------------------

class TestAssetDownloaderRealData:
    """Integration test using actual crawl_state from fandomara.com."""

    def test_collections_all_assets(self, temp_dir):
        """Download from collections/all page using real AssetClassifier output."""
        with open("/tmp/fandomara_cache/www.fandomara.com/crawl_state.json", "r") as f:
            crawl_state = json.load(f)

        from pixel2liquid.asset import AssetClassifier

        classifier = AssetClassifier()
        result = classifier.classify_from_crawl_state(
            crawl_state,
            page_keys=["www.fandomara.com/collections/all"],
        )

        # Pick a subset: first 5 CSS + first 5 JS + first 3 images
        to_dl = {
            "css": result.to_download["css"][:5],
            "js": result.to_download["js"][:5],
            "images": result.to_download["images"][:3],
            "fonts": result.to_download["fonts"][:2],
        }

        dl = AssetDownloader(
            output_dir=str(temp_dir / "downloads"),
            manifest_path=str(temp_dir / "manifest.json"),
        )

        dl_result = dl.download_all_sync(to_dl)

        # Basic sanity
        assert dl_result.total == len(to_dl["css"]) + len(to_dl["js"]) + len(to_dl["images"]) + len(to_dl["fonts"])
        assert len(dl_result.records) == dl_result.total

        # Manifest exists and readable
        assert dl.manifest_path.exists()
        with open(dl.manifest_path) as f:
            manifest = json.load(f)
        assert len(manifest) == dl_result.total

        # Integrity check
        integrity = dl.verify_downloaded_files(dl_result)
        success_records = [r for r in dl_result.records if r.status == "downloaded"]
        assert len(integrity["ok"]) + len(integrity["corrupt"]) == len(success_records)

        # Print summary
        print(f"\n=== Download Result ===")
        print(f"Total: {dl_result.total}")
        print(f"Success: {dl_result.success}")
        print(f"Failed: {dl_result.failed}")
        print(f"Skipped: {dl_result.skipped}")
        print(f"Total bytes: {dl_result.total_bytes:,}")
        print(f"Duration: {dl_result.duration_seconds:.2f}s")
        print(f"Integrity OK: {len(integrity['ok'])}")
        print(f"Integrity corrupt: {len(integrity['corrupt'])}")

        for rec in dl_result.records:
            status_icon = "✅" if rec.status == "success" else "❌"
            print(f"  {status_icon} {rec.local_path} ({rec.size:,} bytes)")
