"""
Phase 1 — YouTube Transcript Extractor (Auto-Proxy Edition)
Channel: Charisma on Command (@Charismaoncommand)

This script will automatically scrape free proxies from the internet if 
your IP gets blocked, allowing it to run completely hands-free!

Usage:
    python youtube-transcript-api.py
"""

import json
import os
import subprocess
import time
import random
import re
import requests

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    IpBlocked,
)

# ── Config ────────────────────────────────────────────────────────────────────
CHANNEL_URL   = "https://www.youtube.com/@Charismaoncommand"
OUTPUT_FILE   = "charisma_transcripts.json"
LANG_PRIORITY = ["en", "en-US", "en-GB"]
REQUEST_DELAY = 3.0        # Base delay between requests


class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.session = requests.Session()
        
    def refresh_proxies(self):
        """Scrape fresh free proxies from free-proxy-list.net"""
        print("\n🔄 [Proxy Manager] Your IP is blocked. Scraping fresh free proxies...")
        try:
            res = requests.get('https://free-proxy-list.net/', timeout=10)
            new_proxies = []
            for match in re.finditer(r'<tr><td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>.*?<td class=\'hm\'>(yes|no)</td>', res.text):
                if match.group(3) == 'yes':
                    new_proxies.append(f'http://{match.group(1)}:{match.group(2)}')
            
            # Shuffle so we don't hit the exact same ones if we re-scrape
            random.shuffle(new_proxies)
            self.proxies = new_proxies
            print(f"✅ Found {len(self.proxies)} HTTPS proxies to test.")
        except Exception as e:
            print(f"⚠️ Failed to scrape proxies: {e}")

    def get_working_session(self) -> requests.Session:
        """Find a working proxy that isn't blocked by YouTube."""
        while True:
            if not self.proxies:
                self.refresh_proxies()
                if not self.proxies:
                    print("❌ No proxies available. Sleeping for 60s before retry...")
                    time.sleep(60)
                    continue

            p = self.proxies.pop(0)
            print(f"   Testing proxy: {p} ... ", end="", flush=True)
            
            session = requests.Session()
            session.proxies = {'http': p, 'https': p}
            
            # Use a short timeout so we don't waste time on dead proxies
            session.request = lambda method, url, **kwargs: requests.Session.request(
                session, method, url, timeout=8, **kwargs
            )
            
            try:
                # Test against a known video to see if proxy works and isn't IP-blocked
                yt = YouTubeTranscriptApi(http_client=session)
                yt.list('RS74828r7eU')
                print("✅ Working!")
                self.current_proxy = p
                self.session = session
                return session
            except IpBlocked:
                print("🚫 Blocked by YouTube")
            except Exception as e:
                print(f"❌ Dead ({type(e).__name__})")

    def handle_block(self):
        """Called when the current proxy gets blocked."""
        print(f"\n🚫 Proxy {self.current_proxy} got blocked by YouTube.")
        self.current_proxy = None


# ── Get all video IDs ──────────────────────────────────────────────────────────

def get_video_ids() -> list[dict]:
    print(f"📡 Fetching video list from YouTube…")
    cmd = [
        "yt-dlp", "--flat-playlist",
        "--print", "%(id)s\t%(title)s",
        "--no-warnings",
        f"{CHANNEL_URL}/videos",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    videos = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split("\t", 1)
        if len(parts) == 2:
            vid_id, title = parts[0].strip(), parts[1].strip()
            if vid_id:
                videos.append({
                    "video_id": vid_id,
                    "title":    title,
                    "url":      f"https://www.youtube.com/watch?v={vid_id}",
                })
    print(f"✅ Found {len(videos)} videos\n")
    return videos


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_existing() -> dict[str, dict]:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = {v["video_id"]: v for v in data}
        print(f"📂 Resuming: {len(existing)} already saved — skipping these")
        return existing
    return {}


def save(records: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Charisma on Command — Transcript Extractor")
    print("  (AUTO-PROXY EDITION — 100% Hands-Free!)")
    print("=" * 60)
    print()

    # Disconnect VPN if they are using one, because we handle proxies now
    existing = load_existing()
    videos   = get_video_ids()

    if not videos:
        print("❌ No videos found. Exiting.")
        return

    results = list(existing.values())
    
    proxy_manager = ProxyManager()
    
    # We start with NO proxy (your home IP). If it works, great. If blocked, we switch to proxies.
    session = requests.Session()
    session.request = lambda method, url, **kwargs: requests.Session.request(
        session, method, url, timeout=10, **kwargs
    )
    yt = YouTubeTranscriptApi(http_client=session)
    
    # Check if home IP is already blocked
    try:
        yt.list('RS74828r7eU')
    except IpBlocked:
        session = proxy_manager.get_working_session()
        yt = YouTubeTranscriptApi(http_client=session)
    except Exception:
        pass

    fetched = skipped = failed = no_captions = 0

    for i, video in enumerate(videos, 1):
        vid_id = video["video_id"]
        title  = video["title"]

        if vid_id in existing:
            skipped += 1
            continue

        print(f"\n[{i}/{len(videos)}] {title[:65]}…")
        
        result = None # Reset result for this video
        
        while True:
            try:
                transcript_list = yt.list(vid_id)
                try:
                    transcript = transcript_list.find_transcript(LANG_PRIORITY)
                except NoTranscriptFound:
                    try:
                        transcript = transcript_list.find_generated_transcript(LANG_PRIORITY)
                    except NoTranscriptFound:
                        all_t = list(transcript_list)
                        if not all_t:
                            transcript = None
                        else:
                            transcript = all_t[0]

                if transcript is not None:
                    snippets = transcript.fetch()
                    result = " ".join(s.text.replace("\n", " ") for s in snippets).strip()
                break # Success! Break out of the while loop

            except IpBlocked:
                # Our current proxy (or home IP) got blocked mid-run. Get a new one!
                if proxy_manager.current_proxy:
                    proxy_manager.handle_block()
                session = proxy_manager.get_working_session()
                yt = YouTubeTranscriptApi(http_client=session)
                # Loop restarts and tries fetching the same video again with the new proxy

            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Connection error ({type(e).__name__}). Switching proxy...")
                if proxy_manager.current_proxy:
                    proxy_manager.handle_block()
                session = proxy_manager.get_working_session()
                yt = YouTubeTranscriptApi(http_client=session)
                
            except (TranscriptsDisabled, NoTranscriptFound):
                print("   ⚠️  No captions available for this video")
                result = None
                break

            except VideoUnavailable:
                print("   ⚠️  Video is private or unavailable")
                result = None
                break

            except Exception as e:
                err = str(e)
                if "blocked" in err.lower() or "429" in err.lower() or "ipblocked" in err.lower():
                    if proxy_manager.current_proxy:
                        proxy_manager.handle_block()
                    session = proxy_manager.get_working_session()
                    yt = YouTubeTranscriptApi(http_client=session)
                    continue
                
                print(f"   ⚠️  Error: {err[:120]}")
                result = None
                break

        if result:
            results.append({
                "video_id":     vid_id,
                "title":        title,
                "url":          video["url"],
                "channel_name": "Charisma on Command",
                "transcript":   result,
            })
            fetched += 1
            print(f"   ✅ {len(result):,} chars")
            
            # Save every time to ensure we don't lose data if a proxy hangs
            save(results)
        elif result is None:
            failed += 1
            no_captions += 1

        time.sleep(REQUEST_DELAY + random.uniform(-1, 2.0))

    save(results)
    print(f"\n{'=' * 60}")
    print(f"✅ Done!")
    print(f"   Fetched       : {fetched} new transcripts")
    print(f"   Skipped       : {skipped} (already saved)")
    print(f"   No captions   : {no_captions}")
    print(f"   Total in file : {len(results)}")
    print(f"\n▶  Next step: python chuck_embeded.py")


if __name__ == "__main__":
    main()
