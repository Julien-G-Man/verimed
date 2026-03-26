import Image from "next/image";
import Link from "next/link";

interface NavbarProps {
  /** Use "" on the landing page, "/" on other pages so anchor links resolve correctly */
  anchorPrefix?: string;
}

export default function Navbar({ anchorPrefix = "" }: NavbarProps) {
  const a = (hash: string) => `${anchorPrefix}${hash}`;

  return (
    <header className="absolute top-0 left-0 w-full px-4 py-4 sm:py-5 z-30">
      <div className="mx-auto max-w-6xl rounded-2xl border border-sky-100 bg-white/90 backdrop-blur-sm px-4 py-3 flex items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <Link href={a("#top")} scroll={false} aria-label="Go to top">
            <Image src="/verimed_logo.png" alt="VeriMed logo" width={220} height={52} className="h-8 sm:h-9 w-auto" priority />
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-5 text-sm text-slate-700">
          <Link href={a("#about")} className="hover:text-sky-700 transition-colors">About</Link>
          <Link href={a("#how-it-works")} className="hover:text-sky-700 transition-colors">How it works</Link>
          <Link href={a("#features")} className="hover:text-sky-700 transition-colors">Features</Link>
          <Link href={a("#faq")} className="hover:text-sky-700 transition-colors">FAQ</Link>
        </nav>

        <Link
          href="/verify"
          className="hidden md:inline-block text-xs sm:text-sm font-semibold px-3 sm:px-4 py-2 rounded-xl bg-sky-600 text-white hover:bg-sky-700 transition-colors"
        >
          Start
        </Link>

        <details className="md:hidden relative">
          <summary
            aria-label="Open navigation menu"
            className="list-none cursor-pointer text-slate-700 hover:text-sky-700 transition-colors p-2 rounded-lg hover:bg-slate-100"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M4 7H20M4 12H20M4 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </summary>
          <nav className="absolute right-0 mt-2 w-52 rounded-xl border border-slate-200 bg-white shadow-xl p-2 flex flex-col text-sm text-slate-700">
            <Link href={a("#about")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors">About</Link>
            <Link href={a("#how-it-works")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors">How it works</Link>
            <Link href={a("#features")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors">Features</Link>
            <Link href={a("#faq")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors">FAQ</Link>
            <Link
              href="/verify"
              className="mt-2 text-center bg-sky-600 hover:bg-sky-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
            >
              Start
            </Link>
          </nav>
        </details>
      </div>
    </header>
  );
}
