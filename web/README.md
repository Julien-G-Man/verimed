# VeriMed Frontend (Next.js)

Mobile-first UI for VeriMed medicine authenticity risk assessment.

## Features

- Home page with Verify CTA
- `/verify` flow with 3 required image slots (front, back, barcode)
- Upload progress state and loading skeletons
- Result card with risk badge and score
- Collapsible extracted fields and scoring reasons panels

## Requirements

- Node.js 20+
- Running backend API (FastAPI) at `http://localhost:8000` by default

## Environment

Copy `.env.example` to `.env.local` and adjust if needed:

```bash
cp .env.example .env.local
```

Environment variables:

- `NEXT_PUBLIC_API_URL`: Base URL for backend API

## Run Locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Scripts

- `npm run dev`: Start dev server
- `npm run lint`: Run ESLint
- `npm run build`: Production build check
- `npm run start`: Run production server

## API Contract Used

- `POST /api/verify` with `multipart/form-data`
	- `front_image`
	- `back_image`
	- `barcode_image`
- Expects response matching `VerificationResult` shape in `lib/types.ts`

## Project Structure

```text
app/
	page.tsx
	verify/page.tsx
components/
	ImageUploadZone.tsx
	UploadProgress.tsx
	ResultSkeleton.tsx
	ResultCard.tsx
	ExtractedFieldsPanel.tsx
	ReasonsPanel.tsx
lib/
	api.ts
	types.ts
```
