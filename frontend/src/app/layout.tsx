import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/layout/Providers";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Allocensus — AI-Validated Portfolio Rebalancing", template: "%s | Allocensus" },
  description: "Institutional-grade portfolio rebalancing intelligence powered by Genlayer AI validators. Transparent, auditable, defensible investment rationale on-chain.",
  keywords: ["portfolio rebalancing", "AI", "institutional", "Genlayer", "blockchain", "investment"],
  icons: {
    icon: [
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/logo.png", type: "image/png" },
    ],
    apple: { url: "/apple-touch-icon.png", sizes: "180x180" },
  },
  openGraph: {
    type: "website",
    siteName: "Allocensus",
    title: "Allocensus — AI-Validated Portfolio Rebalancing",
    description: "Transparent, on-chain investment rationale for institutional portfolios.",
    images: [{ url: "/logo.png" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
