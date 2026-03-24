"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ConversationMessage } from "@/lib/types";

interface Props {
  messages: ConversationMessage[];
  sending: boolean;
  onSend: (message: string) => Promise<void>;
  className?: string;
}

export default function FollowUpChat({ messages, sending, onSend, className }: Props) {
  const [draft, setDraft] = useState("");

  const markdownComponents = {
    p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
      <p className="my-1.5 leading-relaxed" {...props} />
    ),
    ul: (props: React.HTMLAttributes<HTMLUListElement>) => (
      <ul className="my-2 list-disc pl-5 space-y-1" {...props} />
    ),
    ol: (props: React.HTMLAttributes<HTMLOListElement>) => (
      <ol className="my-2 list-decimal pl-5 space-y-1" {...props} />
    ),
    li: (props: React.HTMLAttributes<HTMLLIElement>) => <li {...props} />,
    h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
      <h1 className="text-base font-semibold mt-2 mb-1" {...props} />
    ),
    h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
      <h2 className="text-sm font-semibold mt-2 mb-1" {...props} />
    ),
    h3: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
      <h3 className="text-sm font-semibold mt-2 mb-1" {...props} />
    ),
    code: (props: React.HTMLAttributes<HTMLElement>) => (
      <code className="px-1 py-0.5 rounded bg-slate-100 text-slate-800 text-[0.9em]" {...props} />
    ),
    pre: (props: React.HTMLAttributes<HTMLPreElement>) => (
      <pre className="my-2 p-3 rounded-lg bg-slate-900 text-slate-100 overflow-x-auto text-xs" {...props} />
    ),
    table: (props: React.HTMLAttributes<HTMLTableElement>) => (
      <div className="my-2 overflow-x-auto">
        <table className="w-full border-collapse text-xs" {...props} />
      </div>
    ),
    thead: (props: React.HTMLAttributes<HTMLTableSectionElement>) => (
      <thead className="bg-slate-100" {...props} />
    ),
    th: (props: React.HTMLAttributes<HTMLTableCellElement>) => (
      <th className="border border-slate-300 px-2 py-1 text-left font-semibold" {...props} />
    ),
    td: (props: React.HTMLAttributes<HTMLTableCellElement>) => (
      <td className="border border-slate-300 px-2 py-1 align-top" {...props} />
    ),
    blockquote: (props: React.HTMLAttributes<HTMLElement>) => (
      <blockquote className="my-2 pl-3 border-l-2 border-slate-300 text-slate-600" {...props} />
    ),
  };

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || sending) return;
    setDraft("");
    await onSend(text);
  };

  return (
    <section className={`rounded-2xl border border-gray-200 bg-white shadow-sm p-4 space-y-3 ${className ?? ""}`}>
      <div>
        <h2 className="text-sm font-semibold text-gray-900">Follow-up Conversation</h2>
        <p className="text-xs text-gray-500 mt-1">
          Ask about the score, missing signals, or what to verify next with a pharmacist.
        </p>
      </div>

      <div className="rounded-xl border border-gray-100 bg-gray-50 p-3 h-[44vh] md:h-[56vh] overflow-y-auto space-y-2">
        {messages.length === 0 && (
          <p className="text-xs text-gray-400">No messages yet.</p>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`max-w-[90%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
              message.role === "user"
                ? "ml-auto bg-blue-600 text-white"
                : "mr-auto bg-white text-gray-800 border border-gray-200"
            }`}
          >
            {message.role === "assistant" ? (
              <div className="text-sm text-slate-800">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <span>{message.content}</span>
            )}
          </div>
        ))}
        {sending && (
          <div className="mr-auto bg-white text-gray-600 border border-gray-200 rounded-xl px-3 py-2 text-sm">
            Thinking...
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              void handleSend();
            }
          }}
          placeholder="Example: Why did missing expiry lower the score?"
          className="flex-1 rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={sending}
        />
        <button
          onClick={() => void handleSend()}
          disabled={sending || !draft.trim()}
          className={`rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            sending || !draft.trim()
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          Send
        </button>
      </div>
    </section>
  );
}
