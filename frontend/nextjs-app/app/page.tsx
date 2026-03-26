import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen page-bg flex flex-col items-center justify-center px-6 text-center">
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

        <div className="grid grid-cols-3 gap-3 pt-2">
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
    </main>
  );
}
