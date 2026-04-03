"""
Asset Classifier Module - Classifies and categorizes web assets for local download.
"""

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
            local_path = get_local_path(url, asset_type)
            source = DOMAIN_SOURCE_LABELS.get(domain, "unknown")
            
            return AssetInfo(
                url=url,
                local_path=local_path,
                source=source,
            )
        
        # For other domains, also try to download
        local_path = get_local_path(url, asset_type)
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
                    local_path = get_local_path(url, asset_type)
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
                    local_path = get_local_path(url, asset_type)
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
