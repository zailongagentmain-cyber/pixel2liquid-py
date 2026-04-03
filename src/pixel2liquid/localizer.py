"""
LinkLocalizer Module - Replaces CDN resource references with local relative paths.

Replaces:
- HTML: <img src>, <link href>, <script src> etc.
- CSS: url() references

Input:  pages/*.html, assets/**/*.css
Output: localized/*.html, localized/assets/**/*.css
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse

from pixel2liquid.manifest import ManifestManager


# Regex for CSS url() - handles quoted and unquoted values
CSS_URL_PATTERN = re.compile(
    r'''url\(\s*(['"]?)([^)'"]+)\1\s*\)''',
    re.IGNORECASE
)

# Regex for HTML attributes with URLs
HTML_ATTR_PATTERNS = [
    (re.compile(r'''src\s*=\s*(['"])([^'"]+)\1''', re.IGNORECASE), 'src'),
    (re.compile(r'''href\s*=\s*(['"])([^'"]+)\1''', re.IGNORECASE), 'href'),
    (re.compile(r'''srcset\s*=\s*(['"])([^'"]+)\1''', re.IGNORECASE), 'srcset'),
]


def calc_relative_path(from_file: str, to_file: str) -> str:
    """
    Calculate relative path from one file to another.
    
    Args:
        from_file: Source file path (e.g., 'pages/www.fandomara.com/collections/all.html')
        to_file: Target file path (e.g., 'assets/shopify_cdn/images/hero.webp')
    
    Returns:
        Relative path string (e.g., '../../assets/shopify_cdn/images/hero.webp')
    """
    # Normalize paths
    from_path = Path(from_file).resolve()
    to_path = Path(to_file).resolve()
    
    # Get common ancestor
    try:
        relative = os.path.relpath(to_path.parent, from_path.parent)
    except ValueError:
        # On Windows, relpath fails if paths are on different drives
        return str(to_path)
    
    # Build result: relative path + filename
    if relative == '.':
        relative = './'
    
    return str(Path(relative) / to_path.name)


def parse_url_with_query(url: str) -> tuple[str, str]:
    """
    Split URL into (base_url, query_string).
    
    Returns:
        (base_url_without_query, '?query_string' or '')
    """
    parsed = urlparse(url)
    if parsed.query:
        query = '?' + parsed.query
    else:
        query = ''
    base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return base, query


def is_cdn_url(url: str) -> bool:
    """Check if URL is a CDN asset URL (not a full page URL)."""
    if not url or not url.startswith('http'):
        return False
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Skip data URLs
    if url.startswith('data:'):
        return False
    
    # Skip page URLs (no file extension or .html)
    if path.endswith('.html') or path.endswith('/') or not '.' in path.split('/')[-1]:
        # Might be a page, not an asset
        pass
    
    # CDN asset indicators
    cdn_indicators = ['.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.webp', 
                      '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf', '.eot',
                      '.avif', '.avifs']
    
    return any(path.endswith(ext) for ext in cdn_indicators)


class LinkLocalizer:
    """
    Replaces CDN resource references in HTML/CSS with local relative paths.
    
    Uses ManifestManager to look up local paths from full CDN URLs,
    then calculates relative paths from the HTML/CSS file location.
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
    
    def _load_manifest(self) -> dict:
        """Load manifest into memory for lookups."""
        return self.manifest.load()
    
    def _find_local_path(self, full_url: str) -> str | None:
        """
        Find local path for a full CDN URL from manifest.
        
        Args:
            full_url: Full asset URL with query params (e.g., 
                      'https://cdn.shopify.com/.../hero.webp?v=xxx&width=1066')
        
        Returns:
            Local path string (e.g., 'assets/shopify_cdn/images/hero.webp')
            or None if not found
        """
        manifest = self._load_manifest()
        
        # Parse URL
        base_url, _ = parse_url_with_query(full_url)
        parsed = urlparse(base_url)
        domain = parsed.netloc.lower()
        filename = parsed.path.split('/')[-1]
        
        # Look up in manifest
        if domain in manifest.get('assets', {}):
            source_data = manifest['assets'][domain]
            files = source_data.get('files', {})
            if filename in files:
                return files[filename].get('local_path')
        
        return None
    
    def _replace_url(self, url: str, from_file: str) -> str:
        """
        Replace a single URL with local relative path.
        
        Args:
            url: Full CDN URL (may have query params)
            from_file: HTML/CSS file being processed
        
        Returns:
            Replacement URL (relative path with query params preserved)
        """
        if not url or not url.startswith('http'):
            return url
        
        if not is_cdn_url(url):
            return url
        
        # Look up in manifest
        local_path = self._find_local_path(url)
        if local_path is None:
            # Not in manifest - keep original
            return url
        
        # Preserve query string from original URL
        _, query = parse_url_with_query(url)
        
        # Calculate relative path
        rel_path = calc_relative_path(from_file, local_path)
        
        return rel_path + query
    
    def localize_page(self, html_file: str) -> str:
        """
        Localize a single HTML file.
        
        Args:
            html_file: Relative path to HTML file (e.g., 'www.fandomara.com/collections/all.html')
        
        Returns:
            Localized HTML content
        """
        # Read input HTML
        input_path = self.pages_dir / html_file
        if not input_path.exists():
            raise FileNotFoundError(f"HTML file not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Replace src attributes
        def replace_src(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, html_file)
            return f'src={quote}{replaced}{quote}'
        
        # Replace href attributes
        def replace_href(match):
            quote = match.group(1)
            url = match.group(2)
            replaced = self._replace_url(url, html_file)
            return f'href={quote}{replaced}{quote}'
        
        # Replace srcset attributes
        def replace_srcset(match):
            quote = match.group(1)
            srcset = match.group(2)
            # srcset can have multiple URLs separated by comma+space
            # Format: url size descriptor, url size descriptor, ...
            def replace_srcset_url(m):
                url_part = m.group(0).strip()
                if url_part.startswith('http'):
                    replaced = self._replace_url(url_part, html_file)
                    return replaced
                return url_part
            
            # Split by comma and process each URL
            parts = []
            for part in srcset.split(','):
                part = part.strip()
                if part.startswith('http'):
                    # Extract URL and descriptor
                    url_match = re.match(r'(https?://\S+)\s*(\d+\w)?', part)
                    if url_match:
                        url = url_match.group(1)
                        desc = url_match.group(2) or ''
                        replaced = self._replace_url(url, html_file)
                        parts.append(f'{replaced} {desc}'.strip())
                    else:
                        parts.append(part)
                else:
                    parts.append(part)
            
            new_srcset = ', '.join(parts)
            return f'srcset={quote}{new_srcset}{quote}'
        
        # Apply replacements
        content = re.sub(
            r'''src\s*=\s*(['"])([^'"]+)\1''',
            replace_src,
            content,
            flags=re.IGNORECASE
        )
        
        content = re.sub(
            r'''href\s*=\s*(['"])([^'"]+)\1''',
            replace_href,
            content,
            flags=re.IGNORECASE
        )
        
        content = re.sub(
            r'''srcset\s*=\s*(['"])([^'"]+)\1''',
            replace_srcset,
            content,
            flags=re.IGNORECASE
        )
        
        return content
    
    def localize_css(self, css_file: str) -> str:
        """
        Localize a single CSS file.
        
        Args:
            css_file: Relative path to CSS file (e.g., 'shopify_cdn/css/base.css')
        
        Returns:
            Localized CSS content
        """
        # Read input CSS
        input_path = self.assets_dir / css_file
        if not input_path.exists():
            raise FileNotFoundError(f"CSS file not found: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace url() references
        def replace_url(match):
            quote = match.group(1)  # Opening quote ('', '"', or '')
            url = match.group(2)    # URL value
            replaced = self._replace_url(url, css_file)
            return f"url({quote}{replaced}{quote})"
        
        content = re.sub(
            CSS_URL_PATTERN,
            replace_url,
            content
        )
        
        return content
    
    def _save_localized(self, content: str, output_file: str) -> None:
        """Save localized content to output directory."""
        output_path = self.output_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def localize_page_to_file(self, html_file: str) -> Path:
        """
        Localize a single HTML file and save to output directory.
        
        Args:
            html_file: Relative path to HTML file
        
        Returns:
            Path to output file
        """
        content = self.localize_page(html_file)
        self._save_localized(content, html_file)
        return self.output_dir / html_file
    
    def localize_css_to_file(self, css_file: str) -> Path:
        """
        Localize a single CSS file and save to output directory.
        
        Args:
            css_file: Relative path to CSS file
        
        Returns:
            Path to output file
        """
        content = self.localize_css(css_file)
        self._save_localized(content, css_file)
        return self.output_dir / css_file
    
    def localize_all(self) -> dict:
        """
        Localize all HTML pages and CSS files.
        
        Returns:
            Dict with 'pages' and 'css' lists of processed files
        """
        results = {'pages': [], 'css': []}
        
        # Process HTML pages
        if self.pages_dir.exists():
            for html_path in self.pages_dir.rglob('*.html'):
                rel_path = html_path.relative_to(self.pages_dir)
                rel_str = str(rel_path).replace('\\', '/')
                try:
                    self.localize_page_to_file(rel_str)
                    results['pages'].append(rel_str)
                except Exception as e:
                    print(f"  ⚠️  Failed to localize page {rel_str}: {e}")
        
        # Process CSS files
        if self.assets_dir.exists():
            for css_path in self.assets_dir.rglob('*.css'):
                rel_path = css_path.relative_to(self.assets_dir)
                rel_str = str(rel_path).replace('\\', '/')
                try:
                    self.localize_css_to_file(rel_str)
                    results['css'].append(rel_str)
                except Exception as e:
                    print(f"  ⚠️  Failed to localize CSS {rel_str}: {e}")
        
        return results
