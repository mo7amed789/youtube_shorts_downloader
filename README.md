# YouTube Shorts Range Downloader

This local Windows-friendly tool downloads an inclusive range of videos from a
YouTube channel or Shorts URL. It uses `yt-dlp` and has both a simple GUI and a
command-line mode.

Use it only for videos you have permission to download or reuse, and follow
YouTube's terms and the creator's copyright/license.

## Setup

Install Python 3.10+ and `yt-dlp`:

```powershell
py -m pip install -U "yt-dlp[default]"
```

YouTube now requires a supported JavaScript runtime and yt-dlp's external
challenge solver for many videos. Install Node.js 22+ if it is not already
installed. This tool uses Node and enables yt-dlp's official EJS components
from GitHub automatically.

If YouTube reports `Sign in to confirm you're not a bot`, select the browser
where you are signed in to YouTube in the GUI. The command-line equivalent is:

```powershell
py youtube_shorts_downloader.py `
  --url "https://www.youtube.com/@zadqolob/shorts" `
  --range 1-10 `
  --cookies-from-browser chrome
```

Close the selected browser before starting if yt-dlp cannot read its cookie
database. Cookies stay local and are not uploaded by this tool.

If Chrome shows `Failed to decrypt with DPAPI`, use Firefox in the GUI or
export a Netscape-format cookie file with a reputable browser cookie-export
extension, then select it in **Cookie file**. From PowerShell, use:

```powershell
py youtube_shorts_downloader.py `
  --url "https://www.youtube.com/@zadqolob/shorts" `
  --range 1-10 `
  --cookies "C:\path\to\youtube-cookies.txt"
```

Replace `C:\path\to\youtube-cookies.txt` with the real full path to your
exported file. That path is only an example.

Treat cookie files like passwords: do not upload or share them, and delete the
export after use.

Install FFmpeg and make sure `ffmpeg.exe` is on PATH. YouTube commonly serves
video and audio separately; FFmpeg merges them into one MP4. After a successful
merge, the tool removes the temporary WebM inputs. If FFmpeg is missing, the
tool keeps the WebM files because deleting them would remove the audio.

## Run the GUI

```powershell
py youtube_shorts_downloader.py
```

Paste a channel/Shorts URL, enter a range such as `1-10`, choose a folder,
select your signed-in browser or cookie file if needed, and click **Download range**. The
positions are the order returned by YouTube for that URL; ordering can change
as new Shorts are published.

## Run from PowerShell

```powershell
py youtube_shorts_downloader.py `
  --url "https://www.youtube.com/@zadqolob/shorts" `
  --range 1-10 `
  --output "downloads\zadqolob"
```

Existing files are not overwritten, and interrupted downloads can be resumed.
Filenames preserve Arabic and other Unicode titles while removing characters
that Windows does not allow in file names.
