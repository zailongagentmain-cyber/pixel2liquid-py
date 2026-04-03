"""
Unit tests for AssetClassifier module.
"""

import json
import pytest
from pixel2liquid.asset import (
    AssetClassifier,
    AssetInfo,
    ClassificationResult,
    get_asset_type,
    get_local_path,
    get_domain,
    DOWNLOAD_DOMAINS,
    SKIP_DOMAINS,
)


class TestGetDomain:
    """Tests for get_domain function."""
    
    def test_shopify_cdn(self):
        url = "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/base.css?v=1175"
        assert get_domain(url) == "cdn.shopify.com"
    
    def test_fonts_shopifycdn(self):
        url = "https://fonts.shopifycdn.com/work_sans/worksans_n4.b7973b3d07d0ace13de1b1bea9c45759cdbe12cf.woff2"
        assert get_domain(url) == "fonts.shopifycdn.com"
    
    def test_gemcommerce(self):
        url = "https://assets.gemcommerce.com/assets-v2/gp-button-v7-5.js?v=1752485261645"
        assert get_domain(url) == "assets.gemcommerce.com"
    
    def test_google_fonts(self):
        url = "https://fonts.googleapis.com/css2?family=Work+Sans:wght@400"
        assert get_domain(url) == "fonts.googleapis.com"
    
    def test_gstatic(self):
        url = "https://fonts.gstatic.com/s/worksans/v20/XRXV3I6Li01BKofIO-aBTMsLVv43w.woff2"
        assert get_domain(url) == "fonts.gstatic.com"


class TestGetAssetType:
    """Tests for get_asset_type function."""
    
    def test_css(self):
        assert get_asset_type("https://cdn.shopify.com/s/files/1/base.css") == "css"
        assert get_asset_type("https://example.com/style.CSS") == "css"
    
    def test_js(self):
        assert get_asset_type("https://cdn.shopify.com/s/files/1/app.js") == "js"
        assert get_asset_type("https://example.com/bundle.JS") == "js"
    
    def test_fonts(self):
        assert get_asset_type("https://fonts.shopifycdn.com/font.woff2") == "fonts"
        assert get_asset_type("https://fonts.gstatic.com/font.ttf") == "fonts"
        assert get_asset_type("https://example.com/font.otf") == "fonts"
        assert get_asset_type("https://example.com/font.woff") == "fonts"
        assert get_asset_type("https://example.com/font.eot") == "fonts"
    
    def test_images(self):
        assert get_asset_type("https://cdn.shopify.com/s/files/1/image.png") == "images"
        assert get_asset_type("https://example.com/photo.jpg") == "images"
        assert get_asset_type("https://example.com/photo.jpeg") == "images"
        assert get_asset_type("https://example.com/photo.webp") == "images"
        assert get_asset_type("https://example.com/photo.gif") == "images"
        assert get_asset_type("https://example.com/photo.svg") == "images"
        assert get_asset_type("https://example.com/photo.ico") == "images"
    
    def test_unknown(self):
        assert get_asset_type("https://example.com/unknown.xyz") is None


class TestGetLocalPath:
    """Tests for get_local_path function."""
    
    def test_css_path(self):
        url = "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/base.css?v=1175"
        assert get_local_path(url, "css") == "assets/css/base.css"
    
    def test_js_path(self):
        url = "https://assets.gemcommerce.com/assets-v2/gp-button-v7-5.js?v=1752485261645"
        assert get_local_path(url, "js") == "assets/js/gp-button-v7-5.js"
    
    def test_fonts_path(self):
        url = "https://fonts.shopifycdn.com/work_sans/worksans_n4.b7973b3d07d0ace13de1b1bea9c45759cdbe12cf.woff2"
        assert get_local_path(url, "fonts") == "assets/fonts/worksans_n4.b7973b3d07d0ace13de1b1bea9c45759cdbe12cf.woff2"
    
    def test_images_path(self):
        url = "https://cdn.shopify.com/s/files/1/0913/4689/5219/files/FanoMara.png?v=1763136065&width=150"
        assert get_local_path(url, "images") == "assets/images/FanoMara.png"
    
    def test_unknown_asset_type(self):
        url = "https://example.com/file.xyz"
        assert get_local_path(url, "unknown") is None


class TestAssetClassifierSingle:
    """Tests for AssetClassifier.classify_asset method."""
    
    def setup_method(self):
        self.classifier = AssetClassifier()
    
    def test_shopify_cdn_css(self):
        url = "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/base.css?v=1175"
        result = self.classifier.classify_asset(url)
        
        assert result is not None
        assert result.url == url
        assert result.local_path == "assets/css/base.css"
        assert result.source == "shopify_cdn"
    
    def test_shopify_cdn_js(self):
        url = "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/global.js?v=18434551510515840980"
        result = self.classifier.classify_asset(url)
        
        assert result is not None
        assert result.source == "shopify_cdn"
    
    def test_gemcommerce_js(self):
        url = "https://assets.gemcommerce.com/assets-v2/gp-button-v7-5.js?v=1752485261645"
        result = self.classifier.classify_asset(url)
        
        assert result is not None
        assert result.source == "gemcommerce"
    
    def test_fonts_shopifycdn(self):
        url = "https://fonts.shopifycdn.com/work_sans/worksans_n4.b7973b3d07d0ace13de1b1bea9c45759cdbe12cf.woff2"
        result = self.classifier.classify_asset(url)
        
        assert result is not None
        assert result.source == "shopify_cdn"
    
    def test_google_fonts_skipped(self):
        url = "https://fonts.googleapis.com/css2?family=Work+Sans:wght@400"
        result = self.classifier.classify_asset(url)
        
        assert result is None
    
    def test_gstatic_skipped(self):
        url = "https://fonts.gstatic.com/s/worksans/v20/XRXV3I6Li01BKofIO-aBTMsLVv43w.woff2"
        result = self.classifier.classify_asset(url)
        
        assert result is None
    
    def test_data_url_skipped(self):
        url = "data:image/svg+xml;base64,PHN2Zy..."
        result = self.classifier.classify_asset(url)
        
        assert result is None
    
    def test_other_domain_downloaded(self):
        url = "https://example.com/assets/app.js"
        result = self.classifier.classify_asset(url)
        
        assert result is not None
        assert result.source == "other"


class TestAssetClassifierBatch:
    """Tests for AssetClassifier.classify_assets method."""
    
    def setup_method(self):
        self.classifier = AssetClassifier()
    
    def test_empty_asset_links(self):
        asset_links = {"css": [], "js": [], "images": [], "fonts": []}
        result = self.classifier.classify_assets(asset_links)
        
        assert result.summary["total"] == 0
        assert result.summary["to_download"] == 0
        assert result.summary["to_skip"] == 0
    
    def test_mixed_assets(self):
        asset_links = {
            "css": [
                "https://cdn.shopify.com/s/files/1/0913/4689/5219/t/9/assets/base.css?v=1175",
                "https://fonts.googleapis.com/css2?family=Work+Sans",
            ],
            "js": [
                "https://assets.gemcommerce.com/assets-v2/gp-button-v7-5.js?v=1752485261645",
                "https://fonts.gstatic.com/s/font.woff2",
            ],
            "images": [],
            "fonts": [
                "https://fonts.shopifycdn.com/work_sans/worksans_n4.b7973b3d07d0ace13de1b1bea9c45759cdbe12cf.woff2",
            ],
        }
        
        result = self.classifier.classify_assets(asset_links)
        
        assert result.summary["total"] == 5
        assert result.summary["to_download"] == 3
        assert result.summary["to_skip"] == 2
        
        # Check CSS
        assert len(result.to_download["css"]) == 1
        assert result.to_download["css"][0]["source"] == "shopify_cdn"
        
        # Check JS
        assert len(result.to_download["js"]) == 1
        assert result.to_download["js"][0]["source"] == "gemcommerce"
        
        # Check fonts
        assert len(result.to_download["fonts"]) == 1
        
        # Check skipped (google_fonts list contains all skipped: google fonts URLs + gstatic URLs + data URLs)
        assert len(result.skip["google_fonts"]) == 2  # 1 google fonts CSS URL + 1 gstatic font in js section


class TestAssetClassifierFromCrawlState:
    """Tests for AssetClassifier.classify_from_crawl_state method."""
    
    def setup_method(self):
        self.classifier = AssetClassifier()
    
    def test_real_data(self):
        """Test with actual crawl_state data from fandomara.com."""
        with open("/tmp/fandomara_cache/www.fandomara.com/crawl_state.json", "r") as f:
            crawl_state = json.load(f)
        
        # Test with collections/all page
        result = self.classifier.classify_from_crawl_state(
            crawl_state, 
            page_keys=["www.fandomara.com/collections/all"]
        )
        
        # Verify structure
        assert "css" in result.to_download
        assert "js" in result.to_download
        assert "images" in result.to_download
        assert "fonts" in result.to_download
        assert "google_fonts" in result.skip
        
        # Verify all downloaded assets have local_path
        for asset_type in ["css", "js", "images", "fonts"]:
            for asset in result.to_download[asset_type]:
                assert "url" in asset
                assert "local_path" in asset
                assert "source" in asset
                assert asset["local_path"].startswith(f"assets/{asset_type}/")
    
    def test_all_pages(self):
        """Test with all pages from crawl_state."""
        with open("/tmp/fandomara_cache/www.fandomara.com/crawl_state.json", "r") as f:
            crawl_state = json.load(f)
        
        result = self.classifier.classify_from_crawl_state(crawl_state)
        
        # Should have processed multiple pages
        assert result.summary["total"] > 0
        assert result.summary["to_download"] > 0
        
        # Verify no asset has google fonts domain
        for asset_type in ["css", "js", "images", "fonts"]:
            for asset in result.to_download[asset_type]:
                assert "fonts.googleapis.com" not in asset["url"]
                assert "fonts.gstatic.com" not in asset["url"]


class TestAssetInfo:
    """Tests for AssetInfo dataclass."""
    
    def test_creation(self):
        info = AssetInfo(
            url="https://cdn.shopify.com/test.css",
            local_path="assets/css/test.css",
            source="shopify_cdn"
        )
        
        assert info.url == "https://cdn.shopify.com/test.css"
        assert info.local_path == "assets/css/test.css"
        assert info.source == "shopify_cdn"


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""
    
    def test_default_values(self):
        result = ClassificationResult()
        
        assert "css" in result.to_download
        assert "js" in result.to_download
        assert "images" in result.to_download
        assert "fonts" in result.to_download
        assert "google_fonts" in result.skip
        
        assert result.summary["total"] == 0
        assert result.summary["to_download"] == 0
        assert result.summary["to_skip"] == 0
