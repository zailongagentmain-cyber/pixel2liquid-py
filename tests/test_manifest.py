"""
Tests for ManifestManager module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

# Import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pixel2liquid.manifest import ManifestManager


@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def manifest_manager(temp_manifest):
    """Create a ManifestManager with temporary file."""
    return ManifestManager(manifest_path=temp_manifest)


class TestManifestCreation:
    """Test empty manifest creation."""
    
    def test_initialize_new_manifest(self, manifest_manager):
        """Test initializing a new manifest for a site."""
        manifest = manifest_manager.initialize("www.fandomara.com")
        
        assert manifest["version"] == "1.0"
        assert manifest["site"] == "www.fandomara.com"
        assert manifest["assets"] == {}
        assert manifest["pages"] == {}
        assert "created_at" in manifest
        assert "updated_at" in manifest
    
    def test_empty_manifest_structure(self, manifest_manager):
        """Test that load returns empty structure for non-existent file."""
        # Create fresh manager with non-existent path
        mgr = ManifestManager(manifest_path="/tmp/nonexistent_manifest_12345.json")
        manifest = mgr.load()
        
        assert manifest["version"] == "1.0"
        assert manifest["assets"] == {}
        assert manifest["pages"] == {}


class TestSaveAndLoad:
    """Test save and load functionality."""
    
    def test_save_and_load_basic(self, manifest_manager):
        """Test basic save and load cycle."""
        test_data = {
            "version": "1.0",
            "site": "www.test.com",
            "assets": {
                "cdn.test.com": {
                    "type": "test_cdn",
                    "local_dir": "assets/test",
                    "files": {
                        "style.css": {
                            "url": "https://cdn.test.com/style.css",
                            "local_path": "assets/test/style.css",
                            "status": "pending",
                        }
                    }
                }
            },
            "pages": {}
        }
        
        manifest_manager.save(test_data)
        
        # Load in new manager
        new_manager = ManifestManager(manifest_path=manifest_manager.manifest_path)
        loaded = new_manager.load()
        
        assert loaded["site"] == "www.test.com"
        assert "cdn.test.com" in loaded["assets"]
        assert loaded["assets"]["cdn.test.com"]["files"]["style.css"]["url"] == "https://cdn.test.com/style.css"
    
    def test_load_existing_file(self, manifest_manager):
        """Test loading an existing manifest file."""
        manifest_manager.initialize("www.existing.com")
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            local_dir="assets/shopify",
        )
        
        # Load in new manager
        new_manager = ManifestManager(manifest_path=manifest_manager.manifest_path)
        loaded = new_manager.load()
        
        assert loaded["site"] == "www.existing.com"
        assert "cdn.shopify.com" in loaded["assets"]
        assert "base.css" in loaded["assets"]["cdn.shopify.com"]["files"]


class TestUpdateAsset:
    """Test updating asset status."""
    
    def test_update_asset_basic(self, manifest_manager):
        """Test basic asset update."""
        manifest_manager.initialize("www.test.com")
        manifest_manager.update_asset(
            source="cdn.shopify.com",
            filename="base.css",
            data={
                "url": "https://cdn.shopify.com/s/files/1/2/3/base.css",
                "local_path": "assets/shopify/base.css",
                "source_type": "shopify_cdn",
                "local_dir": "assets/shopify",
                "status": "pending",
                "size": 12345,
            }
        )
        
        manifest = manifest_manager.load()
        assert "cdn.shopify.com" in manifest["assets"]
        assert "base.css" in manifest["assets"]["cdn.shopify.com"]["files"]
        
        file_entry = manifest["assets"]["cdn.shopify.com"]["files"]["base.css"]
        assert file_entry["url"] == "https://cdn.shopify.com/s/files/1/2/3/base.css"
        assert file_entry["status"] == "pending"
        assert file_entry["size"] == 12345
    
    def test_add_asset_via_helper(self, manifest_manager):
        """Test adding asset using helper method."""
        manifest_manager.initialize("www.test.com")
        manifest_manager.add_asset(
            url="https://fonts.shopifycdn.com/fonts/inter.woff2",
            local_path="assets/fonts/inter.woff2",
            source_type="shopify_cdn",
            local_dir="assets/fonts",
            size=45678,
            status="pending",
        )
        
        manifest = manifest_manager.load()
        assert "fonts.shopifycdn.com" in manifest["assets"]
        assert "inter.woff2" in manifest["assets"]["fonts.shopifycdn.com"]["files"]


class TestMarkDownloaded:
    """Test marking assets as downloaded."""
    
    def test_mark_downloaded(self, manifest_manager):
        """Test marking an asset as downloaded."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            local_dir="assets/shopify",
            status="pending",
        )
        
        # Mark as downloaded
        manifest_manager.mark_downloaded(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            size=12345,
        )
        
        manifest = manifest_manager.load()
        file_entry = manifest["assets"]["cdn.shopify.com"]["files"]["base.css"]
        assert file_entry["status"] == "downloaded"
        assert file_entry["size"] == 12345
        assert file_entry["downloaded_at"] is not None


class TestMarkFailed:
    """Test marking assets as failed."""
    
    def test_mark_failed(self, manifest_manager):
        """Test marking an asset as failed."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/missing.css",
            local_path="assets/shopify/missing.css",
            source_type="shopify_cdn",
            local_dir="assets/shopify",
            status="pending",
        )
        
        # Mark as failed
        manifest_manager.mark_failed(
            url="https://cdn.shopify.com/css/missing.css",
            error="HTTP 404 - Not Found",
        )
        
        manifest = manifest_manager.load()
        file_entry = manifest["assets"]["cdn.shopify.com"]["files"]["missing.css"]
        assert file_entry["status"] == "failed"
        assert file_entry["error"] == "HTTP 404 - Not Found"


class TestMarkSkip:
    """Test marking sources as skipped."""
    
    def test_mark_skip_google_fonts(self, manifest_manager):
        """Test marking Google Fonts as skipped."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.mark_skip(
            source="fonts.googleapis.com",
            source_type="google_fonts",
            reason="License restrictions",
        )
        
        manifest = manifest_manager.load()
        assert "fonts.googleapis.com" in manifest["assets"]
        assert manifest["assets"]["fonts.googleapis.com"]["skip"] is True
        assert manifest["assets"]["fonts.googleapis.com"]["type"] == "google_fonts"


class TestGetPendingAssets:
    """Test getting pending assets for resume."""
    
    def test_get_pending_assets(self, manifest_manager):
        """Test retrieving all pending assets."""
        manifest_manager.initialize("www.fandomara.com")
        
        # Add several assets
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            status="pending",
        )
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/theme.css",
            local_path="assets/shopify/theme.css",
            source_type="shopify_cdn",
            status="pending",
        )
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/js/app.js",
            local_path="assets/shopify/app.js",
            source_type="shopify_cdn",
            status="downloaded",  # Already downloaded
        )
        
        pending = manifest_manager.get_pending_assets()
        
        assert len(pending) == 2
        pending_urls = [p["url"] for p in pending]
        assert "https://cdn.shopify.com/css/base.css" in pending_urls
        assert "https://cdn.shopify.com/css/theme.css" in pending_urls
        assert "https://cdn.shopify.com/js/app.js" not in pending_urls
    
    def test_pending_excludes_skipped(self, manifest_manager):
        """Test that skipped sources are excluded from pending."""
        manifest_manager.initialize("www.fandomara.com")
        
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            status="pending",
        )
        manifest_manager.mark_skip("fonts.googleapis.com", "google_fonts")
        
        pending = manifest_manager.get_pending_assets()
        
        # Should only have the shopify asset
        assert len(pending) == 1
        assert pending[0]["source"] == "cdn.shopify.com"


class TestGetStats:
    """Test getting statistics."""
    
    def test_get_stats_empty(self, manifest_manager):
        """Test stats on empty manifest."""
        manifest_manager.initialize("www.fandomara.com")
        stats = manifest_manager.get_stats()
        
        assert stats["total_assets"] == 0
        assert stats["by_status"]["pending"] == 0
        assert stats["total_pages"] == 0
    
    def test_get_stats_with_assets(self, manifest_manager):
        """Test stats with various assets."""
        manifest_manager.initialize("www.fandomara.com")
        
        # Add assets with different statuses
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            size=1000,
            status="downloaded",
        )
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/theme.css",
            local_path="assets/shopify/theme.css",
            source_type="shopify_cdn",
            size=2000,
            status="pending",
        )
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/js/app.js",
            local_path="assets/shopify/app.js",
            source_type="shopify_cdn",
            status="failed",
        )
        
        stats = manifest_manager.get_stats()
        
        assert stats["total_assets"] == 3
        assert stats["by_status"]["downloaded"] == 1
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["failed"] == 1
        assert stats["downloaded_size_bytes"] == 1000
        assert stats["total_size_bytes"] == 3000
        assert "cdn.shopify.com" in stats["by_source"]
    
    def test_get_stats_with_skipped_sources(self, manifest_manager):
        """Test stats include skipped sources."""
        manifest_manager.initialize("www.fandomara.com")
        
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            status="downloaded",
        )
        manifest_manager.mark_skip("fonts.googleapis.com", "google_fonts")
        manifest_manager.mark_skip("fonts.gstatic.com", "google_fonts")
        
        stats = manifest_manager.get_stats()
        
        assert "fonts.googleapis.com" in stats["skipped_sources"]
        assert "fonts.gstatic.com" in stats["skipped_sources"]
        assert len(stats["skipped_sources"]) == 2


class TestPages:
    """Test page management."""
    
    def test_add_page(self, manifest_manager):
        """Test adding a page."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_page(
            url="www.fandomara.com/collections/all",
            html_path="pages/collections/all.html",
            assets_used=["base.css", "theme.css"],
        )
        
        manifest = manifest_manager.load()
        assert "www.fandomara.com/collections/all" in manifest["pages"]
        
        page = manifest["pages"]["www.fandomara.com/collections/all"]
        assert page["html_path"] == "pages/collections/all.html"
        assert "base.css" in page["assets_used"]
        assert page["localized"] is False
    
    def test_update_page(self, manifest_manager):
        """Test updating a page."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_page(
            url="www.fandomara.com/collections/all",
            html_path="pages/collections/all.html",
            assets_used=["base.css"],
        )
        
        manifest_manager.update_page(
            url="www.fandomara.com/collections/all",
            data={"localized": True},
        )
        
        manifest = manifest_manager.load()
        assert manifest["pages"]["www.fandomara.com/collections/all"]["localized"] is True


class TestGetAssetByUrl:
    """Test getting asset by URL."""
    
    def test_get_asset_by_url(self, manifest_manager):
        """Test retrieving asset by URL."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
            size=12345,
            status="downloaded",
        )
        
        asset = manifest_manager.get_asset_by_url("https://cdn.shopify.com/css/base.css")
        
        assert asset is not None
        assert asset["local_path"] == "assets/shopify/base.css"
        assert asset["status"] == "downloaded"
        assert asset["size"] == 12345
    
    def test_get_asset_not_found(self, manifest_manager):
        """Test getting non-existent asset."""
        manifest_manager.initialize("www.fandomara.com")
        asset = manifest_manager.get_asset_by_url("https://nonexistent.com/file.css")
        assert asset is None


class TestRealDataScenario:
    """Test with realistic data from collections/all page."""
    
    def test_collections_all_scenario(self, manifest_manager):
        """Test realistic scenario with collections/all page data."""
        site = "www.fandomara.com"
        manifest_manager.initialize(site)
        
        # Simulate assets from collections/all page
        assets = [
            # Shopify CDN assets
            {
                "url": "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/base.css",
                "local_path": "assets/shopify/base.css",
                "source_type": "shopify_cdn",
                "local_dir": "assets/shopify",
                "size": 45678,
                "status": "downloaded",
            },
            {
                "url": "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/theme.css",
                "local_path": "assets/shopify/theme.css",
                "source_type": "shopify_cdn",
                "local_dir": "assets/shopify",
                "size": 123456,
                "status": "pending",
            },
            {
                "url": "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/app.js",
                "local_path": "assets/shopify/app.js",
                "source_type": "shopify_cdn",
                "local_dir": "assets/shopify",
                "size": 78901,
                "status": "pending",
            },
            # Google Fonts - should be skipped
        ]
        
        for asset in assets:
            manifest_manager.add_asset(**asset)
        
        # Mark Google Fonts as skipped
        manifest_manager.mark_skip(
            "fonts.googleapis.com",
            "google_fonts",
            "License restrictions",
        )
        
        # Add the collections/all page
        manifest_manager.add_page(
            url=f"{site}/collections/all",
            html_path="pages/collections/all.html",
            assets_used=["base.css", "theme.css", "app.js"],
        )
        
        # Verify stats
        stats = manifest_manager.get_stats()
        assert stats["total_assets"] == 3
        assert stats["by_status"]["downloaded"] == 1
        assert stats["by_status"]["pending"] == 2
        assert stats["total_pages"] == 1
        assert "fonts.googleapis.com" in stats["skipped_sources"]
        
        # Verify pending assets for resume
        pending = manifest_manager.get_pending_assets()
        assert len(pending) == 2
        
        # Mark one as downloaded (resume scenario)
        manifest_manager.mark_downloaded(
            url="https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/theme.css",
            local_path="assets/shopify/theme.css",
            size=123456,
        )
        
        # Verify updated stats
        stats = manifest_manager.get_stats()
        assert stats["by_status"]["downloaded"] == 2
        assert stats["by_status"]["pending"] == 1
        
        # Final pending count
        pending = manifest_manager.get_pending_assets()
        assert len(pending) == 1
        assert "app.js" in pending[0]["filename"]


class TestReset:
    """Test manifest reset."""
    
    def test_reset(self, manifest_manager):
        """Test resetting manifest."""
        manifest_manager.initialize("www.fandomara.com")
        manifest_manager.add_asset(
            url="https://cdn.shopify.com/css/base.css",
            local_path="assets/shopify/base.css",
            source_type="shopify_cdn",
        )
        
        # Verify file exists
        assert manifest_manager.manifest_path.exists()
        
        # Reset
        manifest_manager.reset()
        
        # Verify file is gone
        assert not manifest_manager.manifest_path.exists()
        
        # Verify can load fresh
        manifest = manifest_manager.load()
        assert manifest["assets"] == {}


class TestThreadSafety:
    """Test thread safety of manifest operations."""
    
    def test_concurrent_updates(self, manifest_manager):
        """Test that concurrent updates don't corrupt data."""
        import threading
        
        manifest_manager.initialize("www.fandomara.com")
        
        def add_assets(start_idx):
            for i in range(start_idx, start_idx + 10):
                manifest_manager.add_asset(
                    url=f"https://cdn.shopify.com/css/file{i}.css",
                    local_path=f"assets/shopify/file{i}.css",
                    source_type="shopify_cdn",
                    local_dir="assets/shopify",
                    status="pending",
                )
        
        threads = [
            threading.Thread(target=add_assets, args=(0,)),
            threading.Thread(target=add_assets, args=(10,)),
            threading.Thread(target=add_assets, args=(20,)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify all assets were saved
        manifest = manifest_manager.load()
        shopify_files = manifest["assets"]["cdn.shopify.com"]["files"]
        assert len(shopify_files) == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
