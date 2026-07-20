import assert from "node:assert/strict";
import { extractAwemeId, isAudioTrackUrl } from "./media-rules.mjs";

assert.equal(
  isAudioTrackUrl("https://v26-web.douyinvod.com/path/media-audio-und-mp4a/?token=x"),
  true
);
assert.equal(
  isAudioTrackUrl("https://v26-web.douyinvod.com/path/media-video-avc1/?token=x"),
  false
);
assert.equal(isAudioTrackUrl("https://attacker.example/media-audio-und-mp4a/"), false);
assert.equal(extractAwemeId("https://www.douyin.com/video/7663541194290449691"), "7663541194290449691");
assert.equal(
  extractAwemeId("https://www.douyin.com/user/example?modal_id=7663541194290449691"),
  "7663541194290449691"
);
assert.equal(extractAwemeId("https://www.douyin.com/user/example?modal_id=bad"), null);

console.log("media rules ok");
