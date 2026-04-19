"""
Analyst Agent V1
Purpose: Transforms structured AI news input into high-signal intelligence formats via LLM.
"""
import os
import sys
import json
import google.generativeai as genai

# add root to sys path to import config easily just in case
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import GEMINI_API_KEY, MODEL_NAME
    api_key = GEMINI_API_KEY
    model_name = MODEL_NAME
except ImportError:
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = "gemini-2.5-flash"

def run_analyst():
    print("\n--- Analyst Agent Execution (Phase 3) ---")
    
    if not api_key:
        print("[!] ERROR: GEMINI_API_KEY environment variable not found.")
        print("[!] Skipping Analyst Agent. Please set your Gemini API key to proceed.")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json", "temperature": 0.15}
        )
        
        # 1. Load inputs
        raw_path = os.path.join("data", "raw", "today.json")
        prev_path = os.path.join("data", "processed", "insights.json")
        prompt_path = os.path.join("prompts", "analyst_prompt.txt")
        
        with open(raw_path, "r", encoding="utf-8") as f:
            current_raw_data = f.read()
            
        previous_data = "{}"
        if os.path.exists(prev_path):
            with open(prev_path, "r", encoding="utf-8") as f:
                previous_data = f.read()
                
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
            
        # 2. Assemble Dual-Context Prompt
        full_payload = f"{system_prompt}\n\n### CURRENT RUN (today's articles):\n{current_raw_data}\n\n### PREVIOUS RUN (yesterday's analysis):\n{previous_data}"
        
        print("Transmitting deterministic temporal payload to Gemini LLM Engine...")
        response = model.generate_content(full_payload)
        
        # 3. Validation & Parsing
        json_output = response.text
        # Stripping arbitrary markdown if MIME parameter falls back randomly
        if json_output.startswith("```json"):
             json_output = json_output[7:-3].strip()
        elif json_output.startswith("```"):
             json_output = json_output[3:-3].strip()
             
        parsed_json = json.loads(json_output)
        
        # 4. Storage Write-out
        out_target = os.path.join("data", "processed", "insights.json")
        os.makedirs(os.path.dirname(out_target), exist_ok=True)
        
        with open(out_target, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2)
            
        total_remaining = parsed_json.get("total_after_filter", 0)
        themes_count = len(parsed_json.get("themes", []))
        insights_count = len(parsed_json.get("top_insights", []))
        
        print("\n=== ANALYST V1 OUTPUT STATS ===")
        print(f"Items Substantially Filtered In: {total_remaining}")
        print(f"Major Dominant Themes Built:      {themes_count}")
        print(f"Forward-Looking Insights Found:   {insights_count}")
        print("===============================\n")
        
    except Exception as e:
        print(f"\n[!] Analyst Agent Failed during reasoning execution:\n    {e}")

if __name__ == "__main__":
    run_analyst()
