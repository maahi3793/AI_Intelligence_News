import { supabase } from "./supabase";

export async function getLatestNewsletter() {
  const { data } = await supabase
    .from("newsletters")
    .select("*")
    .order("publish_date", { ascending: false })
    .limit(1)
    .single();

  return data;
}

export async function getArticles(newsletterId: string) {
  const { data } = await supabase
    .from("articles")
    .select("*")
    .eq("newsletter_id", newsletterId);

  return data;
}

export async function getInsights(newsletterId: string) {
  const { data } = await supabase
    .from("insights")
    .select("*")
    .eq("newsletter_id", newsletterId);

  return data;
}

// ── Trend Queries ──────────────────────────────────────────────────────────

export interface TrendRow {
  id: string;
  date: string;
  topic: string;
  mention_count: number;
  confidence: string;
  trend: string;       // "rising" | "declining" | "stable"
  theme_name: string;
}

/**
 * Fetch all trend data ordered by date ascending.
 */
export async function getTrendData(): Promise<TrendRow[]> {
  const { data, error } = await supabase
    .from("trends")
    .select("*")
    .order("date", { ascending: true });

  if (error) {
    console.error("Error fetching trend data:", error);
    return [];
  }
  return (data ?? []) as TrendRow[];
}

/**
 * Aggregate trend data into hot-topic summaries with week-over-week change.
 * Returns topics sorted by current-week mentions descending.
 */
export interface HotTopic {
  topic: string;
  currentWeekMentions: number;
  previousWeekMentions: number;
  percentChange: number;
  trend: "rising" | "declining" | "stable";
  latestDate: string;
  firstSeenDate: string;
}

export function computeHotTopics(rows: TrendRow[]): HotTopic[] {
  if (rows.length === 0) return [];

  // Determine the latest date in the dataset
  const allDates = [...new Set(rows.map((r) => r.date))].sort();
  const latestDate = allDates[allDates.length - 1];
  const latestMs = new Date(latestDate).getTime();
  const sevenDays = 7 * 24 * 60 * 60 * 1000;

  // Group by topic
  const topicMap = new Map<string, TrendRow[]>();
  for (const row of rows) {
    const existing = topicMap.get(row.topic) ?? [];
    existing.push(row);
    topicMap.set(row.topic, existing);
  }

  const results: HotTopic[] = [];

  for (const [topic, topicRows] of topicMap) {
    const sortedRows = topicRows.sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const currentWeekRows = sortedRows.filter(
      (r) => latestMs - new Date(r.date).getTime() < sevenDays
    );
    const previousWeekRows = sortedRows.filter((r) => {
      const ms = new Date(r.date).getTime();
      return latestMs - ms >= sevenDays && latestMs - ms < sevenDays * 2;
    });

    const currentWeekMentions = currentWeekRows.reduce(
      (sum, r) => sum + r.mention_count,
      0
    );
    const previousWeekMentions = previousWeekRows.reduce(
      (sum, r) => sum + r.mention_count,
      0
    );

    const percentChange =
      previousWeekMentions > 0
        ? ((currentWeekMentions - previousWeekMentions) / previousWeekMentions) * 100
        : currentWeekMentions > 0
        ? 100
        : 0;

    // Determine trend from the latest row for this topic
    const latestRow = sortedRows[sortedRows.length - 1];
    const trend =
      latestRow.trend === "rising"
        ? "rising"
        : latestRow.trend === "declining"
        ? "declining"
        : "stable";

    results.push({
      topic,
      currentWeekMentions,
      previousWeekMentions,
      percentChange,
      trend: trend as "rising" | "declining" | "stable",
      latestDate: latestRow.date,
      firstSeenDate: sortedRows[0].date,
    });
  }

  // Sort by currentWeekMentions descending
  results.sort((a, b) => b.currentWeekMentions - a.currentWeekMentions);
  return results;
}
