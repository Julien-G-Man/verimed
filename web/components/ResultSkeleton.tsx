"use client";

export default function ResultSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="h-4 w-28 rounded bg-slate-200 animate-pulse" />
        <div className="mt-3 h-7 w-52 rounded bg-slate-200 animate-pulse" />
        <div className="mt-4 h-2 w-full rounded bg-slate-100" />
        <div className="mt-2 h-2 w-3/4 rounded bg-slate-200 animate-pulse" />
        <div className="mt-5 space-y-2">
          <div className="h-3 w-full rounded bg-slate-200 animate-pulse" />
          <div className="h-3 w-5/6 rounded bg-slate-200 animate-pulse" />
          <div className="h-3 w-2/3 rounded bg-slate-200 animate-pulse" />
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="h-4 w-40 rounded bg-slate-200 animate-pulse" />
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="h-3 rounded bg-slate-200 animate-pulse" />
          <div className="h-3 rounded bg-slate-200 animate-pulse" />
          <div className="h-3 rounded bg-slate-200 animate-pulse" />
          <div className="h-3 rounded bg-slate-200 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
