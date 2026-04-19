import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { supabase } from "@/lib/supabase";

export const dynamic = 'force-dynamic'; // Force SSR output without build locks

export default async function Archive() {
  const { data } = await supabase
    .from("newsletters")
    .select("publish_date, id")
    .order("publish_date", { ascending: false });

  return (
    <main className="min-h-screen flex flex-col bg-gray-50/50">
      <Navbar />

      <div className="flex-grow max-w-3xl mx-auto w-full px-6 py-16">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 mb-12 flex items-center">
          <span className="bg-indigo-100 text-indigo-600 rounded-lg p-2 mr-4">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
          </span>
          Historical Archives
        </h1>

        <div className="space-y-4">
          {data && data.length > 0 ? (
            data.map((n: any) => (
              <a 
                key={n.id} 
                href={`/newsletter/${n.publish_date}`} 
                className="flex items-center justify-between p-6 rounded-2xl bg-white border border-gray-200 transition-all duration-200 hover:border-indigo-500 hover:shadow-md group"
              >
                <div className="flex items-center">
                  <div className="w-2 h-10 bg-gradient-to-b from-indigo-500 to-rose-400 rounded-full mr-4"></div>
                  <span className="text-gray-800 font-bold tracking-wide text-lg">
                    Intelligence Briefing
                  </span>
                </div>
                <span className="text-indigo-600 font-bold bg-indigo-50 px-4 py-1.5 rounded-full text-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  {n.publish_date} →
                </span>
              </a>
            ))
          ) : (
            <div className="text-gray-500 text-lg">No historical data found.</div>
          )}
        </div>
      </div>

      <Footer />
    </main>
  );
}
