"""
Tests for LinkLocalizer module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from pixel2liquid.localizer import (
    calc_relative_path,
    is_cdn_url,
    parse_url_with_query,
    LinkLocalizer,
)


class TestCalcRelativePath:
    """Test relative path calculation."""
    
    def test_same_directory(self):
        """Files in same directory."""
        result = calc_relative_path(
            'pages/index.html',
            'assets/image.jpg'
        )
        # pages/ -> assets/ = ../assets/image.jpg
        assert '..' in result
        assert result.endswith('assets/image.jpg')
    
    def test_nested_pages_to_assets(self):
        """Pages from nested directory to assets root."""
        result = calc_relative_path(
            'pages/www.fandomara.com/collections/all.html',
            'assets/shopify_cdn/images/hero.webp'
        )
        # pages/www.fandomara.com/collections/ -> assets/shopify_cdn/images/
        # = ../../../assets/shopify_cdn/images/hero.webp
        assert result == '../../../assets/shopify_cdn/images/hero.webp'
        print(f"✅ calc_relative_path: {result}")
    
    def test_nested_both(self):
        """Both files in nested directories."""
        result = calc_relative_path(
            'pages/www.fandomara.com/products/tshirt.html',
            'assets/shopify_cdn/css/base.css'
        )
        # pages/www.fandomara.com/products/ -> assets/shopify_cdn/css/
        assert result == '../../../assets/shopify_cdn/css/base.css'
    
    def test_sibling_pages(self):
        """Files in sibling directories."""
        result = calc_relative_path(
            'pages/www.fandomara.com/collections/all.html',
            'pages/www.fandomara.com/products/tshirt.html'
        )
        # Same parent dir, should use ./
        assert './' in result or result == '.'


class TestParseUrlWithQuery:
    """Test URL query string parsing."""
    
    def test_url_with_query(self):
        base, query = parse_url_with_query(
            'https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/hero.webp?v=xxx&width=1066'
        )
        assert query == '?v=xxx&width=1066'
        assert '?' not in base
    
    def test_url_without_query(self):
        base, query = parse_url_with_query(
            'https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/hero.webp'
        )
        assert query == ''
        assert base == 'https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/hero.webp'
    
    def test_url_only_query(self):
        base, query = parse_url_with_query(
            'https://cdn.shopify.com/s/files/1/0234/7891/2345/t/1/assets/hero.webp?v=abc'
        )
        assert query == '?v=abc'


class TestIsCdnUrl:
    """Test CDN URL detection."""
    
    def test_css_url_is_cdn(self):
        assert is_cdn_url('https://cdn.shopify.com/s/files/1/0234/base.css?v=xxx')
    
    def test_js_url_is_cdn(self):
        assert is_cdn_url('https://cdn.shopify.com/s/files/1/0234/app.js?v=xxx')
    
    def test_image_url_is_cdn(self):
        assert is_cdn_url('https://cdn.shopify.com/s/files/1/0234/hero.webp?v=xxx')
    
    def test_data_url_is_not_cdn(self):
        assert not is_cdn_url('data:image/png;base64,abc123')
    
    def test_html_url_is_not_cdn(self):
        assert not is_cdn_url('https://www.fandomara.com/collections/all.html')


class TestLinkLocalizerInit:
    """Test LinkLocalizer initialization."""
    
    def test_default_init(self, temp_dir):
        locator = LinkLocalizer(
            manifest_path=str(temp_dir / 'manifest.json'),
            pages_dir=str(temp_dir / 'pages'),
            assets_dir=str(temp_dir / 'assets'),
            output_dir=str(temp_dir / 'localized'),
        )
        assert locator.pages_dir == Path(temp_dir / 'pages')
        assert locator.assets_dir == Path(temp_dir / 'assets')
        assert locator.output_dir == Path(temp_dir / 'localized')


class TestLinkLocalizerHtmlReplacement:
    """Test HTML src/href replacement."""
    
    def test_basic_src_replacement(self, temp_dir):
        """Basic img src replacement."""
        # Set up manifest
        manifest_data = {
            "version": "1.0",
            "site": "www.fandomara.com",
            "assets": {
                "cdn.shopify.com": {
                    "type": "shopify_cdn",
                    "local_dir": "assets/shopify_cdn",
                    "skip": False,
                    "files": {
                        "hero.webp": {
                            "url": "https://cdn.shopify.com/s/files/1/0234/hero.webp?v=xxx",
                            "local_path": "assets/shopify_cdn/images/hero.webp",
                            "size": 12345,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Set up HTML
        pages_dir = temp_dir / 'pages'
        pages_dir.mkdir()
        html_content = '''<!DOCTYPE html>
<html>
<body>
<img src="https://cdn.shopify.com/s/files/1/0234/hero.webp?v=xxx&width=1066" alt="Hero">
</body>
</html>'''
        html_path = pages_dir / 'www.fandomara.com' / 'index.html'
        html_path.parent.mkdir()
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        # Run localizer
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(pages_dir),
            assets_dir=str(temp_dir / 'assets'),
            output_dir=str(temp_dir / 'localized'),
        )
        
        output_path = locator.localize('www.fandomara.com/index.html')
        
        # Should replace with relative path
        result = output_path.read_text()
        assert '../assets/shopify_cdn/images/hero.webp?v=xxx&width=1066' in result
        print(f"✅ HTML src replaced correctly")


class TestLinkLocalizerCssReplacement:
    """Test CSS url() replacement."""
    
    def test_basic_css_url_replacement(self, temp_dir):
        """Basic CSS url() replacement."""
        # Set up manifest
        manifest_data = {
            "version": "1.0",
            "site": "www.fandomara.com",
            "assets": {
                "cdn.shopify.com": {
                    "type": "shopify_cdn",
                    "local_dir": "assets/shopify_cdn",
                    "skip": False,
                    "files": {
                        "bg.webp": {
                            "url": "https://cdn.shopify.com/s/files/1/0234/bg.webp?v=xxx",
                            "local_path": "assets/shopify_cdn/images/bg.webp",
                            "size": 54321,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Set up CSS
        assets_dir = temp_dir / 'assets'
        assets_dir.mkdir()
        css_content = '''.hero {
    background: url('https://cdn.shopify.com/s/files/1/0234/bg.webp?v=xxx');
}'''
        css_path = assets_dir / 'shopify_cdn' / 'css' / 'base.css'
        css_path.parent.mkdir(parents=True)
        with open(css_path, 'w') as f:
            f.write(css_content)
        
        # Run localizer
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(temp_dir / 'pages'),
            assets_dir=str(assets_dir),
            output_dir=str(temp_dir / 'localized'),
        )
        
        result = locator.localize_css('shopify_cdn/css/base.css')
        
        # Should replace with relative path
        # assets/shopify_cdn/css/base.css -> assets/shopify_cdn/images/bg.webp
        # = ../../assets/shopify_cdn/images/bg.webp (from base.css's dir)
        assert '../../assets/shopify_cdn/images/bg.webp?v=xxx' in result
        print(f"✅ CSS url() replaced correctly: {result.strip()}")
    
    def test_css_url_no_quotes(self, temp_dir):
        """CSS url() without quotes."""
        manifest_data = {
            "version": "1.0",
            "site": "test.com",
            "assets": {
                "cdn.test.com": {
                    "type": "test_cdn",
                    "local_dir": "assets/test_cdn",
                    "skip": False,
                    "files": {
                        "img.png": {
                            "url": "https://cdn.test.com/img.png",
                            "local_path": "assets/test_cdn/images/img.png",
                            "size": 100,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        assets_dir = temp_dir / 'assets'
        assets_dir.mkdir()
        css_content = '.test { background: url(https://cdn.test.com/img.png); }'
        css_path = assets_dir / 'test.css'
        with open(css_path, 'w') as f:
            f.write(css_content)
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(temp_dir / 'pages'),
            assets_dir=str(assets_dir),
            output_dir=str(temp_dir / 'localized'),
        )
        
        result = locator.localize_css('test.css')
        
        # Should replace URL (preserves no-quote style)
        assert 'url(https://cdn.test.com/img.png)' not in result
        print(f"✅ CSS url() without quotes replaced: {result.strip()}")


class TestLinkLocalizerQueryParams:
    """Test query parameter preservation."""
    
    def test_query_params_preserved_html(self, temp_dir):
        """Query params preserved in HTML replacement."""
        manifest_data = {
            "version": "1.0",
            "site": "test.com",
            "assets": {
                "cdn.test.com": {
                    "type": "test",
                    "local_dir": "assets/test",
                    "skip": False,
                    "files": {
                        "image.jpg": {
                            "url": "https://cdn.test.com/image.jpg",
                            "local_path": "assets/test/image.jpg",
                            "size": 100,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        pages_dir = temp_dir / 'pages'
        pages_dir.mkdir()
        html_content = '''<img src="https://cdn.test.com/image.jpg?v=abc&width=800">'''
        html_path = pages_dir / 'index.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(pages_dir),
            assets_dir=str(temp_dir / 'assets'),
            output_dir=str(temp_dir / 'localized'),
        )
        
        output_path = locator.localize('index.html')
        result = output_path.read_text()
        assert '?v=abc&width=800' in result
        print(f"✅ Query params preserved in HTML")
    
    def test_query_params_preserved_css(self, temp_dir):
        """Query params preserved in CSS replacement."""
        manifest_data = {
            "version": "1.0",
            "site": "test.com",
            "assets": {
                "cdn.test.com": {
                    "type": "test",
                    "local_dir": "assets/test",
                    "skip": False,
                    "files": {
                        "bg.webp": {
                            "url": "https://cdn.test.com/bg.webp",
                            "local_path": "assets/test/bg.webp",
                            "size": 200,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        assets_dir = temp_dir / 'assets'
        assets_dir.mkdir()
        css_content = ".bg { background: url('https://cdn.test.com/bg.webp?v=xyz'); }"
        css_path = assets_dir / 'test.css'
        with open(css_path, 'w') as f:
            f.write(css_content)
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(temp_dir / 'pages'),
            assets_dir=str(assets_dir),
            output_dir=str(temp_dir / 'localized'),
        )
        
        result = locator.localize_css('test.css')
        
        assert '?v=xyz' in result
        print(f"✅ Query params preserved in CSS")


class TestLinkLocalizerOutput:
    """Test file output functionality."""
    
    def test_localize_page_to_file(self, temp_dir):
        """Test that localized HTML is saved to output directory."""
        manifest_data = {
            "version": "1.0",
            "site": "test.com",
            "assets": {
                "cdn.test.com": {
                    "type": "test",
                    "local_dir": "assets/test",
                    "skip": False,
                    "files": {
                        "img.jpg": {
                            "url": "https://cdn.test.com/img.jpg",
                            "local_path": "assets/test/img.jpg",
                            "size": 100,
                            "status": "downloaded",
                        }
                    }
                }
            },
            "pages": {},
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        pages_dir = temp_dir / 'pages'
        pages_dir.mkdir()
        html_content = '<img src="https://cdn.test.com/img.jpg?v=1">'
        html_path = pages_dir / 'index.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        output_dir = temp_dir / 'localized'
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(pages_dir),
            assets_dir=str(temp_dir / 'assets'),
            output_dir=str(output_dir),
        )
        
        output_path = locator.localize('index.html')
        
        assert output_path.exists()
        content = output_path.read_text()
        assert 'assets/test/img.jpg' in content
        print(f"✅ Output saved to {output_path}")


class TestLinkLocalizerFlatManifest:
    """Test flat manifest structure (URL as key directly)."""
    
    def test_flat_manifest_full_url_match(self, temp_dir):
        """Flat manifest with full URL as key (including query)."""
        # Flat manifest structure: URL as key directly
        manifest_data = {
            "https://cdn.shopify.com/s/files/1/0234/base.css?v=xxx": {
                "local_path": "assets/shopify_cdn/css/base.css",
                "status": "downloaded",
            }
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        pages_dir = temp_dir / 'pages'
        pages_dir.mkdir()
        html_content = '<link rel="stylesheet" href="https://cdn.shopify.com/s/files/1/0234/base.css?v=xxx">'
        html_path = pages_dir / 'test.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        assets_dir = temp_dir / 'assets'
        assets_dir.mkdir()
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(pages_dir),
            assets_dir=str(assets_dir),
            output_dir=str(temp_dir / 'localized'),
        )
        
        output_path = locator.localize('test.html')
        result = output_path.read_text()
        # Should find local path via flat manifest
        assert 'assets/shopify_cdn/css/base.css' in result
        print(f"✅ Flat manifest full URL match works")
    
    def test_flat_manifest_base_url_match(self, temp_dir):
        """Flat manifest with query string in URL but lookup may omit query."""
        manifest_data = {
            "https://cdn.shopify.com/s/files/1/0234/hero.webp": {
                "local_path": "assets/shopify_cdn/images/hero.webp",
                "status": "downloaded",
            }
        }
        manifest_path = temp_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        pages_dir = temp_dir / 'pages'
        pages_dir.mkdir()
        # URL with query params
        html_content = '<img src="https://cdn.shopify.com/s/files/1/0234/hero.webp?v=abc&width=800">'
        html_path = pages_dir / 'test.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        assets_dir = temp_dir / 'assets'
        assets_dir.mkdir()
        
        locator = LinkLocalizer(
            manifest_path=str(manifest_path),
            pages_dir=str(pages_dir),
            assets_dir=str(assets_dir),
            output_dir=str(temp_dir / 'localized'),
        )
        
        output_path = locator.localize('test.html')
        result = output_path.read_text()
        # Should find local path via base URL match (without query)
        assert 'assets/shopify_cdn/images/hero.webp' in result
        # Query params should be preserved
        assert '?v=abc&width=800' in result
        print(f"✅ Flat manifest base URL match with query preservation works")


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
