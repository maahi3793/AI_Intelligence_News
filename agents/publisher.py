import os
import sys
import json
from datetime import datetime, timezone

# Import official Supabase client
from supabase import create_client, Client

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    print("[PUBLISHER] ERROR: Failed: Could not load SUPABASE_URL or SUPABASE_KEY from config.py")
    sys.exit(1)

def load_json(filepath: str) -> dict:
    if not os.path.exists(filepath):
        print(f"[PUBLISHER] ERROR: Failed: File not found at {filepath}")
        sys.exit(1)
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[PUBLISHER] ERROR: Failed: Invalid JSON format: {e}")
        sys.exit(1)

def validate_data(data: dict) -> None:
    required_root_keys = ["date", "articles"]
    for key in required_root_keys:
        if key not in data:
            print(f"[PUBLISHER] ERROR: Failed: Missing required root key '{key}'")
            sys.exit(1)
            
    if not isinstance(data["articles"], list) or len(data["articles"]) < 2:
        print("[PUBLISHER] ERROR: Failed: Must contain at least 2 articles")
        sys.exit(1)
        
    for i, article in enumerate(data["articles"]):
        required_article_keys = ["audience", "title", "content", "insight_used"]
        for key in required_article_keys:
            if key not in article:
                print(f"[PUBLISHER] ERROR: Failed: Article {i} missing required key '{key}'")
                sys.exit(1)

def check_exists(supabase: Client, publish_date: str) -> bool:
    try:
        response = supabase.table("newsletters").select("id").eq("publish_date", publish_date).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"[PUBLISHER] ERROR: Failed during idempotency check: {e}")
        sys.exit(1)

def insert_newsletter(supabase: Client, data: dict) -> str:
    payload = {
        "publish_date": data["date"],
        "model_used": data.get("model_used", "unknown"),
        "fallback_used": data.get("fallback_used", False)
    }
    response = supabase.table("newsletters").insert(payload).execute()
    return response.data[0]["id"]

def insert_articles(supabase: Client, newsletter_id: str, articles: list) -> None:
    payload = []
    for art in articles:
        payload.append({
            "newsletter_id": newsletter_id,
            "audience": art["audience"],
            "title": art["title"],
            "content": art["content"],
            "bullets": art.get("bullets", []),
            "themes_used": art.get("themes_used", []),
            "insight_used": art["insight_used"]
        })
    supabase.table("articles").insert(payload).execute()

def insert_insights(supabase: Client, newsletter_id: str, top_insights: list) -> None:
    if not top_insights:
        return
        
    payload = []
    for insight in top_insights:
        payload.append({
            "newsletter_id": newsletter_id,
            "insight_text": insight
        })
    supabase.table("insights").insert(payload).execute()

def run_publisher():
    """Main execution sequence"""
    print("\n--- Publisher Agent Execution (Phase 1B) ---")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[PUBLISHER] ERROR: Failed: Missing Supabase credentials in config.py")
        sys.exit(1)
        
    # Init client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Load Data
    json_path = os.path.join("data", "processed", "newsletter.json")
    data = load_json(json_path)
    
    # 2. Validate Structure
    validate_data(data)
    publish_date = data["date"]
    
    # 3. Check Idempotency (Converted to Upsert Logic v2)
    existing_id = None
    try:
        response = supabase.table("newsletters").select("id").eq("publish_date", publish_date).execute()
        if response.data:
            existing_id = response.data[0]["id"]
            print(f"[PUBLISHER] UPDATING: Date {publish_date} exists (ID: {existing_id}). Purging old records for fresh sync...")
            # Delete triggers cascade on articles/insights if enabled, or we let the insert handle the fresh state.
            supabase.table("newsletters").delete().eq("id", existing_id).execute()
    except Exception as e:
        print(f"[PUBLISHER] WARNING: Idempotency check/purge failed: {e}")
        
    newsletter_id = None
    
    # 4 & 5. Insert Flow with Python Rollback
    try:
        # Step 1
        newsletter_id = insert_newsletter(supabase, data)
        
        # Step 2
        insert_articles(supabase, newsletter_id, data["articles"])
        
        # Step 3
        insert_insights(supabase, newsletter_id, data.get("top_insights", []))
        
        # 6. Logging Success
        print(f"[PUBLISHER] SUCCESS: Published {publish_date} ({len(data['articles'])} articles)")
        
    except Exception as e:
        # Rollback via Delete Cascade
        if newsletter_id is not None:
            try:
                supabase.table("newsletters").delete().eq("id", newsletter_id).execute()
            except Exception as rollback_err:
                print(f"[PUBLISHER] FATAL ERROR: Rollback failed: {rollback_err}")
                
        print(f"[PUBLISHER] ERROR: Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_publisher()
