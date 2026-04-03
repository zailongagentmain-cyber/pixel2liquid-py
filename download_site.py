#!/usr/bin/env python3
"""
Download script for pixel2liquid - Full site asset download
"""
import asyncio
import json
import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, '/Users/clawbot/projects/pixel2liquid-py/src')

from pixel2liquid.asset import AssetClassifier, AssetDownloader
from pixel2liquid.manifest import ManifestManager

CACHE_DIR = Path("/tmp/fandomara_cache/www.fandomara.com")
CRAWL_STATE_PATH = CACHE_DIR / "crawl_state.json"
OUTPUT_DIR = CACHE_DIR / "assets"
MANIFEST_PATH = CACHE_DIR / "manifest.json"

def load_crawl_state():
    """Load crawl state from JSON file."""
    with open(CRAWL_STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_site_assets(crawl_state, page_keys=None):
    """Classify all assets from crawl state for specified pages."""
    classifier = AssetClassifier()
    return classifier.classify_from_crawl_state(crawl_state, page_keys=page_keys)

async def download_with_progress(downloader, to_download, manifest, desc="Download"):
    """Download assets with progress reporting."""
    total_items = sum(len(v) for v in to_download.values())
    print(f"\n{'='*60}")
    print(f"{desc}")
    print(f"Total assets to download: {total_items}")
    print(f"{'='*60}")
    
    if total_items == 0:
        print("No assets to download.")
        return None
    
    # Add all assets to manifest before downloading
    for category, assets in to_download.items():
        for asset in assets:
            manifest.add_asset(
                url=asset["url"],
                local_path=asset["local_path"],
                source_type=asset["source"],
                local_dir=f"assets/{asset['source']}/{category}",
                status="pending"
            )
    
    start_time = time.time()
    result = await downloader.download_all(to_download)
    elapsed = time.time() - start_time
    
    # Update manifest with results
    for rec in result.records:
        if rec.status == "success":
            manifest.mark_downloaded(rec.url, rec.local_path, rec.size)
        elif rec.status == "failed":
            manifest.mark_failed(rec.url, rec.error or "Unknown error")
    
    print(f"\n{'='*60}")
    print(f"Download Results ({desc})")
    print(f"{'='*60}")
    print(f"Total:     {result.total}")
    print(f"Success:   {result.success}")
    print(f"Failed:    {result.failed}")
    print(f"Skipped:   {result.skipped}")
    print(f"Total bytes: {result.total_bytes:,}")
    print(f"Duration:  {elapsed:.1f}s")
    print(f"Speed:     {result.total_bytes/max(elapsed,0.1)/1024:.1f} KB/s")
    
    return result

async def main():
    print("="*60)
    print("Pixel2Liquid - Full Site Asset Download")
    print("="*60)
    
    # Load crawl state
    print("\n[1/5] Loading crawl state...")
    crawl_state = load_crawl_state()
    pages = crawl_state.get("pages", {})
    print(f"   Total pages in crawl state: {len(pages)}")
    
    # Initialize classifier and manifest
    classifier = AssetClassifier()
    manifest = ManifestManager(str(MANIFEST_PATH))
    manifest.initialize("www.fandomara.com")
    print(f"   Manifest initialized: {MANIFEST_PATH}")
    
    # Initialize downloader
    downloader = AssetDownloader(
        output_dir=str(OUTPUT_DIR),
        manifest_path=str(MANIFEST_PATH),
        verify_ssl=True
    )
    
    # ===== PHASE 1: Download collections/all first =====
    print("\n[2/5] Classifying collections/all assets...")
    collections_all_key = "www.fandomara.com/collections/all"
    result_all = classify_site_assets(crawl_state, page_keys=[collections_all_key])
    
    print(f"   Total assets found: {result_all.summary['total']}")
    print(f"   To download: {result_all.summary['to_download']}")
    print(f"   To skip: {result_all.summary['to_skip']}")
    
    # Show breakdown
    for cat in ["css", "js", "images", "fonts"]:
        items = result_all.to_download.get(cat, [])
        print(f"   - {cat}: {len(items)} files")
    
    # Download collections/all
    print("\n[3/5] Downloading collections/all assets...")
    await download_with_progress(downloader, result_all.to_download, manifest, "collections/all")
    
    # Check if there's a page 2 for collections/all
    page2_key = "www.fandomara.com/collections/all?page=2"
    if page2_key in pages:
        print("\n[3b/5] Downloading collections/all?page=2 assets...")
        result_p2 = classify_site_assets(crawl_state, page_keys=[page2_key])
        await download_with_progress(downloader, result_p2.to_download, manifest, "collections/all?page=2")
    
    # ===== PHASE 2: Download full site =====
    print("\n[4/5] Classifying ALL site assets...")
    full_result = classify_site_assets(crawl_state)  # All pages
    
    print(f"   Total assets found: {full_result.summary['total']}")
    print(f"   To download: {full_result.summary['to_download']}")
    print(f"   To skip: {full_result.summary['to_skip']}")
    
    # Show breakdown
    for cat in ["css", "js", "images", "fonts"]:
        items = full_result.to_download.get(cat, [])
        print(f"   - {cat}: {len(items)} files")
    
    print("\n[5/5] Downloading full site assets...")
    await download_with_progress(downloader, full_result.to_download, manifest, "Full Site Download")
    
    # Final stats
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    # Count downloaded files
    downloaded_files = list(OUTPUT_DIR.rglob("*"))
    file_count = len([f for f in downloaded_files if f.is_file()])
    dir_count = len([d for d in downloaded_files if d.is_dir()])
    
    # Manifest stats
    manifest_stats = manifest.get_stats()
    
    print(f"Manifest path: {MANIFEST_PATH}")
    print(f"Manifest size: {MANIFEST_PATH.stat().st_size:,} bytes")
    print(f"Total assets tracked: {manifest_stats['total_assets']}")
    print(f"Downloaded: {manifest_stats['by_status'].get('downloaded', 0)}")
    print(f"Pending: {manifest_stats['by_status'].get('pending', 0)}")
    print(f"Failed: {manifest_stats['by_status'].get('failed', 0)}")
    print(f"Total downloaded size: {manifest_stats['downloaded_size_bytes']:,} bytes ({manifest_stats['downloaded_size_bytes']/1024/1024:.1f} MB)")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Files on disk: {file_count}")
    print(f"Directories: {dir_count}")
    
    print("\nBy source:")
    for source, stats in manifest_stats.get("by_source", {}).items():
        print(f"  - {source}: {stats['downloaded']}/{stats['total']} downloaded")
    
    print("\nSkipped sources:")
    for src in manifest_stats.get("skipped_sources", []):
        print(f"  - {src}")

if __name__ == "__main__":
    asyncio.run(main())
