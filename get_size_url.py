#!/data/data/com.termux/files/home/.local/bin/python
import sys
import os
import time
import pycurl
from urllib.parse import urlparse
from dh import fsz


def get_remote_size(url):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.NOBODY, True)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.TIMEOUT, 10)
    c.perform()
    size = c.getinfo(c.CONTENT_LENGTH_DOWNLOAD)
    c.close()
    return int(size) if size > 0 else None


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <url> [-d]")
        print("  <url>  : The remote file URL")
        print("  -d     : Download the file to the current directory")
        sys.exit(1)

    url = sys.argv[1]
    do_download = "-d" in sys.argv

    print(f"Checking remote size for: {url}")
    total_size = get_remote_size(url)

    if total_size:
        print(f"Remote file size: {fsz(total_size)}")
    else:
        print("Remote file size: Unknown (server did not provide Content-Length)")

    if do_download:
        print("Starting download...")
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or filename == "/":
            filename = "index.html"  # fallback

        filepath = os.path.join(os.getcwd(), filename)

        downloaded = 0
        start_time = time.time()

        def write_function(data):
            nonlocal downloaded
            with open(filepath, "ab") as f:
                f.write(data)
            downloaded += len(data)

            elapsed = time.time() - start_time
            speed = downloaded / elapsed if elapsed > 0 else 0

            if total_size and total_size > 0:
                progress = (downloaded / total_size) * 100
                remaining = total_size - downloaded
                eta = remaining / speed if speed > 0 else 0
                eta_str = time.strftime("%H:%M:%S", time.gmtime(eta))
                size_str = f"{fsz(downloaded)}/{fsz(total_size)}"
            else:
                progress = 0
                eta_str = "Unknown"
                size_str = f"{fsz(downloaded)}/Unknown"

            sys.stdout.write(
                f"\r[{progress:5.1f}%] {size_str} | Speed: {fsz(speed)}/s | ETA: {eta_str}   "
            )
            sys.stdout.flush()

        # Ensure we start fresh
        if os.path.exists(filepath):
            os.remove(filepath)

        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.WRITEFUNCTION, write_function)
        # To ensure chunked/streaming download, pycurl handles this natively
        # via the write callback. We can also explicitly disable buffering if needed,
        # but standard WRITEFUNCTION is sufficient for chunked processing.

        try:
            c.perform()
        except pycurl.error as e:
            print(f"\nDownload error: {e}")
            sys.exit(1)
        finally:
            c.close()

        print(f"\nDownload complete! Saved to: {filepath}")
    else:
        print("Use -d flag to download the file.")


if __name__ == "__main__":
    main()
