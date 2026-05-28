"""
Phase 1 — YouTube Transcript Extractor (yt-dlp based)
Channel: Charisma on Command

Uses yt-dlp to download subtitle files (.vtt) directly — much better
at bypassing YouTube's bot detection than youtube-transcript-api.

Usage:
    python youtube-transcript-api.py
"""

import json
import os
import re
import subprocess
import time
import random
import glob

# ── Config ────────────────────────────────────────────────────────────────────
CHANNEL_URL   = "https://www.youtube.com/@Charismaoncommand"
OUTPUT_FILE   = "charisma_transcripts.json"
COOKIE_FILE   = "cookies.txt"
BROWSER       = "chrome"
SUBTITLE_DIR  = "./subtitles_tmp"       # temp folder for .vtt files
REQUEST_DELAY = 4.0
JITTER        = 2.0


# ── Cookie export ─────────────────────────────────────────────────────────────

def export_cookies() -> bool:
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 500:
        print(f"🍪 Found existing {COOKIE_FILE} — reusing it")
        return True

    print(f"🍪 Exporting cookies from {BROWSER}…")
    print("   (Mac may ask for login password — enter it, it's safe)")
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", BROWSER,
        "--cookies", COOKIE_FILE,
        "--flat-playlist", "--playlist-items", "1",
        "--print", "%(id)s", "--no-warnings", "--quiet",
        f"{CHANNEL_URL}/videos",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 500:
        print(f"   ✅ Cookies saved ({os.path.getsize(COOKIE_FILE)} bytes)")
        return True
    print(f"   ⚠️  Cookie export failed: {result.stderr[:200]}")
    return False


# ── Get video list ─────────────────────────────────────────────────────────────

def get_video_ids() -> list[dict]:
    print(f"\n📡 Fetching video list…")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(id)s\t%(title)s",
        "--no-warnings",
    ]
    if os.path.exists(COOKIE_FILE):
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(f"{CHANNEL_URL}/videos")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    videos = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split("\t", 1)
        if len(parts) == 2:
            vid_id, title = parts[0].strip(), parts[1].strip()
            videos.append({
                "video_id": vid_id,
                "title":    title,
                "url":      f"https://www.youtube.com/watch?v={vid_id}",
            })
    print(f"✅ Found {len(videos)} videos")
    return videos


# ── Parse .vtt subtitle file ──────────────────────────────────────────────────

def parse_vtt(vtt_path: str) -> str:
    """Convert a .vtt subtitle file into clean plain text."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove WEBVTT header and timestamps
    content = re.sub(r"WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"\d{2}:\d{2}:\d{2}\.\d+ --> \d{2}:\d{2}:\d{2}\.\d+.*\n", "", content)
    content = re.sub(r"<[^>]+>", "", content)           # remove <c> tags
    content = re.sub(r"&amp;", "&", content)
    content = re.sub(r"&lt;", "<", content)
    content = re.sub(r"&gt;", ">", content)

    # Deduplicate repeated lines (auto-captions repeat a lot)
    lines = content.strip().split("\n")
    seen = set()
    unique = []
    for line in lines:
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            unique.append(line)

    return " ".join(unique)


# ── Download subtitles for one video via yt-dlp ───────────────────────────────

def fetch_transcript_ytdlp(video_id: str, title: str) -> str | None:
    """
    Download auto-generated subtitles using yt-dlp.
    yt-dlp has much better bot-evasion than youtube-transcript-api.
    """
    os.makedirs(SUBTITLE_DIR, exist_ok=True)
    out_template = os.path.join(SUBTITLE_DIR, f"{video_id}")
    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        "yt-dlp",
        "--write-auto-sub",         # download auto-generated captions
        "--write-sub",              # also try manual captions
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",          # don't download the video itself
        "--no-warnings",
        "--output", out_template,
    ]
    if os.path.exists(COOKIE_FILE):
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Find the downloaded .vtt file (yt-dlp names it like: ID.en.vtt)
        vtt_files = glob.glob(f"{out_template}*.vtt")
        if not vtt_files:
            # Check stderr for clues
            stderr = result.stderr.lower()
            if "no subtitles" in stderr or "requested format is not available" in stderr:
                print(f"   ⚠️  No English captions available")
            elif "blocked" in stderr or "429" in stderr:
                print(f"   🚫 IP-blocked by YouTube")
            else:
                print(f"   ⚠️  No .vtt file downloaded")
            return None

        # Parse the first matching .vtt file
        text = parse_vtt(vtt_files[0])

        # Clean up temp files
        for f in vtt_files:
            os.remove(f)

        return text if len(text) > 50 else None

    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timed out downloading subtitles")
        return None
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)[:100]}")
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_existing() -> dict[str, dict]:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = {v["video_id"]: v for v in data}
        print(f"📂 Loaded {len(existing)} existing transcripts — will skip these")
        return existing
    return {}


def save(records: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"   💾 Saved {len(records)} total → {OUTPUT_FILE}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Charisma on Command — Transcript Extractor (yt-dlp)")
    print("=" * 60)

    export_cookies()
    existing = load_existing()
    videos   = get_video_ids()

    if not videos:
        print("❌ No videos found. Exiting.")
        return

    results  = list(existing.values())
    fetched  = skipped = failed = 0

    for i, video in enumerate(videos, 1):
        vid_id = video["video_id"]
        title  = video["title"]

        if vid_id in existing:
            skipped += 1
            continue

        print(f"\n[{i}/{len(videos)}] {title[:65]}…")
        transcript = fetch_transcript_ytdlp(vid_id, title)

        if transcript:
            results.append({
                "video_id":     vid_id,
                "title":        title,
                "url":          video["url"],
                "channel_name": "Charisma on Command",
                "transcript":   transcript,
            })
            fetched += 1
            print(f"   ✅ {len(transcript):,} chars")
        else:
            failed += 1

        if fetched > 0 and fetched % 10 == 0:
            save(results)

        time.sleep(REQUEST_DELAY + random.uniform(-1, JITTER))

    save(results)
    print(f"\n{'=' * 60}")
    print(f"✅ Done!")
    print(f"   Fetched : {fetched} | Skipped : {skipped} | Failed : {failed}")
    print(f"   Total   : {len(results)} transcripts → {OUTPUT_FILE}")
    print(f"\n▶  Next: python chuck_embeded.py")


if __name__ == "__main__":
    main()
