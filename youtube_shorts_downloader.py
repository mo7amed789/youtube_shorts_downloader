"""Download an inclusive range of videos from a YouTube channel or Shorts URL.

Use only for videos you are allowed to download. YouTube's terms and a video's
copyright/license may restrict downloading or reuse.
"""

from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


DEFAULT_URL = "https://www.youtube.com/@zadqolob/shorts"
IS_FROZEN = bool(getattr(sys, "frozen", False))
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent


def runtime_environment() -> dict[str, str]:
    """Add bundled FFmpeg to PATH when running from the packaged EXE."""
    env = dict(os.environ)
    roots = []
    if getattr(sys, "_MEIPASS", None):
        roots.append(Path(sys._MEIPASS))
    roots.append(APP_DIR)
    for root in roots:
        bundled_ffmpeg = root / "ffmpeg"
        if (bundled_ffmpeg / "ffmpeg.exe").is_file():
            env["PATH"] = str(bundled_ffmpeg) + os.pathsep + env.get("PATH", "")
            break
    for root in roots:
        bundled_node = root / "node"
        if (bundled_node / "node.exe").is_file():
            env["PATH"] = str(bundled_node) + os.pathsep + env.get("PATH", "")
            break
    return env


def yt_dlp_command() -> list[str]:
    """Return the most portable way to invoke yt-dlp."""
    if IS_FROZEN:
        return [sys.executable, "--yt-dlp"]
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


def run_yt_dlp(args: list[str], output=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        yt_dlp_command() + args,
        text=True,
        stdout=output,
        stderr=subprocess.STDOUT,
        env=runtime_environment(),
        check=False,
    )


def parse_range(value: str) -> tuple[int, int]:
    value = value.strip().replace("–", "-").replace("—", "-")
    if "-" in value:
        left, right = value.split("-", 1)
        start, end = int(left.strip()), int(right.strip())
    else:
        start = end = int(value)
    if start < 1 or end < start:
        raise ValueError("Range must be positive and formatted like 1-10.")
    return start, end


def download(
    url: str,
    start: int,
    end: int,
    folder: Path,
    cookies_browser: str = "",
    cookies_file: str = "",
    on_line=None,
) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    webm_before = set(folder.glob("*.webm"))
    ffmpeg_available = shutil.which("ffmpeg", path=runtime_environment().get("PATH")) is not None
    args = [
        "--yes-playlist",
        "--js-runtimes",
        "node",
        "--remote-components",
        "ejs:github",
        "--playlist-items",
        f"{start}:{end}",
        "--no-overwrites",
        "--continue",
        "--windows-filenames",
        "--trim-filenames",
        "180",
        "-o",
        str(folder / "%(playlist_index)03d - %(title)s [%(id)s].%(ext)s"),
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        url,
    ]
    if cookies_file:
        args[0:0] = ["--cookies", cookies_file]
    elif cookies_browser:
        # yt-dlp reads the login session from the selected local browser.
        args[0:0] = ["--cookies-from-browser", cookies_browser]
    if on_line is None:
        result = run_yt_dlp(args)
    else:
        result = subprocess.run(
            yt_dlp_command() + args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=runtime_environment(),
            check=False,
        )
        for line in result.stdout.splitlines():
            on_line(line)
    if result.returncode == 0 and ffmpeg_available:
        # Successful FFmpeg post-processing produces the final MP4 and leaves
        # no reason to retain the temporary audio/video WebM inputs.
        for temporary in set(folder.glob("*.webm")) - webm_before:
            try:
                temporary.unlink()
            except OSError:
                pass
    return result.returncode


def cli_main(args: argparse.Namespace) -> int:
    try:
        start, end = parse_range(args.range)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.cookies_file and not Path(args.cookies_file).expanduser().is_file():
        print(f"Error: cookie file does not exist: {args.cookies_file}", file=sys.stderr)
        return 2
    print(f"Downloading Shorts {start}-{end} from {args.url}")
    code = download(args.url, start, end, Path(args.output), args.cookies_browser, args.cookies_file, print)
    if code == 0:
        print("Finished.")
    return code


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Shorts Range Downloader")
        self.geometry("760x500")
        self.minsize(680, 430)
        self.events: queue.Queue[str] = queue.Queue()
        self.running = False
        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 7}
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(4, weight=1)

        ttk.Label(main, text="Channel or Shorts URL:").grid(row=0, column=0, sticky="w", **pad)
        self.url = ttk.Entry(main)
        self.url.insert(0, DEFAULT_URL)
        self.url.grid(row=0, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(main, text="Video range:").grid(row=1, column=0, sticky="w", **pad)
        self.range = ttk.Entry(main, width=18)
        self.range.insert(0, "1-10")
        self.range.grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(main, text="Inclusive playlist positions, e.g. 1-10 or 7").grid(
            row=1, column=2, sticky="w", **pad
        )

        ttk.Label(main, text="Save folder:").grid(row=2, column=0, sticky="w", **pad)
        self.output = ttk.Entry(main)
        self.output.insert(0, str(APP_DIR / "downloads"))
        self.output.grid(row=2, column=1, sticky="ew", **pad)
        ttk.Button(main, text="Browse…", command=self.choose_folder).grid(row=2, column=2, **pad)

        ttk.Label(main, text="Signed-in browser:").grid(row=3, column=0, sticky="w", **pad)
        self.browser = ttk.Combobox(main, values=["None", "Chrome", "Edge", "Firefox", "Brave"], state="readonly", width=14)
        self.browser.set("None")
        self.browser.grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(main, text="Choose the browser where you are signed in to YouTube").grid(
            row=3, column=2, sticky="w", **pad
        )

        ttk.Label(main, text="Cookie file (optional):").grid(row=4, column=0, sticky="w", **pad)
        self.cookies_file = ttk.Entry(main)
        default_cookie_file = APP_DIR / "www.youtube.com_cookies.txt"
        if default_cookie_file.is_file():
            self.cookies_file.insert(0, str(default_cookie_file))
        self.cookies_file.grid(row=4, column=1, sticky="ew", **pad)
        ttk.Button(main, text="Browse…", command=self.choose_cookies_file).grid(row=4, column=2, **pad)

        self.start_button = ttk.Button(main, text="Download range", command=self.start_download)
        self.start_button.grid(row=5, column=1, sticky="w", **pad)
        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.grid(row=5, column=2, sticky="ew", **pad)

        ttk.Label(main, text="Log:").grid(row=6, column=0, sticky="nw", **pad)
        self.log = tk.Text(main, height=15, wrap="word", state="disabled")
        self.log.grid(row=6, column=1, columnspan=2, sticky="nsew", **pad)
        scroll = ttk.Scrollbar(main, orient="vertical", command=self.log.yview)
        scroll.grid(row=6, column=3, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        ttk.Label(
            main,
            text="Use only for content you have permission to download or reuse.",
            foreground="#555555",
        ).grid(row=7, column=0, columnspan=3, sticky="w", padx=12, pady=8)

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory()
        if chosen:
            self.output.delete(0, tk.END)
            self.output.insert(0, chosen)

    def choose_cookies_file(self) -> None:
        chosen = filedialog.askopenfilename(
            title="Select exported YouTube cookies",
            filetypes=[("Cookie files", "*.txt *.cookies"), ("All files", "*.*")],
        )
        if chosen:
            self.cookies_file.delete(0, tk.END)
            self.cookies_file.insert(0, chosen)

    def write_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def start_download(self) -> None:
        if self.running:
            return
        try:
            start, end = parse_range(self.range.get())
        except ValueError as exc:
            messagebox.showerror("Invalid range", str(exc))
            return
        url = self.url.get().strip()
        folder = Path(self.output.get().strip()).expanduser()
        browser = self.browser.get().lower()
        cookies_browser = "" if browser == "none" else browser
        cookies_file = self.cookies_file.get().strip()
        if cookies_file and not Path(cookies_file).expanduser().is_file():
            messagebox.showerror("Cookie file not found", f"Select an existing cookie file:\n{cookies_file}")
            return
        if not url:
            messagebox.showerror("Missing URL", "Enter a channel or Shorts URL.")
            return
        self.running = True
        self.start_button.configure(state="disabled")
        self.progress.start(10)
        self.write_log(f"Starting download: {start}-{end}")
        threading.Thread(
            target=self._download_worker,
            args=(url, start, end, folder, cookies_browser, cookies_file),
            daemon=True,
        ).start()

    def _download_worker(
        self,
        url: str,
        start: int,
        end: int,
        folder: Path,
        cookies_browser: str,
        cookies_file: str,
    ) -> None:
        try:
            code = download(url, start, end, folder, cookies_browser, cookies_file, self.events.put)
            self.events.put(f"__DONE__:{code}")
        except Exception as exc:
            self.events.put(f"__ERROR__:{exc}")

    def _drain_events(self) -> None:
        try:
            while True:
                line = self.events.get_nowait()
                if line.startswith("__DONE__:"):
                    code = int(line.split(":", 1)[1])
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.progress.stop()
                    self.write_log("Finished." if code == 0 else f"yt-dlp exited with code {code}.")
                elif line.startswith("__ERROR__:"):
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.progress.stop()
                    self.write_log(line)
                    messagebox.showerror("Download error", line.split(":", 1)[1])
                else:
                    self.write_log(line)
        except queue.Empty:
            pass
        self.after(100, self._drain_events)


def main() -> int:
    if IS_FROZEN and len(sys.argv) > 1 and sys.argv[1] == "--yt-dlp":
        import yt_dlp

        sys.argv = [sys.argv[0], *sys.argv[2:]]
        yt_dlp.main()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Channel or Shorts URL")
    parser.add_argument("--range", dest="range", help="Inclusive range, such as 1-10")
    parser.add_argument("--output", default="downloads", help="Destination folder")
    parser.add_argument(
        "--cookies-from-browser",
        dest="cookies_browser",
        choices=["chrome", "edge", "firefox", "brave"],
        help="Read YouTube login cookies from this browser",
    )
    parser.add_argument(
        "--cookies",
        dest="cookies_file",
        help="Netscape-format cookie file exported from your browser; overrides --cookies-from-browser",
    )
    args = parser.parse_args()
    if args.url or args.range:
        if not args.url or not args.range:
            parser.error("--url and --range must be provided together")
        return cli_main(args)
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
