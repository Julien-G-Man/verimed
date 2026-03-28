# Real-Time Computer Vision Detection (OpenCV)

## Why this module exists

The core `/api/verify` flow is still the source of truth for risk scoring.
This module adds a fast, frame-level detector for camera/live-preview workflows.

- Deterministic: OpenCV feature matching only (no LLM)
- Optional: does not alter existing scoring logic
- Architecture-safe: isolated as a new service + route

## API Endpoint

`POST /api/realtime/detect`

Request: `multipart/form-data`

- `frame_image` (required): one camera frame (jpg/png/webp)
- `side` (optional): `front` or `back` (default `front`)
- `top_k` (optional): number of detections to return (default `3`, clamped to max `5`)

Response:

- `detections[]`: candidate products with confidence and bounding boxes
- `request_id`, `timestamp`, `side`: response metadata
- `reference_templates_loaded`: number of usable reference templates loaded
- `message`: status hint

Rate limit: `30/minute`

## Detection algorithm

Implemented in `backend/services/realtime_cv_service.py`.

1. Load product reference images from `data/reference_images/`
2. Build ORB keypoints/descriptors for each front/back reference template
3. For each incoming frame:
   - compute ORB features
   - run KNN feature matching against templates
   - apply Lowe ratio test
   - estimate homography with RANSAC
   - project template corners onto frame to create bounding box
4. Compute confidence from match quality + inlier ratio
5. Apply NMS to suppress overlapping boxes
6. Return top detections

## Data dependency

This module depends on `reference_image_front` and `reference_image_back` fields in product records.

- If records have no reference images, detection returns no matches.
- For best results, keep reference images sharp, frontal, and well-lit.

## Integration pattern for camera preview

Implemented in `components/RealtimeCameraPreview.tsx`:

1. Capture one frame from `<video>` every 500 ms via Canvas API.
2. Convert frame to Blob/File.
3. Call `detectRealtimeProduct(frameFile, side, topK=3)`.
4. Render two overlay layers inside the camera view:
   - **Top-right name card** — frosted glass pill showing the top detection's product label and a confidence bar. Replaces the redundant per-box label.
   - **Bounding boxes** — lime-green outlines marking where the product was detected in the frame.
   - **"Scanning…" pill** — shown when the camera is live but no detection has been returned yet.
5. User taps "Capture" to freeze the frame as a `File` for the full `/api/verify` flow.

The live name overlay is purely assistive. The deterministic `/api/verify` pipeline remains the source of truth for risk scoring.
