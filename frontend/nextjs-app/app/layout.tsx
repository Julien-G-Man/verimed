import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://verimed-web.netlify.app"),
  title: "VeriMed — Medicine Authenticity Check",
  description: "AI-powered medicine authenticity risk assessment using OCR, barcode decoding, and explainable scoring.",
  icons: {
    icon: "/verimed-og.png",
    shortcut: "/verimed-og.png",
    apple: "/verimed-og.png",
  },
  openGraph: {
    title: "VeriMed — Medicine Authenticity Check",
    description: "AI-powered medicine authenticity risk assessment using OCR, barcode decoding, and explainable scoring.",
    images: [
      {
        url: "/verimed-og.png",
        width: 1200,
        height: 630,
        alt: "VeriMed",
      },
    ],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>{children}</body>
    </html>
  );
}
