import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <main className="min-h-screen page-bg">
      <header className="w-full px-4 pt-4 sm:pt-5">
        <div className="mx-auto max-w-5xl rounded-2xl border border-sky-100 bg-white/90 backdrop-blur-sm px-4 py-3 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <Image src="/verimed_logo.png" alt="VeriMed logo" width={36} height={36} className="rounded-md" priority />
            <span className="text-sm sm:text-base font-semibold text-slate-900">VeriMed</span>
          </div>
          <span className="text-[11px] sm:text-xs px-2 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-100">Risk Assessment</span>
        </div>
      </header>

      <section className="px-4 py-8 sm:py-12 flex flex-col items-center text-center">
      <div className="max-w-sm w-full space-y-6 animate-rise-in">
        <div className="space-y-2">
          <div className="text-5xl">💊</div>
          <h1 className="text-3xl font-bold text-slate-900">VeriMed</h1>
          <p className="text-gray-500 text-sm leading-relaxed">
            An AI-powered medicine authenticity risk assessment tool. Upload or capture photos of your medicine packaging to check for warning signs of counterfeiting.
          </p>
        </div>

        <Link
          href="/verify"
          className="block w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-4 rounded-2xl text-sm transition-colors shadow-lg shadow-sky-200"
        >
          Verify a Medicine
        </Link>

        <p className="text-xs text-gray-400 leading-relaxed">
          This tool provides risk assessment only — not regulatory certification. Always consult a pharmacist if in doubt.
        </p>

        <div className="grid grid-cols-3 gap-2 sm:gap-3 pt-2">
          {[
            { icon: "🔍", label: "OCR scanning" },
            { icon: "📊", label: "Barcode check" },
            { icon: "🤖", label: "AI explanation" },
          ].map(({ icon, label }) => (
            <div key={label} className="bg-white/95 rounded-xl p-3 border border-sky-100 shadow-sm text-center">
              <div className="text-xl">{icon}</div>
              <div className="text-xs text-gray-500 mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>
      </section>
    </main>
  );
}
