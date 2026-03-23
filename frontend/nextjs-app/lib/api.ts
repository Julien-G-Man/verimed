import { VerificationResult } from "./types";

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
