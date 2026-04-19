# AI News System — Project Context

## What This Is

A fully automated, multi-agent AI news intelligence pipeline. It runs three agents in sequence to fetch, analyze, and write a daily newsletter from live AI news sources. The end product is a structured JSON newsletter with four audience-specific articles (devs, students, business, general).

---

## Architecture Overview

```
main.py
  └── run_scout()    → data/raw/today.json
  └── run_analyst()  → data/processed/insights.json
  └── run_writer()   → data/processed/newsletter.json
```

### Agent 1: Scout (`agents/scout.py`)

A fully deterministic scraper (V4.1). No LLM involved — pure Python logic.

**Sources:**
- 19 RSS feeds (DeepMind, Google AI, Anthropic x2, OpenAI, NVIDIA x2, TechCrunch `/category/` URL, The Verge, Reddit r/MachineLearning, HuggingFace, VentureBeat `/feed/`, MIT Tech Review, Simon Willison, Interconnects, The AI Edge)
- GNews API (`GNEWS_API_KEY` hardcoded in scout.py)
- Currents API (`CURRENTS_API_KEY` hardcoded in scout.py)

**Pipeline:**
1. Fetch all sources
2. Credibility blacklist — drop state media (rt.com, tass.ru, xinhua.net, cgtn.com, sputniknews.com, globaltimes.cn, etc.) before any scoring
3. URL pattern blacklist — drop tutorial/docs/academy/support pages before any scoring
4. Hard reject if `ai_context_count == 0` — no exceptions, all source tiers. Count uses **whole-word regex** (`\bterm\b`) via precompiled `_AI_TERM_PATTERNS` — fixes substring false positives ("said"→"ai", "Isaiah"→"ai", "available"→"ai")
5. Hard reject non-AI topics (gaming, politics, ransomware, etc.)
6. Score articles by depth, recency, source tier, entity mentions. Title AI term penalty also uses whole-word matching via `_count_ai_terms()`
7. Deduplicate (6-word consecutive match OR SequenceMatcher ≥ 0.85)
8. Apply Reddit cap (≤ 20% of final output)
9. 3-stage fallback: date window → lower threshold → Tier 1 force

**Stat keys:** `dropped_zero_ai_context`, `dropped_credibility_blacklist`, `dropped_url_pattern`, `dropped_hard_reject`, `dropped_below_threshold`, `dropped_dedup`, `dropped_reddit_cap`

**Known feed issues (2026-04-11):** arXiv RSS (`arxiv.org/rss/cs.*`) returns 0 entries — likely user-agent blocked. DeepLearning.AI The Batch feed URLs all return empty. Google AI Blog `ai.googleblog.com` is dead (use `blog.google/technology/ai/rss/` instead, already in feeds). VentureBeat `/category/ai/feed/` returns months-old articles — use `/feed/` instead (fixed). TechCrunch `/tag/artificial-intelligence/feed/` is stale — use `/category/artificial-intelligence/feed/` (fixed).

**Constants:**
- `SCORE_THRESHOLD = 4`, `FALLBACK_THRESHOLD = 2`
- `MAX_OUTPUT = 20`, `MIN_OUTPUT = 5`
- `DATE_WINDOW_HOURS = 24`, `FALLBACK_WINDOW_HOURS = 48`
- `REDDIT_MAX_PCT = 0.20`

**Output:** `data/raw/today.json` — scored, deduplicated articles with metadata

---

### Agent 2: Analyst (`agents/analyst.py`)

Uses Gemini (`gemini-2.5-flash`, temperature 0.15) to transform raw articles into structured intelligence.

**Prompt:** `prompts/analyst_prompt.txt` — Analyst Agent V3

**Steps in prompt:**
1. Secondary filtering (remove weak/opinion/marketing articles)
1b. Source credibility check — state media flagged as `[SOURCE: STATE MEDIA]`, demoted to weak_signal if sole source
2. Cluster articles into themes (6 categories)
3. Select 2–5 dominant themes
4. Generate developments per theme (`[Entity]: event → impact`)
5. Signal vs. noise assessment
6. Generate 3–5 forward-looking strategic insights
7. Confidence scoring — calibrated: high=3+ sources, medium=2 sources or 1 strong primary, low=single/aggregator/state media. Single-article themes are almost always low. Must differentiate — do not assign all themes the same score.
8. Contradiction detection (surface, don't resolve)
9. Temporal comparison — `emerging/growing/stable/declining`. Decay rule: only "decayed" if absent 3+ consecutive runs or directly contradicted. Single-day absence = "unconfirmed", not decayed.

**Output:** `data/processed/insights.json` — structured intelligence with themes, insights, temporal analysis

---

### Agent 3: Writer (`agents/writer.py`)

Uses Gemini (`gemini-2.5-flash`, temperature 0.6, top_p 0.9) to produce audience-specific articles.

**Prompt:** `prompts/writer_prompt.txt` — Writer Agent V2

**Style target:** Morning Brew + The Hustle + Notion blog. Sharp, opinionated, human-grade.

**Audiences:** `devs`, `students`, `business`, `general`
- Each gets a different angle on the same story
- Minimum 2 audiences always; target 3–4

**Anti-patterns strictly enforced in prompt:**
- No generic openings ("The AI landscape is evolving")
- No AI-slop language ("leverage", "delve into", "unlock")
- No hallucination — every claim must trace to analyst input
- No labeled section headers in body copy (`WHY IT MATTERS:`, `THE BOTTOM LINE:`) — integrate naturally into closing paragraph
- Grounding enforcement: every sentence must trace to a specific theme/development/insight; banned phrases: "your career", "job market", "stay ahead", "in today's world", "as we move forward"
- Students audience skipped unless: new model/tool learners can try, conceptual breakthrough, or free/open resource announced — geopolitics/regulation/pricing do not qualify
- Audience deduplication: each development is the primary driver for only one audience article

**Retry logic:** 2 attempts, 2-second wait between; falls back to `deterministic_fallback()` on total failure

**Output:** `data/processed/newsletter.json` — final newsletter JSON

---

## File Structure

```
ai-news-system/
├── main.py                        # Entry point — runs all 3 agents in sequence
├── config.py                      # GEMINI_API_KEY and MODEL_NAME
├── agents/
│   ├── scout.py                   # Deterministic scraper (no LLM)
│   ├── analyst.py                 # LLM analyst agent
│   └── writer.py                  # LLM writer agent
├── prompts/
│   ├── analyst_prompt.txt         # Analyst Agent V3 system prompt
│   └── writer_prompt.txt          # Writer Agent V2 system prompt
├── data/
│   ├── raw/today.json             # Scout output
│   ├── processed/
│   │   ├── insights.json          # Analyst output (also used as "yesterday" next run)
│   │   └── newsletter.json        # Final newsletter output
│   ├── final/today.json           # (exists, purpose TBD)
│   └── seen_urls.json             # (exists, purpose TBD — likely dedup history)
├── frontend/                      # Next.js website (App Router)
└── test_apis.py / test_gemini.py  # API connection tests
```

---

## Configuration

**`config.py`** stores:
- `GEMINI_API_KEY` — hardcoded (not from environment)
- `MODEL_NAME = "gemini-2.5-flash"`

Scout has its own hardcoded API keys for GNews and Currents at the top of `scout.py`.

**Important:** API keys are currently hardcoded in source files, not in `.env`. Do not commit these to a public repo.

---

## Data Flow

```
RSS + GNews + Currents
        ↓
    Scout (deterministic scoring + filtering)
        ↓
  data/raw/today.json
        ↓
    Analyst (Gemini, low temp, JSON mode)
    also reads: data/processed/insights.json (yesterday)
        ↓
  data/processed/insights.json
        ↓
    Writer (Gemini, higher temp, JSON mode)
        ↓
  data/processed/newsletter.json
```

---

## Running the Pipeline

```bash
cd C:/Users/reach/.gemini/antigravity/scratch/ai-news-system
python main.py
```

Or run agents individually:
```bash
python agents/scout.py
python agents/analyst.py
python agents/writer.py
```

---

## Broader Context

This project lives under `C:\Users\reach\.gemini\antigravity\scratch\` — a scratch/experimental workspace managed by Antigravity, a persistent Gemini agent system. The Antigravity system also manages:

- `knowledge/` — learned patterns (currently: Flet app development patterns from a separate PyNexus project)
- `brain/` — session state (binary protobuf files, not human-readable)
- `conversations/` — conversation history (binary protobuf files)
- `implicit/` — implicit memory (binary protobuf files)

The Flet/PyNexus knowledge is from a different project and is not directly relevant to this news system.

---

## Known Design Decisions

- **Scout is intentionally LLM-free** — deterministic behavior, reproducible results, no API cost for filtering
- **Analyst uses low temperature (0.15)** — analytical precision over creativity
- **Writer uses higher temperature (0.6)** — allows natural writing variation
- **Temporal memory** — `insights.json` is read by the next day's analyst run as "yesterday's analysis," enabling trend tracking without a database
- **Fallback chain** — both Scout (3-stage) and Writer (retry + deterministic fallback) have explicit fallback strategies so the pipeline never silently fails
- **JSON-only LLM output** — both agents use `response_mime_type: "application/json"` with defensive markdown stripping as a fallback

---

## Evolution Tracker (Completed Work)

**Writer Agent (Completed V2 Upgrade):**
- Upgraded the Writer loop mapping to strict audience angles ("Students", "Devs", "General", "Business").
- Banned all "AI-Slop" tokens ("delve", "leverage", etc.) and enforced "Resilience Mode" which dynamically refits active themes to remaining unmapped audiences instead of skipping them when upstream signals are low.
- Natively wired fallback architectures into python to avoid token drops via `max_output_tokens` bounds overrides.

**Publisher Agent (Phase 1A/1B Completed):**
- **Architecture:** Reads `newsletter.json` directly. Employs "Single Source of Truth" pattern meaning Writer natively packs `top_insights` into the output JSON to avoid multi-file publisher entanglement.
- **Backend (Supabase):** Built and deployed tables (`newsletters`, `articles`, `insights`) over PostgreSQL with `UNIQUE(publish_date)` date constraints and `ON DELETE CASCADE` foreign keys.
- **Idempotency & Safety:** Python script executes pre-flight checks blocking uploads if the date already exists. In the event of an orphaned/crashed push, publisher triggers a simulated atomicity rollback (Python intercepts and fires a `.delete()` passing the UUID down the cascade).
- **Next Up:** Phase 2 (Automation Layer).

**Frontend Website (Phase 1C Completed):**
- **Location:** `C:\Users\reach\.gemini\antigravity\scratch\ai-news-system\frontend\` (inside main project directory)
- **Stack:** Next.js 16 (App Router) + Tailwind CSS + Supabase + TypeScript
- **Routes:**
  - `/` — Homepage showing latest newsletter with article cards and strategic insights
  - `/archive` — Historical intelligence listing all published dates
  - `/newsletter/[date]` — Full article view with Executive Summary, semantic `<p>` paragraph rendering, and Key Takeaways bullets
- **Design System:** Dark editorial theme (`#0f1115` background, `#161a22` cards, `#7aa2f7` accent, `#222733` borders). Typography-first, spacing-driven, zero gradients, zero emojis. Target aesthetic: Linear + Notion + Morning Brew.
- **Components:** `Navbar.tsx`, `Footer.tsx`, `ArticleCard.tsx` (card preview), `ArticleView.tsx` (full article with `content.split("\n\n")` mapped to semantic `<p>` tags)
- **Data Layer:** `lib/supabase.ts` (client instantiation), `lib/queries.ts` (getLatestNewsletter, getArticles, getInsights). All pages use Server Components for zero client-side JS overhead.
- **Environment:** `.env.local` holds `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Build Status:** Production build passes with zero errors. Dev server runs on `http://localhost:3000`.
- **Deployment:** Ready for Vercel import. Push to GitHub, import repo in Vercel, add env variables, deploy.
