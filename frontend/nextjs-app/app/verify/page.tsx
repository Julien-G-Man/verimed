"use client";
import { useState } from "react";
import FollowUpChat from "@/components/FollowUpChat";
import ImageUploadZone from "@/components/ImageUploadZone";
import RealtimeCameraPreview from "@/components/RealtimeCameraPreview";
import ResultCard from "@/components/ResultCard";
import ExtractedFieldsPanel from "@/components/ExtractedFieldsPanel";
import ReasonsPanel from "@/components/ReasonsPanel";
import UploadProgress from "@/components/UploadProgress";
import ResultSkeleton from "@/components/ResultSkeleton";
import { sendFollowUpMessage, startConversation, verifyMedicine } from "@/lib/api";
import { ConversationMessage, VerificationResult } from "@/lib/types";
import Link from "next/link";
import Image from "next/image";

type Status = "idle" | "loading" | "done" | "error";

export default function VerifyPage() {
  const [front, setFront] = useState<File | null>(null);
  const [back, setBack] = useState<File | null>(null);
  const [barcode, setBarcode] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [chatBusy, setChatBusy] = useState(false);
  const [chatError, setChatError] = useState("");
  const [cameraMode, setCameraMode] = useState<"front" | "back" | "barcode" | null>(null);

  const canSubmit = front && back && barcode && status !== "loading";

  const handleSubmit = async () => {
    if (!front || !back || !barcode) return;
    setStatus("loading");
    setResult(null);
    setErrorMsg("");
    try {
      const res = await verifyMedicine(front, back, barcode);
      setResult(res);

      try {
        const conv = await startConversation(res);
        setConversationId(conv.conversation_id);
        setMessages(conv.messages);
      } catch {
        setConversationId(null);
        setMessages([]);
      }

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
    setConversationId(null);
    setMessages([]);
    setChatBusy(false);
    setChatError("");
  };

  const handleSendFollowUp = async (message: string) => {
    if (!conversationId) {
      setChatError("Conversation is not available for this result.");
      return;
    }

    const optimisticUserMessage: ConversationMessage = {
      id: `temp-user-${Date.now()}`,
      conversation_id: conversationId,
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMessage]);
    setChatBusy(true);
    setChatError("");

    try {
      const updated = await sendFollowUpMessage(conversationId, message);
      setMessages(updated.messages);
    } catch (err: unknown) {
      setMessages((prev) => prev.filter((item) => item.id !== optimisticUserMessage.id));
      setChatError(err instanceof Error ? err.message : "Failed to send follow-up question.");
    } finally {
      setChatBusy(false);
    }
  };

  return (
    <div className="min-h-screen page-bg">
      <header className="bg-white/85 backdrop-blur-sm border-b border-slate-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Link href="/" className="text-gray-400 hover:text-gray-600 text-xl shrink-0" aria-label="Back to home">←</Link>
            <Image src="/verimed_logo.png" alt="VeriMed logo" width={32} height={32} className="rounded-md shrink-0" priority />
            <h1 className="text-sm sm:text-base font-semibold text-gray-900 truncate">Verify Medicine</h1>
          </div>
          <span className="hidden sm:inline text-xs px-2 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-100">3 photos required</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Upload slots */}
        <div className="space-y-3 animate-rise-in max-w-3xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <p className="text-sm text-gray-500">Upload 3 photos of the medicine packaging.</p>
            <button
              onClick={() => setCameraMode(cameraMode ? null : "front")}
              className="w-full sm:w-auto text-xs font-medium px-3 py-2 rounded-lg border border-slate-300 hover:bg-slate-100 transition-colors"
            >
              {cameraMode ? "📷 Hide camera" : "📷 Use camera"}
            </button>
          </div>

          {cameraMode && (
            <div className="space-y-3">
              <RealtimeCameraPreview
                side={cameraMode}
                onCapture={(file) => {
                  if (cameraMode === "front") setFront(file);
                  else if (cameraMode === "back") setBack(file);
                  else if (cameraMode === "barcode") setBarcode(file);
                }}
              />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  onClick={() => setCameraMode("front")}
                  className={`py-2 px-3 text-xs font-semibold rounded-lg transition-colors ${
                    cameraMode === "front"
                      ? front
                        ? "bg-emerald-100 border border-emerald-400 text-emerald-800"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {front ? "✓ Front" : "Front"}
                </button>
                <button
                  onClick={() => setCameraMode("back")}
                  className={`py-2 px-3 text-xs font-semibold rounded-lg transition-colors ${
                    cameraMode === "back"
                      ? back
                        ? "bg-emerald-100 border border-emerald-400 text-emerald-800"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {back ? "✓ Back" : "Back"}
                </button>
                <button
                  onClick={() => setCameraMode("barcode")}
                  className={`py-2 px-3 text-xs font-semibold rounded-lg transition-colors ${
                    cameraMode === "barcode"
                      ? barcode
                        ? "bg-emerald-100 border border-emerald-400 text-emerald-800"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {barcode ? "✓ Code" : "Code"}
                </button>
              </div>
              {front && back && barcode && (
                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-center">
                  <p className="text-xs font-semibold text-emerald-800">✓ All sides captured!</p>
                  <button
                    onClick={() => setCameraMode(null)}
                    className="mt-2 text-xs px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                  >
                    Close camera & verify
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="flex flex-col gap-2">
              <ImageUploadZone label="Front" sublabel="Main label" file={front} onChange={setFront} />
              {front && (
                <button
                  onClick={() => setCameraMode(cameraMode === "front" ? null : "front")}
                  className="text-xs px-2 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors"
                >
                  {cameraMode === "front" ? "Hide camera" : "Retake with camera"}
                </button>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <ImageUploadZone label="Back" sublabel="Ingredients" file={back} onChange={setBack} />
              {back && (
                <button
                  onClick={() => setCameraMode(cameraMode === "back" ? null : "back")}
                  className="text-xs px-2 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors"
                >
                  {cameraMode === "back" ? "Hide camera" : "Retake with camera"}
                </button>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <ImageUploadZone label="Barcode" sublabel="QR / barcode" file={barcode} onChange={setBarcode} />
              {barcode && (
                <button
                  onClick={() => setCameraMode(cameraMode === "barcode" ? null : "barcode")}
                  className="text-xs px-2 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors"
                >
                  {cameraMode === "barcode" ? "Hide camera" : "Retake with camera"}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Submit */}
        {status !== "done" && status !== "loading" && (
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`w-full max-w-3xl py-3 rounded-xl text-sm font-semibold transition-colors
              ${canSubmit
                ? "bg-blue-600 hover:bg-blue-700 text-white"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"}`}
          >
            Verify Medicine
          </button>
        )}

        {/* Loading */}
        {status === "loading" && (
          <div className="space-y-4 animate-rise-in max-w-2xl">
            <UploadProgress />
            <ResultSkeleton />
          </div>
        )}

        {/* Error */}
        {status === "error" && (
          <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 max-w-2xl">
            <p className="font-medium mb-1">Verification failed</p>
            <p>{errorMsg}</p>
            <button onClick={handleReset} className="mt-2 text-red-600 underline text-xs">Try again</button>
          </div>
        )}

        {/* Results */}
        {status === "done" && result && (
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-4 animate-rise-in items-start">
            <section className="space-y-4 min-w-0">
              <ResultCard result={result} />
              <ExtractedFieldsPanel extraction={result.extraction} barcode={result.barcode} />
              <ReasonsPanel signals={result.scoring.signals} reasons={result.reasons} />
              <button
                onClick={handleReset}
                className="w-full py-3 rounded-xl text-sm font-semibold border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Verify another medicine
              </button>
            </section>

            <aside className="xl:sticky xl:top-20 space-y-3 min-w-0">
              {conversationId ? (
                <FollowUpChat
                  messages={messages}
                  sending={chatBusy}
                  onSend={handleSendFollowUp}
                />
              ) : (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  Follow-up assistant is unavailable for this verification result.
                </div>
              )}

              {chatError && (
                <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                  {chatError}
                </div>
              )}
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
