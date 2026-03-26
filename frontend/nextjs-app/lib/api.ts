import {
  ConversationListResponse,
  ConversationResponse,
  RealtimeDetectionResponse,
  VerificationResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function verifyMedicine(
  frontImage: File,
  backImage: File,
  barcodeImage: File
): Promise<VerificationResult> {
  const formData = new FormData();
  formData.append("front_image", frontImage);
  formData.append("back_image", backImage);
  formData.append("barcode_image", barcodeImage);

  const response = await fetch(`${API_BASE}/api/verify`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: `Request failed with HTTP ${response.status}` }));

    const detail =
      typeof error?.detail === "string"
        ? error.detail
        : Array.isArray(error?.detail)
          ? error.detail.map((item: unknown) => {
              if (typeof item === "string") return item;
              if (typeof item === "object" && item !== null && "msg" in item) {
                return String((item as { msg?: unknown }).msg ?? "Validation error");
              }
              return "Validation error";
            }).join("; ")
          : `Request failed with HTTP ${response.status}`;

    throw new Error(detail);
  }

  return response.json();
}

export async function startConversation(verification: VerificationResult): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE}/api/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ verification }),
  });

  if (!response.ok) {
    throw new Error(`Failed to start conversation (HTTP ${response.status})`);
  }

  return response.json();
}

export async function sendFollowUpMessage(
  conversationId: string,
  message: string
): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const detail = await response
      .json()
      .then((data) => (typeof data?.detail === "string" ? data.detail : null))
      .catch(() => null);
    throw new Error(detail ?? `Failed to send follow-up question (HTTP ${response.status})`);
  }

  return response.json();
}

export async function getConversation(conversationId: string): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: "GET",
  });

  if (!response.ok) {
    const detail = await response
      .json()
      .then((data) => (typeof data?.detail === "string" ? data.detail : null))
      .catch(() => null);
    throw new Error(detail ?? `Failed to load conversation (HTTP ${response.status})`);
  }

  return response.json();
}

export async function listConversations(limit = 100): Promise<ConversationListResponse> {
  const response = await fetch(`${API_BASE}/api/conversations?limit=${limit}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Failed to load conversations (HTTP ${response.status})`);
  }

  return response.json();
}

export async function clearAllConversationHistory(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/conversations/history`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to clear conversation history (HTTP ${response.status})`);
  }
}

export async function detectRealtimeProduct(
  frameImage: File,
  side: "front" | "back" | "barcode" = "front",
  topK = 3
): Promise<RealtimeDetectionResponse> {
  const formData = new FormData();
  formData.append("frame_image", frameImage);
  formData.append("side", side);
  formData.append("top_k", String(topK));

  const response = await fetch(`${API_BASE}/api/realtime/detect`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: `Request failed with HTTP ${response.status}` }));
    const detail = typeof error?.detail === "string"
      ? error.detail
      : `Request failed with HTTP ${response.status}`;
    throw new Error(detail);
  }

  return response.json();
}
