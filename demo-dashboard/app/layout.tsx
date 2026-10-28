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
  title: "RoadAudit AI — Road Asset Intelligence",
  description:
    "AI-powered road inspection, maintenance prioritization, and repair accountability.",
  openGraph: {
    title: "RoadAudit AI",
    description: "From road damage to repair decisions.",
    images: [{ url: "/og.png", width: 1680, height: 941 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "RoadAudit AI",
    description: "From road damage to repair decisions.",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
