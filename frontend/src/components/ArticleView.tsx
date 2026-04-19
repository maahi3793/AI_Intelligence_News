export default function ArticleView({ article }: { article: any }) {
  const paragraphs = article.content.split("\n\n");

  let gradientBadge = "from-gray-600 to-gray-800 text-white";
  switch(article.audience?.toLowerCase()) {
    case 'devs': gradientBadge = "from-blue-600 to-indigo-600 text-white"; break;
    case 'business': gradientBadge = "from-emerald-500 to-teal-700 text-white"; break;
    case 'general': gradientBadge = "from-rose-500 to-orange-500 text-white"; break;
    case 'students': gradientBadge = "from-purple-600 to-pink-600 text-white"; break;
  }

  return (
    <article id={`article-${article.audience?.toLowerCase()}`} className="mt-16 mb-24 max-w-3xl mx-auto px-4 sm:px-6 scroll-mt-32">
      {/* Title block */}
      <div className="mb-12">
        <div className="mb-6 flex items-center">
          <span className={`text-xs uppercase tracking-widest bg-gradient-to-r ${gradientBadge} px-4 py-1.5 rounded-full font-bold shadow-sm`}>
            {article.audience}
          </span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900 leading-[1.15]">
          {article.title}
        </h1>
      </div>

      <hr className="my-10 border-t-2 border-gray-100" />

      {/* Body Mapping */}
      <div className="space-y-8 article-drop-cap">
        {paragraphs.map((para: string, index: number) => (
          <p key={index} className="text-[1.15rem] leading-[1.8] text-gray-800 font-serif">
            {para}
          </p>
        ))}
      </div>

      {/* Bullet Injection */}
      {article.bullets && article.bullets.length > 0 && (
        <div className="mt-16 bg-white border border-gray-200 shadow-sm rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-indigo-500 to-rose-500"></div>
          <h3 className="text-sm font-extrabold text-indigo-600 uppercase tracking-widest mb-6 ml-2">Executive Takeaways</h3>
          <ul className="space-y-4 ml-2">
            {article.bullets.map((b: string, i: number) => (
              <li key={i} className="text-[1.05rem] text-gray-700 flex items-start font-medium">
                <span className="text-rose-500 mr-4 mt-1 text-lg leading-none">✦</span>
                <span className="leading-relaxed">{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}
