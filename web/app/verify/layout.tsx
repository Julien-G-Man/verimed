import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Verify a Medicine",
  description:
    "Upload photos of medicine packaging — front label, back side, and barcode — to get an instant authenticity risk assessment using OCR, barcode decoding, and Ghana FDA reference matching.",
  openGraph: {
    title: "Verify a Medicine — VeriMed",
    description:
      "Upload photos of medicine packaging to get an instant authenticity risk assessment. Free, no account needed.",
    url: "https://verimed-web.netlify.app/verify",
  },
};

export default function VerifyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
