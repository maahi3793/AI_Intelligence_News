import { supabase } from "@/lib/supabase";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ArticleView from "@/components/ArticleView";

export default async function NewsletterDate({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;

  // 1. Fetch the newsletter
  const { data: newsletter } = await supabase
    .from("newsletters")
    .select("id")
    .eq("publish_date", date)
    .single();

  if (!newsletter) {
    return (
      <main className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <div className="flex-grow flex items-center justify-center text-gray-500 font-medium">
          Newsletter not found for this date.
        </div>
        <Footer />
      </main>
    );
  }

  // 2. Fetch the articles properly ordered
  const { data: articles } = await supabase
    .from("articles")
    .select("*")
    .eq("newsletter_id", newsletter.id)
    .order("id", { ascending: true });

  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      <div className="flex-grow max-w-4xl mx-auto w-full px-4 sm:px-6 py-16">
        <header className="mb-16 border-b border-gray-200 pb-12 flex flex-col items-center text-center">
          <div className="bg-indigo-100 text-indigo-700 px-4 py-1.5 rounded-full font-bold uppercase tracking-widest text-xs mb-6">
            Official Briefing
          </div>
          <h1 className="text-4xl sm:text-5xl font-black text-gray-900 tracking-tight">
             Volume {date}
          </h1>
          <p className="text-gray-500 mt-4 text-lg font-medium">
            Curated deterministic intelligence.
          </p>
        </header>

        <div className="space-y-24">
          {articles?.map((article: any) => (
            <ArticleView key={article.id} article={article} />
          ))}
        </div>
      </div>

      <Footer />
    </main>
  );
}
