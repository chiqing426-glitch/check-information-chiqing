import { extractAwemeId, isAudioTrackUrl } from "./media-rules.mjs";

const BRIDGE_URL = "http://127.0.0.1:17321/capture";
const observed = new Set();

async function forwardTrack(details) {
  if (details.tabId < 0 || !isAudioTrackUrl(details.url)) return;
  const tab = await chrome.tabs.get(details.tabId).catch(() => null);
  const awemeId = extractAwemeId(tab?.url || "");
  if (!awemeId) return;

  const media = new URL(details.url);
  const key = `${details.tabId}:${awemeId}:${media.origin}${media.pathname}`;
  if (observed.has(key)) return;
  observed.add(key);

  try {
    const response = await fetch(BRIDGE_URL, {
      method: "POST",
      credentials: "omit",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aweme_id: awemeId,
        source_url: `https://www.douyin.com/video/${awemeId}`,
        media_url: details.url
      })
    });
    if (!response.ok) observed.delete(key);
  } catch {
    observed.delete(key);
  }
}

chrome.webRequest.onBeforeRequest.addListener(
  (details) => { void forwardTrack(details); },
  { urls: ["https://*.douyinvod.com/*"], types: ["media", "xmlhttprequest", "other"] }
);
