export default function ArticleCard({ article, dateStr }: { article: any, dateStr: string }) {
  // Vibrant thematic colors based on audience target
  let gradientBanner = "from-gray-700 to-gray-900";
  let audienceTag = "text-gray-700 bg-gray-100";

  switch(article.audience?.toLowerCase()) {
    case 'devs':
      gradientBanner = "from-blue-600 to-indigo-600";
      audienceTag = "text-blue-700 bg-blue-50";
      break;
    case 'business':
      gradientBanner = "from-emerald-500 to-teal-700";
      audienceTag = "text-emerald-700 bg-emerald-50";
      break;
    case 'general':
      gradientBanner = "from-rose-500 to-orange-500";
      audienceTag = "text-rose-700 bg-rose-50";
      break;
    case 'students':
      gradientBanner = "from-purple-600 to-pink-600";
      audienceTag = "text-purple-700 bg-purple-50";
      break;
  }

  return (
    <div className="bg-white rounded-2xl overflow-hidden border border-gray-200 transition-all duration-300 hover:shadow-[0_20px_35px_-15px_rgba(0,0,0,0.1)] hover:-translate-y-1 group flex flex-col h-full">
      {/* Dynamic Graphic Banner */}
      <div className={`h-2 relative bg-gradient-to-r ${gradientBanner} w-full`}></div>
      
      <div className="p-8 flex flex-col flex-grow">
        <div className="mb-4 flex items-center justify-between">
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest ${audienceTag}`}>
            {article.audience}
          </span>
        </div>

        <h2 className="text-2xl font-extrabold tracking-tight text-gray-900 mb-4 group-hover:text-indigo-600 transition-colors">
          {article.title}
        </h2>

        <p className="text-gray-600 leading-relaxed line-clamp-4 flex-grow mb-6 text-[1.05rem]">
          {article.content.slice(0, 260).split('\n')[0]}...
        </p>

        <a 
          href={`/newsletter/${dateStr}/${article.audience.toLowerCase()}`} 
          className="inline-flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 transition-colors mt-auto group/btn"
        >
          Read full briefing 
          <span className="ml-1 group-hover/btn:translate-x-1 transition-transform">→</span>
        </a>
      </div>
    </div>
  );
}
