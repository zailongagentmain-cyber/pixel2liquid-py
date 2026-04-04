"""
LinkLocalizer Module - Replaces CDN resource references with local relative paths.

Replaces:
- HTML: <img src>, <link href>, <script src>, srcset etc.
- CSS: url() references

Input:  pages/*.html, assets/**/*.css
Output: localized/*.html, localized/assets/**/*.css

Single entry point: localize()
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

from pixel2liquid.manifest import ManifestManager


# Regex for CSS url() - handles quoted and unquoted values
CSS_URL_PATTERN = re.compile(
    r'''url\(\s*(['"]?)([^)'"]+)\1\s*\)''',
    re.IGNORECASE
)


def calc_relative_path(from_file: str, to_file: str) -> str:
    """
    Calculate relative path from one file to another.
    
    Args:
        from_file: Source file path (e.g., 'pages/www.fandomara.com/collections/all.html')
        to_file: Target file path (e.g., 'assets/shopify_cdn/images/hero.webp')
    
    Returns:
        Relative path string (e.g., '../../assets/shopify_cdn/images/hero.webp')
    """
    from_path = Path(from_file).resolve()
    to_path = Path(to_file).resolve()
    
    try:
        relative = os.path.relpath(to_path.parent, from_path.parent)
    except ValueError:
        return str(to_path)
    
    if relative == '.':
        relative = './'
    
    return str(Path(relative) / to_path.name)



def is_cdn_url(url: str) -> bool:
    """Check if URL is a CDN asset URL (not a full page URL)."""
    if not url:
        return False
    
    normalized = url
    if url.startswith('//'):
        normalized = 'https:' + url
    elif not url.startswith('http'):
        return False
    
    parsed = urlparse(normalized)
    path = parsed.path.lower()
    
    if normalized.startswith('data:'):
        return False
    
    if path.endswith('.html') or path.endswith('/') or not '.' in path.split('/')[-1]:
        pass
    
    cdn_indicators = [
        '.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf', '.eot',
        '.avif', '.avifs',
    ]
    
    return any(path.endswith(ext) for ext in cdn_indicators)


class LinkLocalizer:
    """
    Replaces CDN resource references in HTML/CSS with local relative paths.
    
    Single entry point: localize(html_file) -> Path
    All other methods are internal implementation.
    """
    
    def __init__(
        self,
        manifest_path: str = "manifest.json",
        pages_dir: str = "pages",
        assets_dir: str = "assets",
        output_dir: str = "localized",
    ):
        self.manifest = ManifestManager(manifest_path)
        self.pages_dir = Path(pages_dir)
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
    
    # ------------------------------------------------------------------
    # Public API - Single Entry Point
    # ------------------------------------------------------------------
    
    def localize(self, html_file: str) -> Path:
        """
        Main (and only) public entry point for HTML localization.
        
        Reads HTML, replaces CDN URLs with local relative paths,
        writes output to the localized directory, and returns the output path.
        
        Args:
            html_file: Relative path to HTML file (e.g., 'www.fandomara.com/collections/all.html')
        
        Returns:
            Path to the output file (localized/<html_file>)
        """
        content = self._process_html(html_file)
        return self._write_output(html_file, content)
    
    def localize_all(self) -> dict:
        """
        Localize all HTML pages in the pages directory.
        
        Returns:
            Dict with 'pages' list of processed file paths.
        """
        results: dict[str, list[str]] = {'pages': [], 'css': []}
        
        if not self.pages_dir.exists():
            return results
        
        for html_path in self.pages_dir.rglob('*.html'):
            rel_path = html_path.relative_to(self.pages_dir)
            rel_str = str(rel_path).replace('\\', '/')
            try:
                self.localize(rel_str)
                results['pages'].append(rel_str)
            except Exception as e:
                print(f"  ⚠️  Failed to localize page {rel_str}: {e}")
        
        return results
    
    def localize_css(self, css_file: str) -> str:
        """
        Public entry point for CSS localization.
        
        Args:
            css_file: Relative path to CSS file (e.g., 'shopify_cdn/css/base.css')
        
        Returns:
            Localized CSS content string.
        """
        return self._process_css(css_file)
    
    # ------------------------------------------------------------------
    # Internal Implementation
    # ------------------------------------------------------------------
    
    def _process_html(self, html_file: str) -> str:
        """Process HTML file: read content and replace all CDN URLs."""
        input_path = self.pages_dir / html_file
        if not input_path.exists():
            raise FileNotFoundError(f"HTML file not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = self._replace_src(content, html_file)
        content = self._replace_href(content, html_file)
        content = self._replace_srcset(content, html_file)  # srcset attribute
        content = self._replace_data_srcset(content, html_file)  # data-srcset attribute (P0)
        content = self._replace_meta_og_image(content, html_file)  # og:image meta (P1)
        content = self._replace_link_icon(content, html_file)  # <link rel="icon"> (P1)
        content = self._replace_import_statements(content, html_file)  # ES module import() (P0)
        
        return content
    
    def _replace_src(self, content: str, from_file: str) -> str:
        """Replace all src attributes in HTML content."""
        def replacer(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, from_file)
            return f'src={quote}{replaced}{quote}'
        
        return re.sub(
            r'''src\s*=\s*(['"])([^'"]+)\1''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_href(self, content: str, from_file: str) -> str:
        """Replace all href attributes in HTML content."""
        def replacer(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, from_file)
            return f'href={quote}{replaced}{quote}'
        
        return re.sub(
            r'''href\s*=\s*(['"])([^'"]+)\1''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_srcset(self, content: str, from_file: str) -> str:
        """Replace all srcset attributes in HTML content."""
        def replacer(match):
            quote = match.group(1)
            srcset = match.group(2)
            
            parts = []
            for part in srcset.split(','):
                part = part.strip()
                
                # Bug fix: handle protocol-relative URLs
                if part.startswith('//'):
                    part = 'https:' + part
                
                if part.startswith('http'):
                    url_match = re.match(r'(https?://\S+)\s*(\d+\w)?', part)
                    if url_match:
                        url = url_match.group(1)
                        desc = url_match.group(2) or ''
                        replaced = self._replace_url(url, from_file)
                        # New approach: no query params, let Shopify image_url filter handle them
                        parts.append(f'{replaced} {desc}'.strip())
                    else:
                        parts.append(part)
                else:
                    parts.append(part)
            
            new_srcset = ', '.join(parts)
            return f'srcset={quote}{new_srcset}{quote}'
        
        return re.sub(
            r'''srcset\s*=\s*(['"])([^'"]+)\1''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_data_srcset(self, content: str, from_file: str) -> str:
        """Replace all data-srcset attributes in HTML content (P0)."""
        def replacer(match):
            quote = match.group(1)
            srcset = match.group(2)
            
            parts = []
            for part in srcset.split(','):
                part = part.strip()
                
                # Bug fix: handle protocol-relative URLs
                if part.startswith('//'):
                    part = 'https:' + part
                
                if part.startswith('http'):
                    url_match = re.match(r'(https?://\S+)\s*(\d+\w)?', part)
                    if url_match:
                        url = url_match.group(1)
                        desc = url_match.group(2) or ''
                        replaced = self._replace_url(url, from_file)
                        # New approach: no query params, let Shopify image_url filter handle them
                        parts.append(f'{replaced} {desc}'.strip())
                    else:
                        parts.append(part)
                else:
                    parts.append(part)
            
            new_srcset = ', '.join(parts)
            return f'data-srcset={quote}{new_srcset}{quote}'
        
        return re.sub(
            r'''data-srcset\s*=\s*(['"])([^'"]+)\1''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_meta_og_image(self, content: str, from_file: str) -> str:
        """Replace og:image meta content URLs (P1)."""
        def replacer(match):
            content_attr = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, from_file)
            return f'content={content_attr}{replaced}{content_attr}'
        
        return re.sub(
            r'''content\s*=\s*(['"])([^'"]+)\1''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_link_icon(self, content: str, from_file: str) -> str:
        """Replace icon link href attributes (P1)."""
        def replacer(match):
            rel = match.group(1)
            href = match.group(2)
            if 'icon' in rel.lower():
                replaced = self._replace_url(href, from_file)
                return f'href={replaced}'
            return match.group(0)
        
        return re.sub(
            r'''rel\s*=\s*(['"])([^'"]+)\1\s+href\s*=\s*(['\"])([^'\"]+)\3''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_import_statements(self, content: str, from_file: str) -> str:
        """Replace ES module import() URLs in JavaScript (P0)."""
        def replacer(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, from_file)
            return f'import({quote}{replaced}{quote})'
        
        return re.sub(
            r'''import\s*\(\s*(['"])([^'"]+)\1\s*\)''',
            replacer,
            content,
            flags=re.IGNORECASE,
        )
    
    def _replace_css_urls(self, content: str, from_file: str) -> str:
        """Replace all url() references in CSS content."""
        def replacer(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, from_file)
            return f"url({quote}{replaced}{quote})"
        
        return re.sub(CSS_URL_PATTERN, replacer, content)
    
    def _process_css(self, css_file: str) -> str:
        """Process CSS file: read content and replace all url() references."""
        input_path = self.assets_dir / css_file
        if not input_path.exists():
            raise FileNotFoundError(f"CSS file not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._replace_css_urls(content, css_file)
    
    def _write_output(self, output_file: str, content: str) -> Path:
        """Write content to output directory."""
        output_path = self.output_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path
    
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    
    def _load_manifest(self) -> dict:
        """Load manifest into memory for lookups."""
        return self.manifest.load()
    
    def _find_local_path(self, full_url: str) -> str | None:
        """
        Find local path for a CDN URL from manifest.
        
        Only compares URL path, ignores query params (Shopify handles them automatically).
        Supports flat manifest (URL as key) and nested manifest structures.
        """
        manifest = self._load_manifest()
        
        # Extract URL path (without query)
        parsed = urlparse(full_url)
        base_url = parsed.netloc + parsed.path  # e.g., cdn.shopify.com/s/files/.../image.jpg
        
        # Case 1: Flat manifest - exact match with full URL
        if full_url in manifest:
            return manifest[full_url].get('local_path')
        
        # Case 2: Flat manifest - base URL match (without query)
        if base_url in manifest:
            return manifest[base_url].get('local_path')
        
        # Case 3: Flat manifest - path match (ignoring query)
        for url, data in manifest.items():
            if isinstance(data, dict) and url.startswith('http'):
                manifest_parsed = urlparse(url)
                manifest_base = manifest_parsed.netloc + manifest_parsed.path
                if base_url == manifest_base:
                    return data.get('local_path')
        
        # Case 4: Nested manifest structure (legacy)
        parsed_for_nested = urlparse(full_url)
        domain = parsed_for_nested.netloc.lower()
        filename = parsed_for_nested.path.split('/')[-1]
        
        if domain in manifest.get('assets', {}):
            source_data = manifest['assets'][domain]
            files = source_data.get('files', {})
            if filename in files:
                return files[filename].get('local_path')
        
        return None
    
    def _replace_url(self, url: str, from_file: str) -> str:
        """
        Replace a single URL with local relative path.
        
        Note: No query params, Shopify image_url filter handles them automatically.
        """
        if not url:
            return url
        
        # Handle protocol-relative
        normalized_url = url
        if url.startswith('//'):
            normalized_url = 'https:' + url
        
        if not is_cdn_url(normalized_url):
            return url
        
        local_path = self._find_local_path(normalized_url) or self._find_local_path(url)
        if local_path is None:
            return url
        
        # New approach: no query params, return local path directly
        rel_path = calc_relative_path(from_file, local_path)
        return rel_path
