"""
Scout Agent
Purpose: Fully Deterministic V4.1 Scraper matching exact rule mappings.
"""
import feedparser
import json
import datetime
import os
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse
import re
import html
import math
from difflib import SequenceMatcher

# ----------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------
SCORE_THRESHOLD        = 4      
FALLBACK_THRESHOLD     = 2      
MAX_OUTPUT             = 20
MIN_OUTPUT             = 5
REDDIT_MAX_PCT         = 0.20   
TEXT_WINDOW_CHARS      = 300    
DATE_WINDOW_HOURS      = 48     
FALLBACK_WINDOW_HOURS  = 72     

GNEWS_API_KEY = "3eb2aa32e0414793285c08e5f5c2cd9c"
CURRENTS_API_KEY = "xlejpiA7TtRidCMPy5m6Dsv09WMCbnwS-CbcVWPCJJ6I-gPV"
NEWS_API_KEY = "9a1818ed317f4f5d95b35e9e40526f6b"

RSS_FEEDS = [
    "https://deepmind.google/blog/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.anthropic.com/news/rss.xml",
    "https://www.anthropic.com/engineering/rss.xml",
    "https://openai.com/news/rss.xml",
    "https://nvidianews.nvidia.com/rss.xml",
    "https://developer.nvidia.com/blog/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://huggingface.co/blog/feed.xml",
    "https://venturebeat.com/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://simonwillison.net/atom/everything/",
    "https://www.interconnects.ai/feed",
    "https://newsletter.theaiedge.io/feed",
    "https://indianexpress.com/section/technology/artificial-intelligence/feed/",
    "https://aifornewsroom.in/api/rss/all",
    "https://economictimes.indiatimes.com/tech/rss",
    "https://www.moneycontrol.com/rss/tech.xml",
    "https://www.indiatoday.in/rss/1206688",
    "https://www.androidpolice.com/feed/",
    "https://www.androidauthority.com/feed/",
    "https://news.smol.ai/rss.xml",
]

TIER1_DOMAINS = [
    "arxiv.org", "huggingface.co", "openai.com", "deepmind.google",
    "anthropic.com", "ai.google", "research.google", "blog.google",
    "meta.com/research", "mistral.ai", "cohere.com", "stability.ai",
    "together.ai", "ai.meta.com"
]

TIER2_DOMAINS = [
    "techcrunch.com", "venturebeat.com", "wired.com", "arstechnica.com",
    "thenextweb.com", "theregister.com", "zdnet.com", "ieee.org",
    "technologyreview.com", "nature.com", "science.org", 
    "androidpolice.com", "androidauthority.com", "smol.ai", "cnet.com"
]

AGGREGATOR_DOMAINS = [
    "buzzfeed.com", "msn.com", "yahoo.com", "flipboard.com",
    "feedly.com", "alltop.com", "techmeme.com"
]

AI_CORE_TERMS = [
  "ai", "artificial intelligence", "machine learning", "llm",
  "large language model", "neural network", "deep learning",
  "transformer", "inference", "training", "fine-tuning",
  "multimodal", "generative", "foundation model", "embedding",
  "reinforcement learning", "diffusion model", "agent"
]

REJECT_TERMS = [
  "windows update", "ios update", "android update", "chromeos",
  "firmware update", "graphics card review", "laptop review",
  "phone review", "gaming news", "esports", "game release",
  "ransomware", "phishing", "malware", "data breach",
  "stock market", "earnings report", "quarterly results",
  "sports", "election", "politics", "celebrity"
]

CREDIBILITY_BLACKLIST = [
    'rt.com', 'tass.ru', 'xinhua.net', 'cgtn.com',
    'sputniknews.com', 'sputnik.com', 'globaltimes.cn',
    'people.cn', 'chinadaily.com.cn'
]

URL_BLACKLIST_PATTERNS = [
    '/academy/', '/learn/', '/docs/', '/help/',
    '/tutorial/', '/course/', '/education/',
    '/support/', '/faq/'
]

# Precompiled word-boundary patterns for AI_CORE_TERMS.
# Using `term in text` matches substrings — "ai" hits "said", "Isaiah",
# "available", "detail", etc. Word boundaries fix this entirely.
_AI_TERM_PATTERNS = [
    re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
    for term in AI_CORE_TERMS
]

def _count_ai_terms(text):
    """Count how many distinct AI_CORE_TERMS appear as whole words in text."""
    return sum(1 for p in _AI_TERM_PATTERNS if p.search(text))

def strip_html(text):
    if not text: return ""
    clean = re.sub(r'<[^>]+>', ' ', html.unescape(text))
    return re.sub(r'\s+', ' ', clean).strip()

def get_domain(url):
    try:
        netloc = urlparse(url).netloc
        if netloc.startswith("www."): netloc = netloc[4:]
        return netloc
    except:
        return ""

def parse_utc(timestamp_str, struct_time=None):
    try:
        if struct_time:
            return datetime.datetime.fromtimestamp(time.mktime(struct_time), datetime.timezone.utc)
        elif timestamp_str:
            dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.replace(tzinfo=datetime.timezone.utc)
    except: pass
    
    # Fallback heuristic since API timestamps usually follow ISO length
    if timestamp_str and len(timestamp_str) >= 10:
        try:
             # simple fallback date bounding to today
             dt = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
             if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
             return dt
        except: pass
        
    return datetime.datetime.now(datetime.timezone.utc)

def calculate_priority_tier(domain, is_api, url):
    if any(domain == d or domain.endswith("."+d) for d in TIER1_DOMAINS):
        return 3, "TIER1"
    if any(domain == d or domain.endswith("."+d) for d in TIER2_DOMAINS):
        return 2, "TIER2"
    
    if "reddit.com/r/MachineLearning" in url or "reddit.com/r/LocalLLaMA" in url or "reddit.com/r/artificial" in url:
        return 1, "REDDIT"
        
    if is_api:
        return 1, "API"
        
    return 0, "DEFAULT"

class ScoutEngine:
    def __init__(self):
        self.articles = []
        
        self.stats = {
            "fetched_total": 0,
            "dropped_no_ai_context": 0,
            "dropped_zero_ai_context": 0,
            "dropped_credibility_blacklist": 0,
            "dropped_url_pattern": 0,
            "dropped_hard_reject": 0,
            "dropped_below_threshold": 0,
            "dropped_dedup": 0,
            "dropped_reddit_cap": 0,
            "fallback_threshold_triggered": False,
            "fallback_date_window_triggered": False,
            "fallback_tier1_force_triggered": False,
            "final_count": 0
        }
        self.dedup_logs = []

    def fetch_all(self):
        # RSS
        for url in RSS_FEEDS:
            try:
                feed = feedparser.parse(url)
                if feed and hasattr(feed, 'entries'):
                    self.stats["fetched_total"] += len(feed.entries)
                    for e in feed.entries:
                        title = strip_html(getattr(e, "title", ""))
                        link = getattr(e, "link", "")
                        if not title or not link: continue
                        summary = strip_html(getattr(e, "summary", "") or getattr(e, "description", ""))
                        dt = parse_utc(getattr(e, "published", ""), getattr(e, "published_parsed", None))
                        self._ingest(title, summary, link, dt, False)
            except: pass

        # GNEWS
        try:
            req = urllib.request.Request(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={GNEWS_API_KEY}", headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode()).get("articles", [])
                self.stats["fetched_total"] += len(payload)
                for a in payload:
                    title = strip_html(a.get("title", ""))
                    link = a.get("url", "")
                    if not title or not link: continue
                    summary = strip_html(a.get("description", ""))
                    dt = parse_utc(a.get("publishedAt", ""))
        except: pass

        # CURRENTS
        try:
            req = urllib.request.Request(f"https://api.currentsapi.services/v1/latest-news?language=en&apiKey={CURRENTS_API_KEY}", headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode()).get("news", [])
                self.stats["fetched_total"] += len(payload)
                for a in payload:
                    title = strip_html(a.get("title", ""))
                    link = a.get("url", "")
                    if not title or not link: continue
                    summary = strip_html(a.get("description", ""))
                    dt = parse_utc(a.get("published", ""))
                    self._ingest(title, summary, link, dt, True)
        except: pass

        # NEWS API (Targeting CNET AI Atlas)
        try:
            query = "AI Atlas"
            domains = "cnet.com"
            url = f"https://newsapi.org/v2/everything?q={query.replace(' ', '+')}&domains={domains}&apiKey={NEWS_API_KEY}"
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode()).get("articles", [])
                self.stats["fetched_total"] += len(payload)
                for a in payload:
                    title = strip_html(a.get("title", ""))
                    link = a.get("url", "")
                    if not title or not link: continue
                    summary = strip_html(a.get("description", "") or a.get("content", ""))
                    dt = parse_utc(a.get("publishedAt", ""))
                    self._ingest(title, summary, link, dt, True)
        except: pass

    def _ingest(self, title, summary, url, dt, is_api):
        domain = get_domain(url)
        score_text = (title + " " + summary[:TEXT_WINDOW_CHARS]).lower()

        # Credibility blacklist — drop state media before any scoring
        if domain in CREDIBILITY_BLACKLIST:
            self.stats["dropped_credibility_blacklist"] += 1
            return

        # URL pattern blacklist — drop tutorial/marketing/docs pages
        if any(pattern in url.lower() for pattern in URL_BLACKLIST_PATTERNS):
            self.stats["dropped_url_pattern"] += 1
            return

        # Base stats
        ptier, stype = calculate_priority_tier(domain, is_api, url)

        ctx_count = _count_ai_terms(score_text)

        # Hard reject if zero AI context — no exceptions for any source tier
        if ctx_count == 0:
            self.stats["dropped_zero_ai_context"] += 1
            return

        reject_override = False
        if any(term in score_text for term in REJECT_TERMS):
            if ctx_count >= 2:
                reject_override = True
            else:
                self.stats["dropped_hard_reject"] += 1
                return

        # Step 5: Reddit Rules
        question_style = False
        high_signal = False
        
        if stype == "REDDIT":
            title_lower = title.lower()
            if any(term in title_lower for term in ["?", "[d]", "[q]", "[discussion]", "help", "how do i", "what is", "anyone else", "looking for"]):
                question_style = True
            if any(term in title_lower for term in ["paper", "github", "benchmark", "release", "dataset", "model", "results", "released", "open source"]):
                high_signal = True
                
            if not high_signal and question_style:
                self.stats["dropped_no_ai_context"] += 1 # Or hard dropped? Logged broadly as rejected
                return

        self.articles.append({
            "title": title,
            "summary": summary[:280],
            "url": url,
            "source_domain": domain,
            "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dt_obj": dt,
            "source_type": stype,
            "priority_tier": ptier,
            "ai_context_count": ctx_count,
            "reject_override": reject_override,
            "score_text": score_text,
            "question_style": question_style,
            "high_signal": high_signal
        })

    def run_pipeline(self):
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        start_of_today = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Time processing
        pool = []
        for a in self.articles:
            if a["dt_obj"] >= start_of_today:
                pool.append(a)
                
        # Primary Filter
        processed = self._process_batch(pool, SCORE_THRESHOLD, now_dt)
        
        # Step 8 Fallback
        if len(processed) < MIN_OUTPUT:
            self.stats["fallback_date_window_triggered"] = True
            fallback_dt = now_dt - datetime.timedelta(hours=FALLBACK_WINDOW_HOURS)
            pool = [a for a in self.articles if a["dt_obj"] >= fallback_dt]
            processed = self._process_batch(pool, SCORE_THRESHOLD, now_dt)
            
        # Step 9 Fallback
        if len(processed) < MIN_OUTPUT:
            self.stats["fallback_threshold_triggered"] = True
            processed = self._process_batch(pool, FALLBACK_THRESHOLD, now_dt)
            
            if len(processed) < MIN_OUTPUT:
                self.stats["fallback_tier1_force_triggered"] = True
                added = 0
                # Sort forcibly by timestamp explicitly
                tier1_force_pool = sorted([a for a in pool if a["priority_tier"] == 3 and a["ai_context_count"] > 0], 
                                          key=lambda x: x["dt_obj"], reverse=True)
                
                # Check what is already in processed
                existing_urls = {p["url"] for p in processed}
                
                for a in tier1_force_pool:
                    if len(processed) >= MIN_OUTPUT and added >= 5: break
                    if a["url"] not in existing_urls:
                        # Append directly bypassing dedup constraints 
                        self._score_item(a, now_dt) 
                        processed.append(a)
                        existing_urls.add(a["url"])
                        added += 1

        self.stats["final_count"] = len(processed)
        return processed

    def _score_item(self, a, now_dt):
        score = 0
        raw = a["score_text"]
        
        # DEPTH
        if any(term in raw for term in ["new model", "model release", "we are releasing", "introducing", "architecture", "transformer", "mixture of experts", "moe", "diffusion", "rag", "retrieval augmented"]): score += 4
        if any(term in raw for term in ["arxiv", "paper", "benchmark", "dataset", "state of the art", "sota", "eval", "ablation"]): score += 4
        if any(term in raw for term in ["training run", "pretraining", "fine-tuning", "rlhf", "dpo", "inference speed", "quantization", "tokens per second", "flops", "compute"]): score += 3
        if any(term in raw for term in ["api update", "new feature", "plugin", "integration", "now available", "launched", "rolled out"]): score += 2
        if any(term in raw for term in ["funding", "raises", "series", "acquisition", "valued at", "investment"]): score += 2
        if any(term in raw for term in ["openai", "anthropic", "deepmind", "google ai", "meta ai", "mistral", "nvidia", "hugging face"]): score += 2
        if any(term in raw for term in ["according to", "report", "analysis", "suggests", "researchers found", "study"]): score += 1
        
        hours_ago = (now_dt - a["dt_obj"]).total_seconds() / 3600.0
        if 0 <= hours_ago <= 6: score += 1
        
        # PENALTY
        if any(term in raw for term in ["gaming", "esports", "gpu review", "benchmark for gaming", "phishing", "malware", "ransomware", "firmware"]):
            if a["ai_context_count"] < 2: score -= 3
            
        if _count_ai_terms(a["title"]) == 0: score -= 2
        if any(a["source_domain"] == d for d in AGGREGATOR_DOMAINS): score -= 2
        
        if a["source_type"] == "REDDIT" and a["question_style"]: score -= 2
        
        # Clamp
        a["relevance_score"] = max(0, min(10, score))
        a["final_score"] = a["relevance_score"] + a["priority_tier"]
        
    def _process_batch(self, batch_pool, threshold, now_dt):
        passing = []
        for a in batch_pool:
            self._score_item(a, now_dt)
            if a["relevance_score"] >= threshold:
                passing.append(a)
            else:
                self.stats["dropped_below_threshold"] += 1
                
        # Tier logic mapped directly
        def tiebreaker(item):
            stype = {"TIER1": 4, "TIER2": 3, "API": 2, "REDDIT": 1, "DEFAULT": 0}.get(item["source_type"], 0)
            return (item["final_score"], stype, item["dt_obj"])

        passing.sort(key=tiebreaker, reverse=True)
        
        # Deduplication
        deduped = []
        for art in passing:
            norm_title = re.sub(r'[^a-z0-9 ]', '', art["title"].lower())
            norm_title = re.sub(r'\s+', ' ', norm_title).strip()
            art["_norm"] = norm_title
            
            is_dup = False
            for existing in deduped:
                # 6+ consecutive words match
                art_words = art["_norm"].split()

                consecutive = False
                for i in range(len(art_words) - 5):
                    chunk = " ".join(art_words[i:i+6])
                    if chunk in existing["_norm"]:
                        consecutive = True
                        break
                        
                sm = SequenceMatcher(None, art["_norm"], existing["_norm"]).ratio()
                
                if consecutive or sm >= 0.85:
                    is_dup = True
                    # existing is always >= final_score due to sorting inherently.
                    self.stats["dropped_dedup"] += 1
                    self.dedup_logs.append(f"dedup: [{existing['title']}] over [{art['title']}]")
                    break
                    
            if not is_dup:
                deduped.append(art)
                
        # Max Output slice
        final = deduped[:MAX_OUTPUT]
        
        # Reddit Cap
        max_reddit = math.floor(len(final) * REDDIT_MAX_PCT)
        rcount = 0
        final_capped = []
        
        # Sort so we drop lowest scoring reddit posts first... wait, they are already sorted by final_score descending!
        for art in final:
            if art["source_type"] == "REDDIT":
                if rcount >= max_reddit:
                    self.stats["dropped_reddit_cap"] += 1
                    continue
                rcount += 1
            final_capped.append(art)

        return final_capped

def run_scout():
    eng = ScoutEngine()
    eng.fetch_all()
    final_output = eng.run_pipeline()
    
    target_tz_offset = 8
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    pst_now = utc_now - datetime.timedelta(hours=target_tz_offset)
    run_date_str = pst_now.date().isoformat()
    
    print(f"[SYSTEM] CLOCK SYNC: UTC({utc_now.strftime('%H:%M')}) -> PST({pst_now.strftime('%H:%M')}) | TARGET_DATE: {run_date_str}")
    out_obj = {
        "run_date": run_date_str,
        "run_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metadata": eng.stats,
        "articles": []
    }
    
    for a in final_output:
        out_obj["articles"].append({
            "title": a["title"],
            "summary": a["summary"],
            "source_domain": a["source_domain"],
            "url": a["url"],
            "timestamp_utc": a["timestamp_utc"],
            "source_type": a["source_type"],
            "relevance_score": a["relevance_score"],
            "priority_tier": a["priority_tier"],
            "final_score": a["final_score"],
            "ai_context_count": a["ai_context_count"],
            "reject_override": a["reject_override"]
        })
        
    os.makedirs(os.path.dirname(os.path.join("data", "raw", "today.json")), exist_ok=True)
    with open(os.path.join("data", "raw", "today.json"), "w", encoding="utf-8") as f:
        json.dump(out_obj, f, indent=2)

    # Logging
    print(f"\n=== SCOUT AGENT RUN: {run_date_str} ===")
    print(f"Sources fetched       : {eng.stats['fetched_total']} total")
    print("----------------------------------")
    print(f"Dropped (zero AI ctx) : {eng.stats['dropped_zero_ai_context']}")
    print(f"Dropped (credibility) : {eng.stats['dropped_credibility_blacklist']}")
    print(f"Dropped (URL pattern) : {eng.stats['dropped_url_pattern']}")
    print(f"Dropped (hard reject) : {eng.stats['dropped_hard_reject']}")
    print(f"Dropped (low score)   : {eng.stats['dropped_below_threshold']}")
    print(f"Dropped (dedup)       : {eng.stats['dropped_dedup']}")
    print(f"Dropped (reddit cap)  : {eng.stats['dropped_reddit_cap']}")
    print("----------------------------------")
    
    fallbacks = []
    if eng.stats["fallback_date_window_triggered"]: fallbacks.append("DATE_WINDOW")
    if eng.stats["fallback_threshold_triggered"]: fallbacks.append("THRESHOLD")
    if eng.stats["fallback_tier1_force_triggered"]: fallbacks.append("TIER1_FORCE")
    
    print(f"Fallbacks triggered   : {', '.join(fallbacks) if fallbacks else 'none'}")
    print("----------------------------------")
    print(f"Final output          : {eng.stats['final_count']} articles")
    print("----------------------------------")
    print("TOP 5 BY SCORE:")
    for i, a in enumerate(final_output[:5]):
        print(f"  {i+1}. [{a['final_score']}] [{a['source_type']}] {a['title']}")
    print("===================================")

if __name__ == "__main__":
    run_scout()
