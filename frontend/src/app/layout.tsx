import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Intelligence | Premium AI News & Analysis",
  description: "The definitive daily briefing for artificial intelligence. Deterministic filtering, curated insights, and deep-technical analysis across development, business, and strategy.",
  keywords: ["AI News", "Artificial Intelligence", "Machine Learning", "Tech Briefing", "LLM", "Generative AI"],
  authors: [{ name: "AI Intelligence Engine" }],
  openGraph: {
    title: "AI Intelligence | Daily Analytical Briefing",
    description: "Navigate the noise of AI with our curated, high-signal intelligence gathering system.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
