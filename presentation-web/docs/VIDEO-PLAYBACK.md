AGROSENTINEL ROVER VIDEO FIX

Upload the CONTENTS of wwwroot/ into the existing website's wwwroot/ folder:
  wwwroot/js/site.js
  wwwroot/media/rover-web.mp4
Keep the same folder structure. These are the only two replacement/additional files needed for this playback fix. Do not upload this README into wwwroot.
Then refresh the website with Ctrl+F5 and select The ground rover.
The new media filename avoids reusing the old cached rover file.

The original rover video had its MP4 metadata at the end of a 93,563,531-byte file. The new file moves it ahead of media data so the browser can read playback information before downloading the video body. All media payload bytes are unchanged; duration remains 73.5 seconds. First, middle and final frames decoded successfully. Audio is retained without re-encoding.

This is a lossless fast-start fix, not a bitrate reduction: file size remains about 94 MB (89.2 MiB). Slow connections can still buffer. An encoder was unavailable in the current environment. The hosted server still needs to serve byte-range requests correctly. Hosted playback has not been independently tested because no public site URL was supplied.

A complete fresh ASP.NET publish folder is also available beside this patch under agrosentinel-video-fix/publish if you prefer a full re-upload.
