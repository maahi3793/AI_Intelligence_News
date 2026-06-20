"""
Backfill Trends Script
Purpose: Retroactively populate the Supabase 'trends' table by scanning ALL
         existing newsletters and their articles for AI entity mentions.

Usage:
    python scripts/backfill_trends.py

This script:
  1. Connects to Supabase
  2. Fetches all newsletters ordered by publish_date
  3. For each newsletter, fetches its articles
  4. Extracts topics from article titles, themes_used, and content
  5. Inserts into the 'trends' table
  6. Prints progress throughout
"""

import os
import sys
import re
from collections import defaultdict

# Add project root to path so we can import config and the trend extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

from supabase import create_client, Client

# Re-use the same entity extraction logic from the trend extractor agent
from agents.trend_extractor import extract_entities

# ---------------------------------------------------------------------------
# Core backfill logic
# ---------------------------------------------------------------------------

def extract_trends_from_articles(publish_date: str, articles: list[dict]) -> list[dict]:
    """
    Given a list of article dicts from Supabase, extract entity trend rows.

    Each article has: audience, title, content, bullets (jsonb),
                      themes_used (jsonb), insight_used (text)
    """
    # Accumulator: (topic, theme_name) -> mention_count
    trend_map: dict[tuple[str, str], int] = defaultdict(int)

    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")
        insight = article.get("insight_used", "")
        audience = article.get("audience", "general")

        # Combine bullets into a single string
        bullets = article.get("bullets", [])
        if isinstance(bullets, list):
            bullets_text = " ".join(str(b) for b in bullets)
        else:
            bullets_text = str(bullets) if bullets else ""

        # Combine themes_used into searchable text
        themes_used = article.get("themes_used", [])
        if isinstance(themes_used, list):
            themes_text = " ".join(str(t) for t in themes_used)
        else:
            themes_text = str(themes_used) if themes_used else ""

        # Build combined text blob for entity extraction
        combined = f"{title} {content} {insight} {bullets_text} {themes_text}"
        entities = extract_entities(combined)

        # Determine a theme_name from the article's themes_used or audience
        if themes_used and isinstance(themes_used, list) and len(themes_used) > 0:
            # Use the first theme as the canonical theme_name
            primary_theme = str(themes_used[0])
        else:
            primary_theme = f"Article ({audience})"

        for entity, count in entities.items():
            key = (entity, primary_theme)
            trend_map[key] += count

    # Flatten to row dicts
    rows = []
    for (topic, theme_name), mention_count in trend_map.items():
        rows.append({
            "date": publish_date,
            "topic": topic,
            "mention_count": mention_count,
            "confidence": "historical",  # Mark backfilled data distinctly
            "trend": "historical",
            "theme_name": theme_name,
        })

    return rows


def run_backfill():
    """Main backfill execution."""
    print("=" * 60)
    print("  TREND BACKFILL SCRIPT")
    print("  Scanning all historical newsletters for AI entity trends")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[BACKFILL] ERROR: Missing Supabase credentials.")
        print("           Set SUPABASE_URL and SUPABASE_KEY in config.py or env vars.")
        sys.exit(1)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Step 1: Fetch all newsletters ordered by date
    print("\n[1/4] Fetching all newsletters...")
    try:
        response = supabase.table("newsletters") \
            .select("id, publish_date") \
            .order("publish_date", desc=False) \
            .execute()
        newsletters = response.data
    except Exception as e:
        print(f"[BACKFILL] ERROR: Failed to fetch newsletters: {e}")
        sys.exit(1)

    if not newsletters:
        print("[BACKFILL] No newsletters found in the database. Nothing to backfill.")
        return

    print(f"[BACKFILL] Found {len(newsletters)} newsletters to process.")

    # Step 2: Process each newsletter
    total_trends_inserted = 0
    errors = 0

    for i, newsletter in enumerate(newsletters, 1):
        nl_id = newsletter["id"]
        pub_date = newsletter["publish_date"]

        print(f"\n[2/4] Processing newsletter {i}/{len(newsletters)}: {pub_date} (ID: {nl_id[:8]}...)")

        # Fetch articles for this newsletter
        try:
            art_response = supabase.table("articles") \
                .select("title, content, audience, bullets, themes_used, insight_used") \
                .eq("newsletter_id", nl_id) \
                .execute()
            articles = art_response.data
        except Exception as e:
            print(f"       ERROR fetching articles: {e}")
            errors += 1
            continue

        if not articles:
            print(f"       No articles found – skipping.")
            continue

        print(f"       Found {len(articles)} articles.")

        # Extract trends
        trend_rows = extract_trends_from_articles(pub_date, articles)

        if not trend_rows:
            print(f"       No entities detected – skipping.")
            continue

        print(f"       Extracted {len(trend_rows)} trend records.")

        # Step 3: Delete existing trends for this date (idempotent re-runs)
        try:
            supabase.table("trends").delete().eq("date", pub_date).execute()
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "does not exist" in error_msg.lower():
                print("\n[BACKFILL] FATAL: 'trends' table does not exist.")
                print("           Please create it first with this schema:")
                print("             date       text")
                print("             topic      text")
                print("             mention_count  int4")
                print("             confidence text")
                print("             trend      text")
                print("             theme_name text")
                sys.exit(1)
            else:
                print(f"       WARNING: Failed to clear old trends: {e}")

        # Step 4: Insert new trends
        try:
            supabase.table("trends").insert(trend_rows).execute()
            total_trends_inserted += len(trend_rows)
            print(f"       [OK] Inserted {len(trend_rows)} trends.")
        except Exception as e:
            print(f"       ERROR inserting trends: {e}")
            errors += 1

    # Final summary
    print("\n" + "=" * 60)
    print("  BACKFILL COMPLETE")
    print(f"  Newsletters processed:  {len(newsletters)}")
    print(f"  Total trends inserted:  {total_trends_inserted}")
    print(f"  Errors encountered:     {errors}")
    print("=" * 60)


if __name__ == "__main__":
    run_backfill()
