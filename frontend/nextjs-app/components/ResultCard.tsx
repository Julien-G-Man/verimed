"use client";
import { VerificationResult } from "@/lib/types";

const BADGE: Record<string, { label: string; bg: string; text: string; border: string }> = {
  low_risk:      { label: "Low Risk",      bg: "bg-green-100",  text: "text-green-800",  border: "border-green-300" },
  medium_risk:   { label: "Medium Risk",   bg: "bg-amber-100",  text: "text-amber-800",  border: "border-amber-300" },
  high_risk:     { label: "High Risk",     bg: "bg-red-100",    text: "text-red-800",    border: "border-red-300"   },
  cannot_verify: { label: "Cannot Verify", bg: "bg-gray-100",   text: "text-gray-700",   border: "border-gray-300"  },
};

export default function ResultCard({ result }: { result: VerificationResult }) {
  const badge = BADGE[result.classification] ?? BADGE.cannot_verify;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide">Identified product</div>
          <div className="text-lg font-bold text-gray-900 mt-0.5">
            {result.identified_product ?? "Unknown product"}
          </div>
        </div>
        <span className={`px-3 py-1.5 rounded-full text-sm font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}>
          {badge.label}
        </span>
      </div>

      {/* Score bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Risk Score</span>
          <span className="font-semibold text-gray-800">{result.risk_score} / 100</span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              result.classification === "low_risk" ? "bg-green-500" :
              result.classification === "medium_risk" ? "bg-amber-500" :
              result.classification === "high_risk" ? "bg-red-500" : "bg-gray-400"
            }`}
            style={{ width: `${result.risk_score}%` }}
          />
        </div>
      </div>

      {/* Explanation */}
      <div className="text-sm text-gray-700 leading-relaxed">{result.explanation}</div>

      {/* Recommendation */}
      <div className={`rounded-lg p-3 text-sm font-medium border ${badge.bg} ${badge.text} ${badge.border}`}>
        {result.recommendation}
      </div>
    </div>
  );
}
