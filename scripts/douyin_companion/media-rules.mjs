export function isAudioTrackUrl(url) {
  try {
    const parsed = new URL(url);
    return (
      (parsed.hostname === "douyinvod.com" || parsed.hostname.endsWith(".douyinvod.com")) &&
      /\/media-audio-/i.test(parsed.pathname)
    );
  } catch {
    return false;
  }
}

export function extractAwemeId(tabUrl) {
  try {
    const parsed = new URL(tabUrl);
    if (parsed.hostname !== "www.douyin.com") return null;
    const standalone = parsed.pathname.match(/^\/video\/(\d+)\/?$/);
    if (standalone) return standalone[1];
    const modalId = parsed.searchParams.get("modal_id");
    return modalId && /^\d+$/.test(modalId) ? modalId : null;
  } catch {
    return null;
  }
}
