"use client";

import { useEffect, useRef, useState } from "react";
import { detectRealtimeProduct } from "@/lib/api";
import { RealtimeDetection } from "@/lib/types";

type CaptureSide = "front" | "back" | "barcode";

interface Props {
  side: CaptureSide;
  onCapture: (file: File) => void;
}

const POLL_MS = 500;

export default function RealtimeCameraPreview({ side, onCapture }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pollRef = useRef<number | null>(null);
  const busyRef = useRef(false);

  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [detections, setDetections] = useState<RealtimeDetection[]>([]);
  const [message, setMessage] = useState("Camera idle");

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const stopCamera = () => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsRunning(false);
  };

  const captureBlob = async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) return null;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return await new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.85);
    });
  };

  const pollDetection = async () => {
    if (busyRef.current) return;
    busyRef.current = true;

    try {
      const blob = await captureBlob();
      if (!blob) return;
      const frameFile = new File([blob], `frame-${Date.now()}.jpg`, { type: "image/jpeg" });
      const result = await detectRealtimeProduct(frameFile, side, 3);
      setDetections(result.detections);
      setMessage(result.message || "ok");
      setError("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Realtime detection failed.");
    } finally {
      busyRef.current = false;
    }
  };

  const startCamera = async () => {
    try {
      setError("");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (!videoRef.current) {
        setError("Camera preview is unavailable.");
        return;
      }

      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      setIsRunning(true);
      setMessage("Camera live");

      pollRef.current = window.setInterval(() => {
        void pollDetection();
      }, POLL_MS);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to access camera.");
      stopCamera();
    }
  };

  const handleToggle = async () => {
    if (isRunning) {
      stopCamera();
      setMessage("Camera stopped");
      return;
    }
    await startCamera();
  };

  const handleCapture = async () => {
    try {
      const blob = await captureBlob();
      if (!blob) {
        setError("No frame available to capture.");
        return;
      }
      const file = new File([blob], `${side}-${Date.now()}.jpg`, { type: "image/jpeg" });
      onCapture(file);
      setMessage(`✓ Captured ${side}. Switch to another side or click Done.`);
    } catch {
      setError("Capture failed.");
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Realtime camera ({side})</h2>
          <p className="text-xs text-slate-500">Captures and analyzes one frame every ~500ms.</p>
        </div>
        <div className="text-[11px] font-medium px-2 py-1 rounded-full bg-slate-100 text-slate-600">
          {isRunning ? "Live" : "Idle"}
        </div>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-slate-300 bg-slate-900 aspect-video">
        <video ref={videoRef} muted playsInline className="h-full w-full object-cover" />

        {detections.map((det) => (
          <div
            key={`${det.product_id}-${det.box.x}-${det.box.y}`}
            className="absolute border-2 border-lime-400 bg-lime-500/10"
            style={{
              left: `${(det.box.x / 1280) * 100}%`,
              top: `${(det.box.y / 720) * 100}%`,
              width: `${(det.box.width / 1280) * 100}%`,
              height: `${(det.box.height / 720) * 100}%`,
            }}
          >
            <div className="absolute -top-6 left-0 whitespace-nowrap rounded bg-lime-500 px-2 py-0.5 text-[10px] font-semibold text-slate-900">
              {det.product_label || det.product_id} • {(det.confidence * 100).toFixed(0)}%
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => void handleToggle()}
          className={`px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${
            isRunning ? "bg-gray-600 text-white hover:bg-gray-700" : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          {isRunning ? "Done" : "Start camera"}
        </button>

        <button
          onClick={() => void handleCapture()}
          disabled={!isRunning}
          className="px-3 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Capture {side}
        </button>
      </div>

      <div className="space-y-1">
        <p className="text-xs text-slate-500">{message}</p>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>
    </section>
  );
}
