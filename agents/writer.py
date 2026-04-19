"""
Writer Agent V1
Purpose: Transforms structured intelligence into audience-specific articles.
"""
import os
import sys
import json
import time
import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import GEMINI_API_KEY, MODEL_NAME
    api_key = GEMINI_API_KEY
    model_name = MODEL_NAME
except ImportError:
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = "gemini-2.5-flash"

def deterministic_fallback(parsed_insights, error_msg):
    # STEP 9: FALLBACK PROTOCOL
    print(f"\n[!] WRITER_FALLBACK_USED | {time.time()} | API failure: {error_msg}")
    
    fallback_insight = "AI innovation continues to accelerate across all verticals."
    if parsed_insights.get("top_insights"):
        fallback_insight = parsed_insights["top_insights"][0]
        
    template = {
        "date": parsed_insights.get("date", "Unknown"),
        "model_used": "NONE-FALLBACK",
        "articles": [
            {
               "audience": "general",
               "title": "Daily AI Intelligence Summary",
               "content": f"The AI ecosystem continues to rapidly shift. Today's core signal indicates: {fallback_insight}\n\nWe tracked {parsed_insights.get('total_after_filter', 0)} major developments today. Expect ongoing momentum in this sector as infrastructure and models evolve dynamically.",
               "themes_used": [t.get("name") for t in parsed_insights.get("themes", [])][:1],
               "insight_used": fallback_insight
            }
        ],
        "skipped_audiences": ["devs", "students", "business"],
        "skip_reasons": {
            "devs": "API Fail - fallback executed",
            "students": "API Fail - fallback executed",
            "business": "API Fail - fallback executed"
        },
        "top_insights": parsed_insights.get("top_insights", [fallback_insight]),
        "fallback_used": True
    }
    return template

def run_writer():
    print("\n--- Writer Agent Execution (V1) ---")
    
    if not api_key:
        print("[!] ERROR: GEMINI_API_KEY environment variable not found.")
        print("[!] Skipping Writer Agent execution.")
        return
        
    insights_path = os.path.join("data", "processed", "insights.json")
    if not os.path.exists(insights_path):
        print(f"[!] No insights found at {insights_path}. Scout/Analyst must run first.")
        return
        
    with open(insights_path, "r", encoding="utf-8") as f:
        insights_data = f.read()
        try:
            parsed_insights = json.loads(insights_data)
        except:
            parsed_insights = {}

    with open(os.path.join("prompts", "writer_prompt.txt"), "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    full_payload = f"{system_prompt}\n\n### RAW JSON INPUT:\n{insights_data}"

    genai.configure(api_key=api_key)
    
    # Per instructions STEP 8
    generation_config = {
        "temperature": 0.6,
        "top_p": 0.9,
        "response_mime_type": "application/json"
    }
    
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )
    
    final_output = None
    
    # Retry Loop (Step 9)
    for attempt in range(2):
        try:
            print(f"Executing LLM generation (Attempt {attempt+1}/2)...")
            response = model.generate_content(full_payload)
            json_text = response.text
            
            # Sanitization if MimeType gets ignored
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()
                
            final_output = json.loads(json_text)
            print("Generation successful and JSON validated.")
            break 
            
        except Exception as e:
            print(f"[!] API/Parsing Error on Attempt {attempt+1}: {e}")
            if attempt == 0:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
            else:
                final_output = deterministic_fallback(parsed_insights, str(e))
                
    out_target = os.path.join("data", "processed", "newsletter.json")
    os.makedirs(os.path.dirname(out_target), exist_ok=True)
    
    with open(out_target, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
        
    print("\n=== WRITER V1 OUTPUT STATS ===")
    print(f"Fallback Used     : {final_output.get('fallback_used', False)}")
    print(f"Articles Written  : {len(final_output.get('articles', []))}")
    print(f"Audiences Skipped : {len(final_output.get('skipped_audiences', []))}")
    print("===============================\n")

if __name__ == "__main__":
    run_writer()
