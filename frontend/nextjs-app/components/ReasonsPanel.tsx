"use client";
import { useState } from "react";
import { ScoringSignal } from "@/lib/types";

interface Props {
  signals: ScoringSignal[];
  reasons: string[];
}

export default function ReasonsPanel({ signals, reasons }: Props) {
  const [open, setOpen] = useState(false);
  const passed = signals.filter((s) => s.passed);
  const failed = signals.filter((s) => !s.passed);

  const contributionFor = (signal: ScoringSignal): number => {
    if (typeof signal.contribution === "number") {
      return signal.contribution;
    }
    if (signal.passed && signal.weight > 0) {
      return signal.weight;
    }
    if (!signal.passed && signal.weight < 0) {
      return signal.weight;
    }
    return 0;
  };

  const formatContribution = (value: number): string => {
    if (value > 0) {
      return `+${value}`;
    }
    if (value < 0) {
      return `${value}`;
    }
    return "0";
  };

  const totalContribution = signals.reduce((acc, signal) => acc + contributionFor(signal), 0);

  return (
    <div className="rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between p-4 text-sm font-semibold text-gray-700 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span>Scoring Signals ({signals.length})</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="p-4 bg-white space-y-4">
          {passed.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-green-700 mb-2 uppercase tracking-wide">Passed</div>
              <ul className="space-y-1.5">
                {passed.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                    <span>{s.reason}</span>
                    <span className="ml-auto text-xs text-green-600 font-medium shrink-0">{formatContribution(contributionFor(s))}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {failed.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-red-700 mb-2 uppercase tracking-wide">Failed / Penalties</div>
              <ul className="space-y-1.5">
                {failed.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-red-400 mt-0.5 shrink-0">✗</span>
                    <span>{s.reason}</span>
                    <span className="ml-auto text-xs text-red-500 font-medium shrink-0">{formatContribution(contributionFor(s))}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-sm">
            <span className="text-gray-500">Net score contribution</span>
            <span className="font-semibold text-gray-800">{formatContribution(totalContribution)}</span>
          </div>
          {reasons.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Summary</div>
              <ul className="space-y-1 text-sm text-gray-600 list-disc list-inside">
                {reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
