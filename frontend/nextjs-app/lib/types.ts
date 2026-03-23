export interface ExtractedFields {
  brand_name: string | null;
  generic_name: string | null;
  strength: string | null;
  dosage_form: string | null;
  manufacturer: string | null;
  batch_number: string | null;
  expiry_date: string | null;
  keywords_found: string[];
  raw_front_text: string;
  raw_back_text: string;
  ocr_confidence_front: number;
  ocr_confidence_back: number;
}

export interface BarcodeResult {
  decoded: boolean;
  code_type: string | null;
  value: string | null;
  raw_payload: string | null;
}

export interface MatchResult {
  matched: boolean;
  product: Record<string, unknown> | null;
  match_method: string;
  match_confidence: number;
}

export interface ScoringSignal {
  field: string;
  passed: boolean;
  weight: number;
  reason: string;
}

export interface ScoringResult {
  raw_score: number;
  normalized_score: number;
  classification: string;
  signals: ScoringSignal[];
  reasons: string[];
}

export interface VerificationResult {
  request_id: string;
  timestamp: string;
  identified_product: string | null;
  matched_product_id: string | null;
  extraction: ExtractedFields;
  barcode: BarcodeResult;
  match: MatchResult;
  scoring: ScoringResult;
  risk_score: number;
  classification: string;
  reasons: string[];
  explanation: string;
  recommendation: string;
}
