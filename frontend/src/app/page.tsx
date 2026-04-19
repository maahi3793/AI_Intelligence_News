import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { getLatestNewsletter, getArticles, getInsights } from "@/lib/queries";
import ArticleCard from "@/components/ArticleCard";

export const dynamic = 'force-dynamic'; // Preventing cache staleness & dev reload loops

export default async function Home() {
  const newsletter = await getLatestNewsletter();
  
  // Handle empty state if DB is entirely empty
  if (!newsletter) {
    return (
      <main className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <div className="flex-grow flex items-center justify-center text-gray-400">
          No intelligence published yet.
        </div>
        <Footer />
      </main>
    );
  }

  const articles = await getArticles(newsletter.id);
  const insights = await getInsights(newsletter.id);

  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      <div className="flex-grow max-w-4xl mx-auto w-full px-6 py-16">
        {/* Header */}
        <div className="mb-14 text-center">
          <p className="text-indigo-600 font-extrabold tracking-widest text-sm uppercase mb-3 drop-shadow-sm">
            Daily Intelligence Briefing
          </p>
          <h1 className="text-5xl sm:text-6xl font-black tracking-tight text-gray-900 drop-shadow-sm">
            Vol. {newsletter.publish_date}
          </h1>
        </div>

        {/* Core Insights Block */}
        {insights && insights.length > 0 && (
          <div className="mb-16 bg-white border border-gray-200 rounded-3xl p-8 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full blur-3xl -mr-10 -mt-10 opacity-70 border border-indigo-100"></div>
            <h2 className="text-xl font-extrabold text-gray-900 tracking-tight mb-6 flex items-center">
               <span className="bg-indigo-100 text-indigo-600 rounded-lg p-1.5 mr-3">
                 <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
               </span>
               Strategic Overview
            </h2>
            <ul className="space-y-4">
              {insights.map((i: any) => (
                <li key={i.id} className="leading-relaxed flex items-start text-gray-700 font-medium">
                  <span className="text-indigo-400 mr-4 mt-1 font-bold text-lg">›</span>
                  <span className="text-[1.05rem]">{i.insight_text}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Articles List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {articles?.map((article: any) => (
            <ArticleCard key={article.id} article={article} dateStr={newsletter.publish_date} />
          ))}
        </div>
      </div>

      <Footer />
    </main>
  );
}
