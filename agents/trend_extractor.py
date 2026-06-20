"""
Trend Extractor Agent
Purpose: Extracts topic/entity trends from the Analyst output and stores them
         in the Supabase 'trends' table for historical tracking and dashboarding.

Reads: data/processed/insights.json (Analyst output)
Writes: Supabase 'trends' table
Schema: date (text), topic (text), mention_count (int), confidence (text),
        trend (text), theme_name (text)
"""

import os
import sys
import json
import re
from collections import defaultdict

# Add parent directory so config imports work from any cwd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Smart Entity Extraction – curated lists of known AI ecosystem entities
# ---------------------------------------------------------------------------

# Major AI companies and labs
AI_COMPANIES = [
    "OpenAI", "Google", "Anthropic", "Meta", "Microsoft", "NVIDIA",
    "Mistral", "Cohere", "DeepMind", "Apple", "Amazon", "AWS",
    "Hugging Face", "HuggingFace", "Stability AI", "StabilityAI",
    "Inflection", "xAI", "Databricks", "Snowflake", "Scale AI",
    "Perplexity", "Adept", "Character AI", "Midjourney", "Runway",
    "Adobe", "Salesforce", "IBM", "Intel", "AMD", "Qualcomm",
    "Samsung", "Baidu", "Alibaba", "Tencent", "ByteDance",
    "Cerebras", "SambaNova", "Groq", "Together AI", "Anyscale",
    "Lightmatter", "Clarifai", "NeoCognition", "GDEP Advance",
    "WPP", "Hearst", "Hyatt", "Yelp",
]

# Model families and specific model names
AI_TECHNOLOGIES = [
    "GPT", "GPT-4", "GPT-4o", "GPT-5", "ChatGPT",
    "Gemini", "Gemma",
    "Claude", "Mythos",
    "LLaMA", "Llama", "Llama 3", "Llama 4",
    "Mixtral", "Mistral Large",
    "Phi", "Phi-3",
    "DALL-E", "DALL·E", "Sora", "Veo",
    "Stable Diffusion", "Flux",
    "Command R", "Command R+",
    "Grok",
    "Copilot", "GitHub Copilot",
    "Transformer", "Diffusion Model",
    "BERT", "T5", "PaLM",
]

# Concepts, paradigms, and technique categories
AI_CONCEPTS = [
    "AI Agents", "AI Agent", "Agentic AI",
    "RAG", "Retrieval Augmented Generation",
    "Fine-tuning", "Fine-Tuning", "RLHF",
    "Prompt Engineering", "Prompt Injection",
    "AI Governance", "AI Safety", "AI Ethics", "AI Regulation",
    "Multimodal", "Multi-modal",
    "Computer Vision", "NLP", "Natural Language Processing",
    "Reinforcement Learning", "Deep Learning", "Machine Learning",
    "LLM", "Large Language Model",
    "Foundation Model", "Foundation Models",
    "Edge AI", "On-device AI",
    "Generative AI", "GenAI",
    "AI Infrastructure", "AI Hardware",
    "Quantum Computing", "Quantum AI",
    "Autonomous AI", "AI Automation",
    "AI Security", "Deepfake", "Deepfakes",
    "Text-to-Image", "Text-to-Video",
    "AI Coding", "Code Generation",
    "Robotics", "Embodied AI",
    "Synthetic Data",
    "Vector Database", "Embeddings",
    "AI Manufacturing", "AI Ops", "MLOps",
]

# Compile everything into a single lookup: canonical_name -> regex pattern
# We use case-insensitive matching for robustness
_ENTITY_PATTERNS: list[tuple[str, re.Pattern]] = []

def _build_patterns():
    """Build compiled regex patterns once at import time."""
    if _ENTITY_PATTERNS:
        return
    seen = set()
    for entity_list in (AI_COMPANIES, AI_TECHNOLOGIES, AI_CONCEPTS):
        for entity in entity_list:
            canonical = entity.strip()
            if canonical.lower() in seen:
                continue
            seen.add(canonical.lower())
            # Escape for regex, then build a word-boundary pattern
            escaped = re.escape(canonical)
            pattern = re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)
            _ENTITY_PATTERNS.append((canonical, pattern))

_build_patterns()


def extract_entities(text: str) -> dict[str, int]:
    """
    Scan a block of text for known AI entities.
    Returns {canonical_name: mention_count}.
    """
    counts: dict[str, int] = defaultdict(int)
    for canonical, pattern in _ENTITY_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            counts[canonical] += len(matches)
    return dict(counts)


def extract_trends_from_insights(insights_data: dict) -> list[dict]:
    """
    Walk the Analyst output and produce a flat list of trend records.

    Strategy:
      1. For each theme, concatenate its name + description + developments
         into one text blob and extract entities from it.
      2. Each entity found becomes a trend row, inheriting the theme's
         confidence and trend values.
      3. Also scan top_insights and signal_vs_noise for extra mentions.
    """
    date = insights_data.get("date", "unknown")
    themes = insights_data.get("themes", [])

    # Accumulator: (topic, theme_name) -> {count, confidence, trend}
    trend_map: dict[tuple[str, str], dict] = {}

    # --- Pass 1: Extract from each theme ---
    for theme in themes:
        theme_name = theme.get("name", "Unknown Theme")
        confidence = theme.get("confidence", "unknown")
        trend_dir = theme.get("trend", "unknown")

        # Build a combined text blob for this theme
        parts = [
            theme_name,
            theme.get("description", ""),
            theme.get("why_it_matters", ""),
        ]
        for dev in theme.get("developments", []):
            parts.append(dev)

        combined_text = " ".join(parts)
        entities = extract_entities(combined_text)

        for entity, count in entities.items():
            key = (entity, theme_name)
            if key in trend_map:
                trend_map[key]["mention_count"] += count
            else:
                trend_map[key] = {
                    "mention_count": count,
                    "confidence": confidence,
                    "trend": trend_dir,
                }

    # --- Pass 2: Scan top_insights for extra signal ---
    top_insights = insights_data.get("top_insights", [])
    insight_text = " ".join(top_insights) if top_insights else ""
    if insight_text:
        extra_entities = extract_entities(insight_text)
        for entity, count in extra_entities.items():
            # Attribute to a generic "Cross-Theme Insights" bucket
            key = (entity, "Cross-Theme Insights")
            if key in trend_map:
                trend_map[key]["mention_count"] += count
            else:
                trend_map[key] = {
                    "mention_count": count,
                    "confidence": "medium",
                    "trend": "stable",
                }

    # --- Pass 3: Scan signal_vs_noise headlines ---
    svn = insights_data.get("signal_vs_noise", {})
    headline_texts = " ".join(
        svn.get("strong_signal", []) + svn.get("weak_signal", [])
    )
    if headline_texts:
        extra_entities = extract_entities(headline_texts)
        for entity, count in extra_entities.items():
            key = (entity, "Signal Headlines")
            if key in trend_map:
                trend_map[key]["mention_count"] += count
            else:
                trend_map[key] = {
                    "mention_count": count,
                    "confidence": "low",
                    "trend": "stable",
                }

    # --- Flatten to list of row dicts ---
    rows = []
    for (topic, theme_name), meta in trend_map.items():
        rows.append({
            "date": date,
            "topic": topic,
            "mention_count": meta["mention_count"],
            "confidence": meta["confidence"],
            "trend": meta["trend"],
            "theme_name": theme_name,
        })

    return rows


def run_trend_extractor():
    """
    Main entry point – reads insights.json, extracts trends, and upserts
    into the Supabase 'trends' table.
    """
    print("\n--- Trend Extractor Agent Execution ---")

    # 1. Validate Supabase credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[TREND] ERROR: Missing Supabase credentials. Skipping.")
        return

    # 2. Load Analyst output
    insights_path = os.path.join("data", "processed", "insights.json")
    if not os.path.exists(insights_path):
        print(f"[TREND] WARNING: {insights_path} not found. Nothing to extract.")
        return

    with open(insights_path, "r", encoding="utf-8") as f:
        insights_data = json.load(f)

    # 3. Extract trend rows
    trend_rows = extract_trends_from_insights(insights_data)

    if not trend_rows:
        print("[TREND] No entities detected in today's insights. Skipping insert.")
        return

    print(f"[TREND] Extracted {len(trend_rows)} trend records from insights.")

    # 4. Connect to Supabase and insert
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    publish_date = insights_data.get("date", "unknown")

    try:
        # Delete any existing trends for this date to make re-runs idempotent
        supabase.table("trends").delete().eq("date", publish_date).execute()

        # Batch insert all trend rows
        supabase.table("trends").insert(trend_rows).execute()

        print(f"[TREND] SUCCESS: Inserted {len(trend_rows)} trends for {publish_date}")

    except Exception as e:
        error_msg = str(e)
        # Gracefully handle missing table (Supabase returns 404 / relation does not exist)
        if "404" in error_msg or "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            print("[TREND] WARNING: 'trends' table does not exist in Supabase.")
            print("[TREND] Please create it with columns: date (text), topic (text),")
            print("        mention_count (int4), confidence (text), trend (text), theme_name (text)")
            print("[TREND] Skipping insert – no data was lost.")
        else:
            print(f"[TREND] ERROR: Failed to insert trends: {e}")

    # 5. Summary
    print("\n=== TREND EXTRACTOR OUTPUT ===")
    unique_topics = set(r["topic"] for r in trend_rows)
    print(f"  Unique Topics Detected: {len(unique_topics)}")
    for topic in sorted(unique_topics):
        total = sum(r["mention_count"] for r in trend_rows if r["topic"] == topic)
        print(f"    • {topic} ({total} mentions)")
    print("==============================\n")


if __name__ == "__main__":
    run_trend_extractor()
