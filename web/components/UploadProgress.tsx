"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Validating images",
  "Extracting text and barcode",
  "Scoring consistency",
  "Generating explanation",
];

export default function UploadProgress() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STEPS.length);
    }, 1200);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-sky-300 bg-white text-sky-600">
          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
            <path d="M12 2a10 10 0 0 1 10 10h-4a6 6 0 0 0-6-6V2z" fill="currentColor" className="opacity-80" />
          </svg>
        </span>
        <div>
          <p className="text-sm font-semibold text-sky-900">Analyzing your medicine package</p>
          <p className="text-xs text-sky-700">This usually takes a few seconds.</p>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {STEPS.map((step, index) => {
          const done = index < activeStep;
          const active = index === activeStep;

          return (
            <div key={step} className="flex items-center gap-2 text-xs">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  done ? "bg-emerald-500" : active ? "bg-sky-500 animate-pulse" : "bg-sky-200"
                }`}
              />
              <span className={done || active ? "text-sky-900" : "text-sky-600"}>{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}