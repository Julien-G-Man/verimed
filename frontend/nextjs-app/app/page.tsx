import Link from "next/link";
import Navbar from "@/components/Navbar";

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebApplication",
      "@id": "https://verimed-web.netlify.app/#app",
      name: "VeriMed",
      url: "https://verimed-web.netlify.app",
      description:
        "AI-powered medicine authenticity risk assessment tool. Upload photos of medicine packaging to get OCR text extraction, barcode verification, Ghana FDA reference matching, and an explainable risk score.",
      applicationCategory: "HealthApplication",
      operatingSystem: "Any",
      browserRequirements: "Requires JavaScript",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
      featureList: [
        "OCR text extraction from medicine packaging",
        "Barcode and QR code decoding",
        "Ghana FDA reference dataset matching",
        "Deterministic weighted risk scoring",
        "Plain-language AI explanation",
        "Follow-up assistant for contextual questions",
      ],
    },
    {
      "@type": "FAQPage",
      "@id": "https://verimed-web.netlify.app/#faq",
      mainEntity: [
        {
          "@type": "Question",
          name: "Does VeriMed certify medicine as genuine?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "No. VeriMed provides a risk assessment, not a certificate of authenticity. It identifies signals that are consistent or inconsistent with a known product. Only a laboratory or regulatory authority can certify a medicine.",
          },
        },
        {
          "@type": "Question",
          name: "What images should I upload?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Three clear photos: the front label (brand name, strength), the back or ingredients side, and a close-up of the barcode or QR code. Good lighting and a steady hand make a big difference to accuracy.",
          },
        },
        {
          "@type": "Question",
          name: "What does the risk score mean?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "The score runs from 0 to 100 and reflects how closely the packaging details match a verified reference record. Low risk (80+) means strong consistency. Medium risk (50–79) means some signals are off. High risk (below 50) means significant mismatches were found. Cannot verify means the product is not in the reference dataset.",
          },
        },
        {
          "@type": "Question",
          name: "What if no product is matched?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "You will get a cannot verify result. This does not mean the medicine is fake — it means VeriMed could not find it in the reference dataset. Treat it as a caution signal and consult a pharmacist before use.",
          },
        },
        {
          "@type": "Question",
          name: "Are my images stored or shared?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "No. Images are processed entirely in memory and discarded immediately after verification. VeriMed does not store, log, or share your uploaded photos.",
          },
        },
        {
          "@type": "Question",
          name: "What should I do if I get a high risk result?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Do not discard the medicine immediately. Note the batch number and expiry date, stop using the product, and report it to your pharmacist or the Ghana FDA. A high risk result means the packaging raised significant warning signs — professional guidance is essential.",
          },
        },
      ],
    },
  ],
};

export default function Home() {
  return (
    <main className="min-h-screen page-bg relative">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Navbar anchorPrefix="/" sticky />

      <section
        className="hero-section w-full min-h-[70vh] sm:min-h-[74vh] animate-rise-in bg-slate-900 flex items-end"
        style={{
          backgroundImage: "linear-gradient(90deg, rgba(2,6,23,0.84) 0%, rgba(2,6,23,0.68) 43%, rgba(2,6,23,0.36) 100%), url('/drugs-on-desk.jpg')",
        }}
      >
        <div className="w-full px-4 pt-28 pb-7 sm:px-8 sm:pt-32 sm:pb-10 lg:px-12 lg:pt-36 lg:pb-14">
          <div className="mx-auto max-w-6xl">
            <div className="max-w-xl lg:max-w-2xl">
              <h1 className="mt-4 text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white leading-[0.96]">
                Verify Medicines.
                <br />
                Protect Your Health.
              </h1>
              <p className="mt-4 text-sm sm:text-base text-slate-100/90 leading-relaxed max-w-xl">
                Upload medicine package photos and get a transparent risk assessment powered by OCR,
                barcode checks, trusted reference matching, and explainable scoring.
              </p>

              <div className="mt-7 flex flex-col sm:flex-row gap-3">
                <Link
                  href="/verify"
                  className="text-center w-full sm:w-auto bg-sky-500 hover:bg-sky-600 text-white font-semibold px-6 py-3 rounded-2xl text-sm transition-colors"
                >
                  Start Verification
                </Link>
                <Link
                  href="/#how-it-works"
                  className="text-center w-full sm:w-auto bg-white/10 border border-white/35 hover:bg-white/20 text-white font-semibold px-6 py-3 rounded-2xl text-sm transition-colors"
                >
                  How It Works
                </Link>
              </div>

              <p className="mt-4 text-xs text-white/80">
                Risk assessment only, not regulatory certification. Consult a pharmacist when in doubt.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="anchor-section px-4 py-6 sm:py-10">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs uppercase tracking-[0.14em] font-semibold text-sky-700">About VeriMed</p>
          <h2 className="mt-2 text-4xl sm:text-5xl font-extrabold text-slate-900 leading-[0.98] max-w-4xl">
            Confidence in
            <span className="text-sky-700"> Medicine Verification</span>
          </h2>

          <div className="mt-7 grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-600">
            <div>
              <h3 className="text-xl font-bold text-slate-900">Why VeriMed?</h3>
              <p className="mt-3 text-base leading-relaxed">
                Counterfeit medicines are a real risk. Most people can&apos;t easily tell if a medicine is genuine just by looking at the packaging. Batch numbers, expiry dates, and barcodes can be confusing or misleading.
              </p>
              <p className="mt-3 text-base leading-relaxed">
                VeriMed gives you a simple way to check. It turns complex packaging details into a clear risk assessment, so you can make safer choices in seconds.
              </p>
            </div>

            <div>
              <h3 className="text-xl font-bold text-slate-900">What to expect</h3>
              <p className="mt-3 text-base leading-relaxed">
                VeriMed provides a <strong className="text-slate-800">risk assessment</strong>, not a certificate of authenticity. It will never tell you a product is definitely real or definitely fake — that level of certainty requires laboratory testing.
              </p>
              <p className="mt-3 text-base leading-relaxed">
                A <strong className="text-slate-800">cannot verify</strong> result means the product is not in the reference dataset — this is important information, not a failure. Always consult a pharmacist if you have any doubt about a medicine.
              </p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/verify"
              className="inline-flex items-center justify-center bg-sky-600 hover:bg-sky-700 text-white font-semibold px-5 py-3 rounded-xl text-sm transition-colors"
            >
              Start Verification
            </Link>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="anchor-section px-4 py-6 sm:py-10">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs uppercase tracking-[0.14em] font-semibold text-sky-700">How It Works</p>
          <h2 className="mt-2 text-4xl sm:text-5xl font-extrabold text-slate-900 leading-[0.98] max-w-4xl">
            From photo to result
            <span className="text-sky-700"> in six steps</span>
          </h2>

          <div className="mt-7 space-y-6">
            {/* Steps 1 & 2 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 1</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">Open VeriMed</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">Go to the VeriMed web app on any phone or computer. No account, no app download, no setup required.</p>
              </div>
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 2</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">Upload 3 photos</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">Upload a clear photo of the <strong className="text-slate-700">front label</strong>, the <strong className="text-slate-700">back / ingredients side</strong>, and the <strong className="text-slate-700">barcode or QR code</strong>. You can use your camera directly or pick from your gallery. VeriMed checks each photo for blur before proceeding.</p>
              </div>
            </div>
            {/* Steps 3 & 4 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 3</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">VeriMed reads your packaging</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">Optical character recognition (OCR) extracts the brand name, strength, dosage form, batch number, and expiry date from your photos. The barcode or QR code is decoded separately and compared against the reference record.</p>
              </div>
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 4</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">Your data is matched and scored</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">Extracted details are compared against a curated Ghana FDA reference dataset. A risk score is then calculated using fixed, transparent weighted rules — every point added or deducted corresponds to a specific signal you can see in your result.</p>
              </div>
            </div>
            {/* Steps 5 & 6 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 5</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">Review your result</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">You&apos;ll see a risk level — <strong className="text-emerald-700">low</strong>, <strong className="text-amber-600">medium</strong>, <strong className="text-red-600">high</strong>, or <strong className="text-slate-500">cannot verify</strong> — a breakdown of every signal that contributed to the score, and a plain-language explanation. A <em>cannot verify</em> result means the product is not in the reference dataset; treat it as a caution signal.</p>
              </div>
              <div className="rounded-2xl bg-white border border-slate-200 p-5 flex flex-col">
                <p className="text-xs sm:text-sm font-semibold text-sky-700">STEP 6</p>
                <h3 className="mt-2 text-lg font-bold text-slate-900 leading-tight">Ask questions & decide</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">Use the built-in assistant panel to ask follow-up questions about your specific result. VeriMed supports your decision — it does not replace professional advice. If you are unsure about a medicine, always consult a pharmacist before use.</p>
              </div>
            </div>
          </div>
        </div>
      </section>



      <section id="features" className="anchor-section px-4 py-6 sm:py-10">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs uppercase tracking-[0.14em] font-semibold text-sky-700">Features</p>
          <h2 className="mt-2 text-4xl sm:text-5xl font-extrabold text-slate-900 leading-[0.98] max-w-4xl">
            How VeriMed
            <span className="text-sky-700"> Works Under the Hood</span>
          </h2>

          <div className="mt-7 grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">OCR Text Extraction</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Reads the packaging for you</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                VeriMed uses optical character recognition to extract brand name, strength, dosage form, batch number, and expiry date directly from your photos — no manual typing required.
              </p>
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">Barcode & QR Decoding</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Checks the code, not just the label</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Barcodes and QR codes are decoded and cross-referenced against the reference dataset. A mismatch between the barcode and the printed label is a strong counterfeit signal.
              </p>
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">Ghana FDA Reference Matching</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Matched against real registry data</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Extracted details are compared against a curated dataset of Ghana FDA-registered medicines using fuzzy matching — accounting for OCR variations and formatting differences.
              </p>
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">Deterministic Weighted Scoring</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Transparent rules, not AI guesswork</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Every field match or mismatch contributes a defined score. The final risk level — low, medium, high, or cannot verify — follows fixed thresholds. You can see exactly why a result was given.
              </p>
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">Plain-language Explanation</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Results you can actually understand</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                After scoring, an AI assistant summarizes the result in 2–4 plain sentences — translating technical signals into clear guidance without making certification claims.
              </p>
            </div>

            <div className="rounded-2xl bg-white border border-slate-200 p-5">
              <p className="text-xs font-semibold text-sky-700 uppercase tracking-wide">Follow-up Assistant</p>
              <h3 className="mt-2 text-base font-bold text-slate-900">Ask questions about your result</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                A built-in assistant panel lets you ask follow-up questions about the specific result you received — without starting a new verification or leaving the page.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="faq" className="anchor-section px-4 py-6 sm:py-10 pb-12 sm:pb-16">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs uppercase tracking-[0.14em] font-semibold text-sky-700">FAQ</p>
          <h2 className="mt-2 text-4xl sm:text-5xl font-extrabold text-slate-900 leading-[0.98] max-w-4xl">
            Common
            <span className="text-sky-700"> questions</span>
          </h2>

          <div className="mt-7 space-y-3">
            {[
              [
                "Does VeriMed certify medicine as genuine?",
                "No. VeriMed provides a risk assessment, not a certificate of authenticity. It identifies signals that are consistent or inconsistent with a known product. Only a laboratory or regulatory authority can certify a medicine."
              ],
              [
                "What images should I upload?",
                "Three clear photos: the front label (brand name, strength), the back or ingredients side, and a close-up of the barcode or QR code. Good lighting and a steady hand make a big difference to accuracy."
              ],
              [
                "What does the risk score mean?",
                "The score runs from 0 to 100 and reflects how closely the packaging details match a verified reference record. Low risk (80+) means strong consistency. Medium risk (50–79) means some signals are off. High risk (below 50) means significant mismatches were found. Cannot verify means the product is not in the reference dataset."
              ],
              [
                "What if no product is matched?",
                "You will get a cannot verify result. This does not mean the medicine is fake — it means VeriMed could not find it in the reference dataset. Treat it as a caution signal and consult a pharmacist before use."
              ],
              [
                "Are my images stored or shared?",
                "No. Images are processed entirely in memory and discarded immediately after verification. VeriMed does not store, log, or share your uploaded photos."
              ],
              [
                "What should I do if I get a high risk result?",
                "Do not discard the medicine immediately. Note the batch number and expiry date, stop using the product, and report it to your pharmacist or the Ghana FDA. A high risk result means the packaging raised significant warning signs — professional guidance is essential."
              ],
            ].map(([q, a]) => (
              <details key={q} className="group rounded-2xl border border-slate-200 bg-white overflow-hidden">
                <summary className="flex items-center justify-between cursor-pointer px-5 py-4 text-sm font-semibold text-slate-900 select-none group-open:text-sky-700 hover:bg-slate-50 transition-colors">
                  {q}
                  <span className="ml-4 shrink-0 transition-transform duration-200 group-open:rotate-180">
                    <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M5 8l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  </span>
                </summary>
                <div className="px-5 pb-4 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
                  {a}
                </div>
              </details>
            ))}
          </div>

          <div className="mt-8">
            <Link
              href="/verify"
              className="inline-flex items-center justify-center bg-sky-600 hover:bg-sky-700 text-white font-semibold px-5 py-3 rounded-2xl text-sm transition-colors"
            >
              Verify a Medicine Now
            </Link>
          </div>
        </div>
      </section>

      <footer className="w-full bg-[#0b1741] text-white flex flex-col items-center justify-center min-h-[120px] py-8 mt-12">
        <div className="text-center text-sm sm:text-base font-medium">
          VeriMed provides risk assessment support and should not replace professional medical guidance.
        </div>
        <div className="mt-2 text-xs text-slate-200">&copy; {new Date().getFullYear()} VeriMed. All rights reserved.</div>
      </footer>
    </main>
  );
}
