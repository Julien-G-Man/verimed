"use client";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";

interface Props {
  label: string;
  sublabel: string;
  file: File | null;
  onChange: (file: File) => void;
}

export default function ImageUploadZone({ label, sublabel, file, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) onChange(dropped);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed cursor-pointer transition-colors min-h-[140px] p-3
        ${dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50 hover:bg-gray-100"}
        ${file ? "border-green-400 bg-green-50" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onChange(f); }}
      />
      {preview ? (
        <div className="relative h-24 w-full">
          <Image
            src={preview}
            alt={label}
            fill
            sizes="120px"
            className="rounded object-contain"
            unoptimized
          />
        </div>
      ) : (
        <div className="text-center">
          <div className="text-3xl mb-1">📷</div>
          <div className="text-sm font-semibold text-gray-700">{label}</div>
          <div className="text-xs text-gray-400 mt-0.5">{sublabel}</div>
        </div>
      )}
      {file && (
        <div className="mt-1 text-xs text-green-600 truncate max-w-full">{file.name}</div>
      )}
    </div>
  );
}
