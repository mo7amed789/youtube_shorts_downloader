# YouTube Shorts Range Downloader

This local Windows-friendly tool downloads an inclusive range of videos from a
YouTube channel or Shorts URL. It uses `yt-dlp` and has both a simple GUI and a
command-line mode.

Use it only for videos you have permission to download or reuse, and follow
YouTube's terms and the creator's copyright/license.

## Setup

Install Python 3.10+ and `yt-dlp`:

```powershell
py -m pip install -U yt-dlp
```

For best quality when separate audio/video streams are selected, install
FFmpeg and make sure `ffmpeg.exe` is on PATH. The tool will still use a
single-file format when merging is unavailable.

## Run the GUI

```powershell
py youtube_shorts_downloader.py
```

Paste a channel/Shorts URL, enter a range such as `1-10`, choose a folder, and
click **Download range**. The positions are the order returned by YouTube for
that URL; ordering can change as new Shorts are published.

## Run from PowerShell

```powershell
py youtube_shorts_downloader.py `
  --url "https://www.youtube.com/@zadqolob/shorts" `
  --range 1-10 `
  --output "downloads\zadqolob"
```

Existing files are not overwritten, and interrupted downloads can be resumed.
