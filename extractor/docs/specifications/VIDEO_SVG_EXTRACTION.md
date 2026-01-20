# Video/SVG Extraction (Deprecated)

Video downloads are no longer automated in the extractor. SVG downloads remain
browser-based, but video files must be downloaded manually.

## Current Policy

- The extractor **does not download video files**.
- Use `media_discovery.txt` (VIDEO QUESTION IDS) or
  `media_discovery.json` (`metadata.statistics.video_question_ids`) to find
  the questions that contain videos.
- Videos should be downloaded manually per question and saved under
  `mksap_data/{system}/{question_id}/videos/`.

## Media Metadata Notes (Still Relevant)

- Video metadata lives in `/api/content_metadata.json` with fields like
  `id`, `canonicalLocation` (question ID), `title`, `mp4Hash`, `height`, `width`.
- Link videos to questions by matching `video.canonicalLocation` to the
  question ID.
- Figures (including SVGs) are referenced via `contentIds` in question
  `stimulus`/`exposition` inline entries and can be resolved via
  `/api/content_metadata.json`.
- Figure `imageInfo.hash` is not a direct URL; CDN URLs are hash-based and
  typically look like `https://d2chybfyz5ban.cloudfront.net/assets/{hash}.{ext}`.

## What We Learned

- Video URLs are often only available after the browser renders the page and
  initializes the player; API metadata is incomplete or inconsistent.
- MP4 URLs use hashed filenames, and the hash does not reliably map back to a
  stable API field across all questions.
- Browser automation added significant flakiness (timing, auth state, and
  playback triggers) and made runs unreliable.
- Large video files are expensive to download in batch and complicate retries.

## Manual Download Checklist

1. Open the question URL in the browser.
2. Locate the video player and download the MP4.
3. Save into `mksap_data/{system}/{question_id}/videos/` using the original
   filename from the URL.
4. (Optional) Add the filename to the question JSON `media.videos` array.

## If We Revisit Automation Later

- Use browser automation only to **collect** URLs, not download them.
- Treat video downloads as a separate, opt-in step with throttling and retries.
- Require explicit confirmation before any MP4 downloads.
