"""
Create the 'trends' table in Supabase.
Run this ONCE to set up the schema.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test insert to check if table exists
print("Testing trends table...")
try:
    test = supabase.table("trends").select("*").limit(1).execute()
    print(f"✅ Trends table exists! ({len(test.data)} rows found)")
except Exception as e:
    error_msg = str(e)
    if "relation" in error_msg and "does not exist" in error_msg:
        print("❌ Trends table does NOT exist.")
        print()
        print("Please create it in Supabase SQL Editor with:")
        print()
        print("""
CREATE TABLE trends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date TEXT NOT NULL,
    topic TEXT NOT NULL,
    mention_count INTEGER DEFAULT 1,
    confidence TEXT DEFAULT 'unknown',
    trend TEXT DEFAULT 'stable',
    theme_name TEXT DEFAULT 'Unknown',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast date-based queries
CREATE INDEX idx_trends_date ON trends(date);

-- Index for topic aggregation
CREATE INDEX idx_trends_topic ON trends(topic);

-- Enable RLS but allow public read access (for frontend)
ALTER TABLE trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access" ON trends FOR SELECT USING (true);
CREATE POLICY "Allow service role insert" ON trends FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role delete" ON trends FOR DELETE USING (true);
""")
    else:
        print(f"Error: {e}")
