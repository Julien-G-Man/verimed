import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import BackendKeepalive from "../components/BackendKeepalive";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://verimed-web.netlify.app"),
  applicationName: "VeriMed",
  title: {
    default: "VeriMed — Medicine Authenticity Risk Assessment",
    template: "%s | VeriMed",
  },
  description:
    "VeriMed is a free AI-powered tool to assess medicine authenticity risk. Upload photos of medicine packaging to get OCR text extraction, barcode verification, Ghana FDA reference matching, and an explainable risk score — instantly, on any device.",
  keywords: [
    "medicine authenticity check",
    "counterfeit medicine detector",
    "drug verification tool",
    "medicine barcode scanner",
    "fake medicine checker",
    "Ghana FDA drug registry",
    "medicine risk assessment",
    "pharmaceutical verification",
    "medicine packaging check",
    "OCR medicine scanner",
    "medicine safety tool",
    "how to spot fake medicine",
  ],
  authors: [{ name: "VeriMed" }],
  creator: "VeriMed",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "VeriMed",
  },
  icons: {
    icon: "/verimed-og.png",
    shortcut: "/verimed-og.png",
    apple: "/verimed-og.png",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://verimed-web.netlify.app",
    siteName: "VeriMed",
    title: "VeriMed — Medicine Authenticity Risk Assessment",
    description:
      "Upload medicine packaging photos and get instant risk assessment using OCR, barcode decoding, Ghana FDA reference matching, and explainable scoring. Free — no account needed.",
    images: [
      {
        url: "/verimed-og.png",
        width: 1200,
        height: 630,
        alt: "VeriMed — Medicine Authenticity Risk Assessment Tool",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "VeriMed — Medicine Authenticity Risk Assessment",
    description:
      "Upload medicine packaging photos and get instant risk assessment using OCR, barcode decoding, Ghana FDA reference matching, and explainable scoring.",
    images: ["/verimed-og.png"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0ea5e9",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <BackendKeepalive />
        {children}
      </body>
    </html>
  );
}
