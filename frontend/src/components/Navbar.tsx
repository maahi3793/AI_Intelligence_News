import Link from "next/link";

export default function Navbar() {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-50">
      <div className="max-w-4xl mx-auto flex justify-between items-center">
        <Link href="/" className="flex items-center space-x-3 group">
          {/* Custom SVG Geometric Logo (No emojis, highly professional) */}
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-rose-500 flex items-center justify-center text-white shadow-md transform transition-transform group-hover:scale-105">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <span className="font-extrabold text-xl tracking-tight text-gray-900 group-hover:text-indigo-600 transition-colors">
            AI Intelligence
          </span>
        </Link>
        <div className="space-x-8 text-sm font-medium text-gray-600">
          <a href="/" className="hover:text-indigo-600 transition-colors">Today</a>
          {/* Using raw anchor tag to bypass Nextjs client-render hang on historical fetching */}
          <a href="/archive" className="hover:text-indigo-600 transition-colors">Archive</a>
        </div>
      </div>
    </div>
  );
}
