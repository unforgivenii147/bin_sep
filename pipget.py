#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import sys
import time
from io import BytesIO
from pathlib import Path
import pycurl
from bs4 import BeautifulSoup

MIRROR_URL = "https://mirror-pypi.runflare.com"
TIMEOUT = 30
DOWNLOAD_DIR = Path.cwd()
MAX_RETRIES = 3
RETRY_DELAY = 2


def fetch_package_page(pkg_name: str) -> str:
    url = f"{MIRROR_URL}/{pkg_name}"
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEDATA, buffer)
    curl.setopt(curl.FOLLOWLOCATION, 1)
    curl.setopt(curl.TIMEOUT, TIMEOUT)
    curl.setopt(
        curl.USERAGENT,
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    curl.setopt(curl.ACCEPT_ENCODING, "gzip, deflate")
    curl.setopt(
        curl.HTTPHEADER,
        [
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language: en-US,en;q=0.5",
        ],
    )
    try:
        curl.perform()
        response_code = curl.getinfo(curl.RESPONSE_CODE)
        if response_code != 200:
            print(f"Error: HTTP {response_code} for {pkg_name}")
            if response_code == 402:
                print(
                    "  HTTP 402: Payment Required - The mirror might require authentication"
                )
            elif response_code == 403:
                print("  HTTP 403: Forbidden - Access denied")
            elif response_code == 404:
                print(f"  Package '{pkg_name}' not found on mirror")
            elif response_code == 429:
                print("  HTTP 429: Too Many Requests - Rate limited")
            return ""
        return buffer.getvalue().decode("utf-8")
    except Exception as e:
        print(f"Error fetching page for {pkg_name}: {e}")
        return ""
    finally:
        curl.close()


def extract_latest_download_url(html: str, pkg_name: str) -> tuple[str, str] | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        all_links = soup.find_all("a", href=True)
        if not all_links:
            print(f"No download links found for {pkg_name}")
            return None
        latest_link = all_links[-1]
        download_url = latest_link["href"]
        filename = latest_link.get_text().strip()
        download_url = download_url.split("#")[0]
        return (download_url, filename)
    except Exception as e:
        print(f"Error parsing HTML for {pkg_name}: {e}")
        return None


def download_file_with_retry(
    url: str, filename: str, max_retries: int = MAX_RETRIES
) -> bool:
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"  Retry attempt {attempt + 1}/{max_retries}...")
            time.sleep(RETRY_DELAY * attempt)
        if download_file(url, filename):
            return True
        print(f"  Download failed (attempt {attempt + 1}/{max_retries})")
    return False


def download_file(url: str, filename: str) -> bool:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DOWNLOAD_DIR / filename
    if output_path.exists() and output_path.stat().st_size > 0:
        print(
            f"  File already exists: {filename} ({output_path.stat().st_size:,} bytes)"
        )
        return True
    print(f"  Downloading: {filename}")
    with open(output_path, "wb") as f:
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, f)
        curl.setopt(curl.FOLLOWLOCATION, 1)
        curl.setopt(curl.TIMEOUT, 120)
        curl.setopt(
            curl.USERAGENT,
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        curl.setopt(curl.ACCEPT_ENCODING, "gzip, deflate")
        curl.setopt(
            curl.HTTPHEADER,
            [
                "Accept: */*",
                "Accept-Language: en-US,en;q=0.5",
                "Referer: https://mirror-pypi.runflare.com/",
            ],
        )
        curl.setopt(curl.NOPROGRESS, 0)

        def progress_callback(download_t, download_d, upload_t, upload_d):
            if download_t > 0:
                percent = (download_d * 40) / download_t
                if int(percent) % 10 == 0:
                    print(
                        f"  Progress: {percent:.1f}% ({download_d:,}/{download_t:,} bytes)",
                        end="\r",
                    )
            else:
                print(f"  Downloaded: {download_d:,} bytes", end="\r")
            return 0

        curl.setopt(curl.XFERINFOFUNCTION, progress_callback)
        try:
            curl.perform()
            response_code = curl.getinfo(curl.RESPONSE_CODE)
            if response_code == 200:
                print()
                file_size = output_path.stat().st_size
                print(f"  Downloaded successfully: {filename} ({file_size:,} bytes)")
                return True
            else:
                print(f"\n  Error: HTTP {response_code} while downloading {filename}")
                if response_code == 402:
                    print(
                        "  HTTP 402: Payment Required - The mirror might require authentication or has usage limits"
                    )
                    print(
                        "  Suggestion: Try downloading directly from pypi.org or use pip install"
                    )
                elif response_code == 403:
                    print("  HTTP 403: Forbidden - Access denied")
                    print("  Suggestion: The mirror might be blocking direct downloads")
                elif response_code == 404:
                    print("  HTTP 404: File not found on mirror")
                elif response_code == 429:
                    print(
                        "  HTTP 429: Too Many Requests - Rate limited, try again later"
                    )
                if output_path.exists():
                    output_path.unlink()
                return False
        except Exception as e:
            print(f"\n  Error downloading {filename}: {e}")
            return False
        finally:
            curl.close()


def process_package(pkg_name: str) -> bool:
    print(f"\n{'=' * 40}")
    print(f"Processing package: {pkg_name}")
    print(f"{'=' * 40}")
    print(f"Fetching package info for {pkg_name}...")
    html = fetch_package_page(pkg_name)
    if not html:
        print(f"Failed to fetch package info for {pkg_name}")
        return False
    download_info = extract_latest_download_url(html, pkg_name)
    if not download_info:
        print(f"No valid download links found for {pkg_name}")
        return False
    url, filename = download_info
    print(f"Latest version file: {filename}")
    print(f"Download URL: {url}")
    return download_file_with_retry(url, filename)


def main():
    if len(sys.argv) < 2:
        print("Usage: python pyget.py <package1> [package2] [package3] ...")
        print("Example: python pyget.py requests wheel setuptools")
        sys.exit(1)
    packages = sys.argv[1:]
    print(f"Packages to download: {', '.join(packages)}")
    print(f"Download directory: {DOWNLOAD_DIR}")
    print(f"Max retries per package: {MAX_RETRIES}")
    start_time = time.time()
    successful = []
    failed = []
    for pkg_name in packages:
        try:
            if process_package(pkg_name):
                successful.append(pkg_name)
            else:
                failed.append(pkg_name)
        except Exception as e:
            print(f"Unexpected error processing {pkg_name}: {e}")
            failed.append(pkg_name)
    print(f"\n{'=' * 40}")
    print("DOWNLOAD SUMMARY")
    print(f"{'=' * 40}")
    print(f"Total packages: {len(packages)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    if successful:
        print(f"\nSuccessfully downloaded:")
        for pkg in successful:
            print(f"  ✓ {pkg}")
    if failed:
        print(f"\nFailed to download:")
        for pkg in failed:
            print(f"  ✗ {pkg}")
        print("\nSuggestions for failed downloads:")
        print("  1. Try using pip directly: pip download <package>")
        print("  2. Check if the mirror requires authentication")
        print("  3. Try again later (might be rate limited)")
        print(
            "  4. Use official PyPI: pip download <package> --index-url https://pypi.org/simple"
        )
    end_time = time.time()
    print(f"\nFinished in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
