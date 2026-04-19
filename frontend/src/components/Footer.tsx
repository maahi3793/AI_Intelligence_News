export default function Footer() {
  return (
    <footer className="border-t border-gray-200 mt-24 px-6 py-12 bg-white">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center text-sm text-gray-500">
        <div className="font-semibold tracking-wide text-gray-800 flex items-center space-x-2">
          <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <span>AI Intelligence</span>
        </div>
        <div className="mt-4 md:mt-0">
          Deterministic News Pipeline &copy; {new Date().getFullYear()}
        </div>
      </div>
    </footer>
  );
}
