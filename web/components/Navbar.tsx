"use client";

import Image from "next/image";
import Link from "next/link";
import { MouseEvent, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

interface NavbarProps {
  /** Use "/" so section links resolve cleanly from both the landing page and inner pages */
  anchorPrefix?: string;
  sticky?: boolean;
}

export default function Navbar({ anchorPrefix = "", sticky = false }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const a = (hash: string) => `${anchorPrefix}${hash}`;
  const headerClassName = sticky
    ? "fixed top-0 left-0 w-full px-4 py-4 sm:py-5 z-30"
    : "absolute top-0 left-0 w-full px-4 py-4 sm:py-5 z-30";

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [menuOpen]);

  const handleLogoClick = (event: MouseEvent<HTMLAnchorElement>) => {
    setMenuOpen(false);

    if (pathname !== "/") {
      return;
    }

    event.preventDefault();
    router.replace("/", { scroll: false });
    window.history.replaceState(null, "", "/");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <header className={headerClassName}>
      <div className="mx-auto max-w-6xl rounded-2xl border border-white/40 bg-white/70 backdrop-blur-md px-4 py-3 flex items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <Link href="/" scroll={false} aria-label="Go to top" onClick={handleLogoClick}>
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

        <div className="md:hidden relative" ref={menuRef}>
          <button
            type="button"
            aria-label="Open navigation menu"
            aria-expanded={menuOpen}
            className="list-none cursor-pointer text-slate-700 hover:text-sky-700 transition-colors p-2 rounded-lg hover:bg-slate-100"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M4 7H20M4 12H20M4 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
          {menuOpen ? (
            <nav className="absolute right-0 mt-2 w-52 rounded-xl border border-slate-200 bg-white/95 shadow-xl backdrop-blur-md p-2 flex flex-col text-sm text-slate-700">
              <Link href={a("#about")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors" onClick={() => setMenuOpen(false)}>About</Link>
              <Link href={a("#how-it-works")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors" onClick={() => setMenuOpen(false)}>How it works</Link>
              <Link href={a("#features")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors" onClick={() => setMenuOpen(false)}>Features</Link>
              <Link href={a("#faq")} className="px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors" onClick={() => setMenuOpen(false)}>FAQ</Link>
              <Link
                href="/verify"
                className="mt-2 text-center bg-sky-600 hover:bg-sky-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
                onClick={() => setMenuOpen(false)}
              >
                Start
              </Link>
            </nav>
          ) : null}
        </div>
      </div>
    </header>
  );
}
