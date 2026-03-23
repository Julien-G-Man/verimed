"use client";
import { useState } from "react";
import { ExtractedFields, BarcodeResult } from "@/lib/types";

interface Props {
  extraction: ExtractedFields;
  barcode: BarcodeResult;
}

const Field = ({ label, value }: { label: string; value: string | null | undefined }) =>
  value ? (
    <div className="flex justify-between gap-2 text-sm py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="text-gray-900 font-medium text-right">{value}</span>
    </div>
  ) : null;

export default function ExtractedFieldsPanel({ extraction, barcode }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between p-4 text-sm font-semibold text-gray-700 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span>Extracted Fields</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="p-4 space-y-0 bg-white">
          <Field label="Brand name" value={extraction.brand_name} />
          <Field label="Generic name" value={extraction.generic_name} />
          <Field label="Strength" value={extraction.strength} />
          <Field label="Dosage form" value={extraction.dosage_form} />
          <Field label="Manufacturer" value={extraction.manufacturer} />
          <Field label="Batch number" value={extraction.batch_number} />
          <Field label="Expiry date" value={extraction.expiry_date} />
          <Field label="Barcode" value={barcode.decoded ? `${barcode.code_type}: ${barcode.value}` : "Not decoded"} />
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-400 mb-1">OCR confidence</div>
            <div className="text-xs text-gray-600">
              Front: {(extraction.ocr_confidence_front * 100).toFixed(0)}% · Back: {(extraction.ocr_confidence_back * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
