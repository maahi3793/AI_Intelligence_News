"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  getTrendData,
  computeHotTopics,
  type TrendRow,
  type HotTopic,
} from "@/lib/queries";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { format, parseISO, differenceInDays } from "date-fns";

// ── Curated color palette ─────────────────────────────────────────────────
const CHART_COLORS = [
  { stroke: "#6366f1", fill: "rgba(99,102,241,0.08)" },   // indigo
  { stroke: "#f43f5e", fill: "rgba(244,63,94,0.08)" },    // rose
  { stroke: "#10b981", fill: "rgba(16,185,129,0.08)" },   // emerald
  { stroke: "#f59e0b", fill: "rgba(245,158,11,0.08)" },   // amber
  { stroke: "#8b5cf6", fill: "rgba(139,92,246,0.08)" },   // violet
];

// ── Animated count-up hook ────────────────────────────────────────────────
function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number>();

  useEffect(() => {
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return value;
}

// ── Single Hot Topic Card ─────────────────────────────────────────────────
function HotTopicCard({
  topic,
  rank,
  isVisible,
}: {
  topic: HotTopic;
  rank: number;
  isVisible: boolean;
}) {
  const count = useCountUp(isVisible ? topic.currentWeekMentions : 0);
  const isFirst = rank === 0;

  const trendConfig = {
    rising: { icon: "↑", color: "text-emerald-600", bg: "bg-emerald-50", label: "Rising" },
    declining: { icon: "↓", color: "text-rose-500", bg: "bg-rose-50", label: "Declining" },
    stable: { icon: "→", color: "text-gray-500", bg: "bg-gray-100", label: "Stable" },
  };
  const t = trendConfig[topic.trend];

  return (
    <div
      className={`
        relative bg-white rounded-2xl border transition-all duration-500 ease-out
        hover:shadow-[0_20px_50px_-12px_rgba(0,0,0,0.12)] hover:-translate-y-1
        ${isFirst
          ? "border-transparent shadow-lg"
          : "border-gray-200 shadow-sm"
        }
        ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
      `}
      style={{ transitionDelay: `${rank * 100}ms` }}
    >
      {/* Glowing gradient border for #1 */}
      {isFirst && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-rose-500 -z-10 blur-[2px] scale-[1.02] opacity-60 animate-pulse" />
      )}
      {isFirst && (
        <div className="absolute inset-0 rounded-2xl bg-white -z-[5]" />
      )}

      <div className="p-6">
        {/* Rank badge */}
        <div className="flex items-start justify-between mb-4">
          <span
            className={`
              inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-black
              ${isFirst
                ? "bg-gradient-to-br from-indigo-600 to-rose-500 text-white shadow-md"
                : "bg-gray-100 text-gray-500"
              }
            `}
          >
            {rank + 1}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${t.bg} ${t.color}`}
          >
            <span className="mr-1">{t.icon}</span>
            {topic.percentChange !== 0
              ? `${topic.percentChange > 0 ? "+" : ""}${topic.percentChange.toFixed(0)}%`
              : t.label}
          </span>
        </div>

        {/* Topic name */}
        <h3
          className={`font-extrabold tracking-tight mb-3 ${
            isFirst ? "text-xl text-gray-900" : "text-lg text-gray-800"
          }`}
        >
          {topic.topic}
        </h3>

        {/* Animated mention count */}
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-black text-gray-900 tabular-nums">
            {count}
          </span>
          <span className="text-sm text-gray-400 font-medium">
            mentions this week
          </span>
        </div>

        {/* Subtle bar indicator */}
        <div className="mt-4 h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-out ${
              isFirst
                ? "bg-gradient-to-r from-indigo-500 to-rose-500"
                : "bg-indigo-400"
            }`}
            style={{
              width: isVisible ? "100%" : "0%",
              transitionDelay: `${rank * 100 + 400}ms`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Custom Tooltip for Chart ──────────────────────────────────────────────
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ color: string; name: string; value: number }>;
  label?: string;
}) {
  if (!active || !payload || !label) return null;

  let formattedLabel = label;
  try {
    formattedLabel = format(parseISO(label), "MMM d, yyyy");
  } catch {
    // keep original label
  }

  return (
    <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl shadow-xl px-4 py-3 text-sm">
      <p className="font-bold text-gray-900 mb-2">{formattedLabel}</p>
      <div className="space-y-1">
        {payload.map((entry, i) => (
          <div key={i} className="flex items-center space-x-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-600">{entry.name}:</span>
            <span className="font-bold text-gray-900">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sparkle SVG Icon ──────────────────────────────────────────────────────
function SparkleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z" />
    </svg>
  );
}

// ── Loading Skeleton ──────────────────────────────────────────────────────
function LoadingSkeleton() {
  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      {/* Dark hero skeleton */}
      <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="h-4 w-48 bg-gray-700 rounded-full mx-auto mb-6 animate-pulse" />
          <div className="h-10 w-96 max-w-full bg-gray-700 rounded-2xl mx-auto mb-4 animate-pulse" />
          <div className="h-5 w-80 max-w-full bg-gray-700/60 rounded-full mx-auto animate-pulse" />
        </div>
      </div>

      <div className="flex-grow max-w-5xl mx-auto w-full px-6 py-16">
        {/* Topic cards skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-20">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-gray-200 p-6 animate-pulse"
            >
              <div className="flex justify-between mb-4">
                <div className="w-8 h-8 bg-gray-200 rounded-lg" />
                <div className="w-16 h-6 bg-gray-200 rounded-full" />
              </div>
              <div className="h-5 w-3/4 bg-gray-200 rounded-lg mb-3" />
              <div className="h-8 w-1/2 bg-gray-200 rounded-lg mb-4" />
              <div className="h-1 bg-gray-200 rounded-full" />
            </div>
          ))}
        </div>

        {/* Chart skeleton */}
        <div className="bg-white rounded-2xl border border-gray-200 p-8 animate-pulse">
          <div className="h-6 w-48 bg-gray-200 rounded-lg mb-8" />
          <div className="h-80 bg-gray-100 rounded-xl" />
        </div>
      </div>

      <Footer />
    </main>
  );
}

// ══════════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ══════════════════════════════════════════════════════════════════════════
export default function TrendsPage() {
  const [trendData, setTrendData] = useState<TrendRow[]>([]);
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [cardsVisible, setCardsVisible] = useState(false);
  const [chartVisible, setChartVisible] = useState(false);

  useEffect(() => {
    async function fetchData() {
      const data = await getTrendData();
      setTrendData(data);
      setHotTopics(computeHotTopics(data));
      setLoading(false);

      // Stagger animations
      setTimeout(() => setCardsVisible(true), 150);
      setTimeout(() => setChartVisible(true), 500);
    }
    fetchData();
  }, []);

  // ── Build chart data: pivot rows into { date, topic1: count, topic2: count, ... }
  const top5Topics = hotTopics.slice(0, 5).map((t) => t.topic);

  const chartData = (() => {
    const dateMap = new Map<string, Record<string, number>>();
    for (const row of trendData) {
      if (!top5Topics.includes(row.topic)) continue;
      const existing = dateMap.get(row.date) ?? {};
      existing[row.topic] = (existing[row.topic] ?? 0) + row.mention_count;
      dateMap.set(row.date, existing);
    }
    return [...dateMap.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, topics]) => ({ date, ...topics }));
  })();

  // ── Emerging signals: topics first seen within the last 7 days
  const emergingSignals = (() => {
    if (trendData.length === 0) return [];
    const allDates = [...new Set(trendData.map((r) => r.date))].sort();
    const latestDate = parseISO(allDates[allDates.length - 1]);

    return hotTopics.filter((t) => {
      try {
        return differenceInDays(latestDate, parseISO(t.firstSeenDate)) < 7;
      } catch {
        return false;
      }
    });
  })();

  if (loading) return <LoadingSkeleton />;

  const isEmpty = trendData.length === 0;

  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      {/* ── Dark Gradient Hero ─────────────────────────────────────────── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 py-20 sm:py-24 px-6">
        {/* Animated gradient orbs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-rose-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl" />

        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 text-indigo-300 text-xs font-bold tracking-widest uppercase mb-6">
            <SparkleIcon className="w-3.5 h-3.5 mr-2" />
            Intelligence Analytics
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white mb-4">
            Trend{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-rose-400 bg-clip-text text-transparent">
              Dashboard
            </span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Real-time intelligence on what&rsquo;s moving in AI. Powered by deterministic
            analysis across hundreds of signals daily.
          </p>
        </div>
      </div>

      {/* ── Main Content ───────────────────────────────────────────────── */}
      <div className="flex-grow max-w-5xl mx-auto w-full px-6 py-16">
        {isEmpty ? (
          <div className="text-center py-32">
            <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-extrabold text-gray-900 mb-2">No trend data yet</h2>
            <p className="text-gray-500">Trend analytics will appear once the pipeline begins collecting signals.</p>
          </div>
        ) : (
          <>
            {/* ═══════ SECTION 1: What's Hot Right Now ═══════ */}
            <section className="mb-20">
              <div className="flex items-center mb-8">
                <div className="bg-gradient-to-br from-indigo-600 to-rose-500 rounded-xl p-2 mr-4 shadow-md">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-extrabold tracking-tight text-gray-900">
                    What&rsquo;s Hot Right Now
                  </h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Top trending topics by mention volume this week
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {hotTopics.slice(0, 5).map((topic, i) => (
                  <HotTopicCard
                    key={topic.topic}
                    topic={topic}
                    rank={i}
                    isVisible={cardsVisible}
                  />
                ))}
              </div>
            </section>

            {/* ═══════ SECTION 2: Trend Timeline ═══════ */}
            <section className="mb-20">
              <div className="flex items-center mb-8">
                <div className="bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl p-2 mr-4 shadow-md">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-extrabold tracking-tight text-gray-900">
                    Trend Timeline
                  </h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Topic mention volume over time — hover to explore
                  </p>
                </div>
              </div>

              <div
                className={`
                  bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8
                  transition-all duration-700 ease-out
                  ${chartVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}
                `}
              >
                {/* Chart legend */}
                <div className="flex flex-wrap gap-4 mb-6">
                  {top5Topics.map((topic, i) => (
                    <div key={topic} className="flex items-center space-x-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length].stroke }}
                      />
                      <span className="text-sm font-medium text-gray-600">{topic}</span>
                    </div>
                  ))}
                </div>

                {/* Recharts Area Chart */}
                <div className="w-full h-80 sm:h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={chartData}
                      margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                    >
                      <defs>
                        {top5Topics.map((topic, i) => (
                          <linearGradient
                            key={topic}
                            id={`gradient-${i}`}
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor={CHART_COLORS[i % CHART_COLORS.length].stroke}
                              stopOpacity={0.15}
                            />
                            <stop
                              offset="95%"
                              stopColor={CHART_COLORS[i % CHART_COLORS.length].stroke}
                              stopOpacity={0}
                            />
                          </linearGradient>
                        ))}
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#f1f5f9"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: "#9ca3af", fontSize: 12, fontWeight: 500 }}
                        tickLine={false}
                        axisLine={{ stroke: "#e5e7eb" }}
                        tickFormatter={(val) => {
                          try {
                            return format(parseISO(val), "MMM d");
                          } catch {
                            return val;
                          }
                        }}
                      />
                      <YAxis
                        tick={{ fill: "#9ca3af", fontSize: 12, fontWeight: 500 }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ stroke: "#e5e7eb", strokeWidth: 1 }}
                      />
                      {top5Topics.map((topic, i) => (
                        <Area
                          key={topic}
                          type="monotone"
                          dataKey={topic}
                          stroke={CHART_COLORS[i % CHART_COLORS.length].stroke}
                          strokeWidth={2.5}
                          fill={`url(#gradient-${i})`}
                          dot={false}
                          activeDot={{
                            r: 5,
                            strokeWidth: 2,
                            fill: "#fff",
                            stroke: CHART_COLORS[i % CHART_COLORS.length].stroke,
                          }}
                        />
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>

            {/* ═══════ SECTION 3: Emerging Signals ═══════ */}
            <section>
              <div className="flex items-center mb-8">
                <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl p-2 mr-4 shadow-md">
                  <SparkleIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-extrabold tracking-tight text-gray-900">
                    Emerging Signals
                  </h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Topics that appeared for the first time in the last 7 days
                  </p>
                </div>
              </div>

              {emergingSignals.length === 0 ? (
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12 text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 12H4" />
                    </svg>
                  </div>
                  <p className="text-gray-500 font-medium">
                    No new signals detected this week
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    Emerging topics will surface here when first detected by the pipeline.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {emergingSignals.map((signal, i) => (
                    <div
                      key={signal.topic}
                      className={`
                        bg-white rounded-2xl border border-gray-200 shadow-sm p-6
                        hover:shadow-[0_12px_35px_-10px_rgba(0,0,0,0.1)] hover:-translate-y-0.5
                        transition-all duration-500 ease-out
                        ${cardsVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
                      `}
                      style={{ transitionDelay: `${i * 80 + 800}ms` }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="inline-flex items-center px-2.5 py-1 bg-amber-50 text-amber-600 rounded-full text-xs font-bold tracking-wide">
                          <SparkleIcon className="w-3 h-3 mr-1.5" />
                          NEW
                        </span>
                        <span className="text-xs text-gray-400 font-medium">
                          {(() => {
                            try {
                              return format(parseISO(signal.firstSeenDate), "MMM d");
                            } catch {
                              return signal.firstSeenDate;
                            }
                          })()}
                        </span>
                      </div>
                      <h3 className="text-lg font-extrabold text-gray-900 tracking-tight mb-2">
                        {signal.topic}
                      </h3>
                      <p className="text-sm text-gray-500">
                        <span className="font-bold text-gray-800">
                          {signal.currentWeekMentions}
                        </span>{" "}
                        mentions since first detection
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>

      <Footer />
    </main>
  );
}
