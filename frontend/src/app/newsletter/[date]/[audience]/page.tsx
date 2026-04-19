import { supabase } from "@/lib/supabase";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ArticleView from "@/components/ArticleView";

export default async function IsolatedArticle({ params }: { params: Promise<{ date: string, audience: string }> }) {
  const { date, audience } = await params;

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

  // 2. Fetch the specific article matching the audience (using ilike for case insensitivity)
  const { data: article } = await supabase
    .from("articles")
    .select("*")
    .eq("newsletter_id", newsletter.id)
    .ilike("audience", audience)
    .single();

  if (!article) {
    return (
      <main className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <div className="flex-grow flex items-center justify-center text-gray-500 font-medium">
          Article not found.
        </div>
        <Footer />
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      <div className="flex-grow w-full py-10">
        {/* Navigation Breadcrumb */}
        <div className="max-w-3xl mx-auto px-4 sm:px-6 mb-4">
          <a href={`/newsletter/${date}`} className="inline-flex items-center text-sm font-bold text-gray-400 hover:text-indigo-600 transition-colors group">
            <span className="mr-2 group-hover:-translate-x-1 transition-transform">←</span>
            Back to Full Volume {date}
          </a>
        </div>
        
        {/* Render Only The Chosen Article */}
        <ArticleView article={article} />
      </div>

      <Footer />
    </main>
  );
}
