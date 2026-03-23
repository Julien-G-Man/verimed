"use client";
import { useState } from "react";
import ImageUploadZone from "@/components/ImageUploadZone";
import ResultCard from "@/components/ResultCard";
import ExtractedFieldsPanel from "@/components/ExtractedFieldsPanel";
import ReasonsPanel from "@/components/ReasonsPanel";
import UploadProgress from "@/components/UploadProgress";
import ResultSkeleton from "@/components/ResultSkeleton";
import { verifyMedicine } from "@/lib/api";
import { VerificationResult } from "@/lib/types";
import Link from "next/link";

type Status = "idle" | "loading" | "done" | "error";

export default function VerifyPage() {
  const [front, setFront] = useState<File | null>(null);
  const [back, setBack] = useState<File | null>(null);
  const [barcode, setBarcode] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const canSubmit = front && back && barcode && status !== "loading";

  const handleSubmit = async () => {
    if (!front || !back || !barcode) return;
    setStatus("loading");
    setResult(null);
    setErrorMsg("");
    try {
      const res = await verifyMedicine(front, back, barcode);
      setResult(res);
      setStatus("done");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Verification failed. Please try again.");
      setStatus("error");
    }
  };

  const handleReset = () => {
    setFront(null);
    setBack(null);
    setBarcode(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
  };

  return (
    <div className="min-h-screen page-bg">
      <header className="bg-white/85 backdrop-blur-sm border-b border-slate-200 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <Link href="/" className="text-gray-400 hover:text-gray-600 text-xl">←</Link>
        <h1 className="text-base font-semibold text-gray-900">Verify Medicine</h1>
      </header>

      <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
        {/* Upload slots */}
        <div className="space-y-3 animate-rise-in">
          <p className="text-sm text-gray-500">Upload 3 photos of the medicine packaging.</p>
          <div className="grid grid-cols-3 gap-3">
            <ImageUploadZone label="Front" sublabel="Main label" file={front} onChange={setFront} />
            <ImageUploadZone label="Back" sublabel="Ingredients" file={back} onChange={setBack} />
            <ImageUploadZone label="Barcode" sublabel="QR / barcode" file={barcode} onChange={setBarcode} />
          </div>
        </div>

        {/* Submit */}
        {status !== "done" && status !== "loading" && (
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`w-full py-3 rounded-xl text-sm font-semibold transition-colors
              ${canSubmit
                ? "bg-blue-600 hover:bg-blue-700 text-white"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"}`}
          >
            Verify Medicine
          </button>
        )}

        {/* Loading */}
        {status === "loading" && (
          <div className="space-y-4 animate-rise-in">
            <UploadProgress />
            <ResultSkeleton />
          </div>
        )}

        {/* Error */}
        {status === "error" && (
          <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">
            <p className="font-medium mb-1">Verification failed</p>
            <p>{errorMsg}</p>
            <button onClick={handleReset} className="mt-2 text-red-600 underline text-xs">Try again</button>
          </div>
        )}

        {/* Results */}
        {status === "done" && result && (
          <div className="space-y-4 animate-rise-in">
            <ResultCard result={result} />
            <ExtractedFieldsPanel extraction={result.extraction} barcode={result.barcode} />
            <ReasonsPanel signals={result.scoring.signals} reasons={result.reasons} />
            <button
              onClick={handleReset}
              className="w-full py-3 rounded-xl text-sm font-semibold border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors"
            >
              Verify another medicine
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
