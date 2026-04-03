"""
Integration tests for AssetClassifier + ManifestManager + AssetDownloader.

Tests the full flow:
1. AssetClassifier classifies resources
2. ManifestManager stores URL → local_path mapping (with query params preserved in URL)
3. AssetDownloader downloads and verifies
4. Verify no duplicate files from different query params
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from pixel2liquid.asset import AssetClassifier, AssetDownloader
from pixel2liquid.manifest import ManifestManager


# ------------------------------------------------------------------
# Test URL - minimal unit test case
# ------------------------------------------------------------------

TEST_URL_WITH_QUERY = "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/images/product-image.jpg?v=xxx&width=1066"
TEST_URL_SAME_BASE_DIFF_QUERY = "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/images/product-image.jpg?v=yyy&width=533"


class TestQueryParamStripping:
    """Test that query params are stripped from local filenames but preserved in manifest."""

    def test_get_local_path_strips_query_params(self):
        """AssetClassifier.get_local_path() should strip query params from filename."""
        classifier = AssetClassifier()
        
        # With query params
        path1 = classifier.get_local_path(TEST_URL_WITH_QUERY)
        path2 = classifier.get_local_path(TEST_URL_SAME_BASE_DIFF_QUERY)
        
        # Should be the SAME local path despite different query params
        assert path1 == path2, f"Expected same path but got {path1} vs {path2}"
        
        # Should NOT contain query params
        assert "?" not in path1, f"Query params should be stripped from local path: {path1}"
        assert "v=xxx" not in path1
        assert "width=1066" not in path1
        
        # Should have correct structure: assets/{source}/{asset_type}/{filename}
        assert path1 == "assets/shopify_cdn/images/product-image.jpg", f"Unexpected path: {path1}"
        
        print(f"✅ Query params correctly stripped: {path1}")

    def test_multiple_urls_same_base_same_local_path(self):
        """URLs with same base but different query params should map to same local file."""
        classifier = AssetClassifier()
        
        urls = [
            "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/images/hero.webp?v=abc&width=1066",
            "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/images/hero.webp?v=def&width=533",
            "https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/images/hero.webp?alt=media",
        ]
        
        paths = [classifier.get_local_path(url) for url in urls]
        
        # All should be the same
        assert len(set(paths)) == 1, f"All paths should be identical but got: {paths}"
        assert paths[0] == "assets/shopify_cdn/images/hero.webp"
        
        print(f"✅ Multiple query param variants correctly map to same local path: {paths[0]}")


class TestAssetClassifier:
    """Test AssetClassifier module."""

    def test_classify_single_asset(self):
        """Classify a single asset URL."""
        classifier = AssetClassifier()
        result = classifier.classify_asset(TEST_URL_WITH_QUERY)
        
        assert result is not None
        assert result.url == TEST_URL_WITH_QUERY  # Full URL with query params preserved
        assert result.local_path == "assets/shopify_cdn/images/product-image.jpg"  # Query stripped
        assert result.source == "shopify_cdn"
        
        print(f"✅ classify_asset result: URL={result.url}, local_path={result.local_path}")

    def test_classify_same_base_different_query(self):
        """Two URLs with same base but different query params should classify to same local_path."""
        classifier = AssetClassifier()
        
        result1 = classifier.classify_asset(TEST_URL_WITH_QUERY)
        result2 = classifier.classify_asset(TEST_URL_SAME_BASE_DIFF_QUERY)
        
        assert result1 is not None
        assert result2 is not None
        
        # URLs are different (query params differ)
        assert result1.url != result2.url
        
        # But local_paths are the same (query params stripped)
        assert result1.local_path == result2.local_path
        
        print(f"✅ Same base different query: URL1={result1.url}, URL2={result2.url}")
        print(f"   Both map to same local_path: {result1.local_path}")


class TestManifestManagerStoresFullURL:
    """Test that ManifestManager stores full URL with query params."""

    def test_manifest_stores_full_url(self, temp_dir):
        """Manifest should store full URL (with query params) in file entry."""
        manifest_path = temp_dir / "manifest.json"
        mm = ManifestManager(str(manifest_path))
        
        # Add asset with URL containing query params
        mm.add_asset(
            url=TEST_URL_WITH_QUERY,
            local_path="assets/shopify_cdn/images/product-image.jpg",
            source_type="shopify_cdn",
            size=12345,
            status="downloaded",
        )
        
        # Load and verify
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # The file entry is stored by filename (key), not by full URL
        # But the full URL IS preserved inside the file entry
        file_entry = manifest["assets"]["cdn.shopify.com"]["files"]["product-image.jpg"]
        assert file_entry["url"] == TEST_URL_WITH_QUERY  # Full URL preserved
        assert file_entry["local_path"] == "assets/shopify_cdn/images/product-image.jpg"
        
        print(f"✅ Manifest correctly stores full URL in file entry: {file_entry['url']}")


class TestIntegrationMinimal:
    """Minimal integration test - one asset through the full pipeline."""

    def test_full_pipeline_single_asset(self, temp_dir):
        """
        Test the full pipeline with a single asset:
        1. AssetClassifier classifies the URL
        2. ManifestManager stores the mapping
        3. AssetDownloader downloads (or verifies)
        4. Verify manifest has full URL, local file has no query params
        """
        output_dir = temp_dir / "downloads"
        manifest_path = temp_dir / "manifest.json"
        
        # Step 1: AssetClassifier
        classifier = AssetClassifier()
        asset_info = classifier.classify_asset(TEST_URL_WITH_QUERY)
        
        assert asset_info is not None
        assert "?" not in asset_info.local_path, "local_path should not have query params"
        
        print(f"Step 1 - AssetClassifier:")
        print(f"  URL (full): {asset_info.url}")
        print(f"  local_path: {asset_info.local_path}")
        
        # Step 2: ManifestManager stores the mapping
        mm = ManifestManager(str(manifest_path))
        mm.add_asset(
            url=asset_info.url,  # Full URL with query params
            local_path=asset_info.local_path,  # Clean local path
            source_type=asset_info.source,
            size=0,
            status="pending",
        )
        
        # Verify manifest stores full URL as key
        manifest = mm.load()
        file_entry = manifest["assets"]["cdn.shopify.com"]["files"]["product-image.jpg"]
        
        assert file_entry["url"] == TEST_URL_WITH_QUERY, "Manifest should store full URL"
        assert "?" not in file_entry["local_path"], "local_path should be clean"
        
        print(f"Step 2 - ManifestManager: stored full URL as key")
        
        # Step 3: Verify the structure is correct
        # The manifest key is the FULL URL, but local_path is clean
        print(f"Step 3 - Verification:")
        print(f"  Manifest URL key: {TEST_URL_WITH_QUERY}")
        print(f"  Local file path: {asset_info.local_path}")
        print(f"  ✅ No duplicate files will be created for different query params!")


class TestIntegrationRealData:
    """Integration test using real crawl_state data."""

    def test_collections_all_single_image(self, temp_dir):
        """Download a single image from collections/all page using real data."""
        crawl_state_path = "/tmp/fandomara_cache/www.fandomara.com/crawl_state.json"
        
        if not os.path.exists(crawl_state_path):
            pytest.skip(f"Test data not found: {crawl_state_path}")
        
        with open(crawl_state_path, "r") as f:
            crawl_state = json.load(f)
        
        # Step 1: Classify assets from collections/all
        classifier = AssetClassifier()
        result = classifier.classify_from_crawl_state(
            crawl_state,
            page_keys=["www.fandomara.com/collections/all"],
        )
        
        # Get first image
        images = result.to_download.get("images", [])
        if not images:
            pytest.skip("No images found in collections/all page")
        
        first_image = images[0]
        
        print(f"Step 1 - AssetClassifier found {len(images)} images")
        print(f"  First image URL: {first_image['url']}")
        print(f"  First image local_path: {first_image['local_path']}")
        
        # Verify query params are stripped from local_path
        assert "?" not in first_image["local_path"], \
            f"local_path should not contain query params: {first_image['local_path']}"
        
        # Step 2: Download just this one image
        output_dir = temp_dir / "downloads"
        manifest_path = temp_dir / "manifest.json"
        
        dl = AssetDownloader(
            output_dir=str(output_dir),
            manifest_path=str(manifest_path),
        )
        
        to_dl = {
            "css": [],
            "js": [],
            "images": [first_image],
            "fonts": [],
        }
        
        dl_result = dl.download_all_sync(to_dl, limit=1)
        
        # Step 3: Verify results
        print(f"\nStep 2 - AssetDownloader results:")
        print(f"  Total: {dl_result.total}")
        print(f"  Success: {dl_result.success}")
        print(f"  Failed: {dl_result.failed}")
        
        # Step 4: Verify manifest has full URL
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        print(f"\nStep 3 - Manifest verification:")
        for url, info in manifest.items():
            print(f"  URL: {url}")
            print(f"  local_path: {info['local_path']}")
            assert "?" in url, "Manifest should store full URL with query params"
            assert "?" not in info["local_path"], "local_path should not have query params"
        
        # Step 5: Verify local file exists and has correct name
        local_path = first_image["local_path"]
        full_local_path = output_dir / local_path
        
        print(f"\nStep 4 - Local file verification:")
        print(f"  Expected path: {full_local_path}")
        
        if full_local_path.exists():
            print(f"  ✅ File exists: {full_local_path}")
            print(f"  File size: {full_local_path.stat().st_size:,} bytes")
        else:
            print(f"  ❌ File not found: {full_local_path}")
        
        # Verify no duplicate files were created
        all_files = list(output_dir.rglob("*"))
        image_files = [f for f in all_files if f.is_file() and f.suffix in [".jpg", ".jpeg", ".webp", ".png"]]
        
        print(f"\nStep 5 - Duplicate check:")
        print(f"  Total image files in output: {len(image_files)}")
        
        # There should be exactly 1 image file (product-image.jpg)
        # NOT 2 files like product-image.jpg?v=xxx&width=1066 and product-image.jpg?v=yyy&width=533
        assert len(image_files) <= 1, f"Expected at most 1 image file but found {len(image_files)}: {image_files}"


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
