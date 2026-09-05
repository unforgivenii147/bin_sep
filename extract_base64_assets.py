#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import base64
import hashlib
import logging
import mimetypes
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from multiprocessing import Manager, Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import tree_sitter
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree-sitter not available, using regex fallback")
SUPPORTED_EXTENSIONS = {".html", ".css", ".js", ".jsx", ".tsx", ".ts"}
ASSETS_DIR = Path("assets")
WORKERS = 8
CHUNK_SIZE = 8192
MAX_FILE_SIZE = 100 * 1024 * 1024
BASE64_SIGNATURES: dict[str, tuple[bytes, str, str]] = {
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png", "images"),
    "image/jpeg": (b"\xff\xd8\xff", ".jpg", "images"),
    "image/gif": (b"GIF87a", ".gif", "images"),
    "image/gif": (b"GIF89a", ".gif", "images"),
    "image/webp": (b"RIFF", ".webp", "images"),
    "image/svg+xml": (b"<?xml", ".svg", "images"),
    "image/svg+xml": (b"<svg", ".svg", "images"),
    "font/woff": (b"wOF2", ".woff2", "fonts"),
    "font/woff": (b"wOF2", ".woff2", "fonts"),
    "font/ttf": (b"\x00\x01\x00\x00", ".ttf", "fonts"),
    "application/x-font-ttf": (b"\x00\x01\x00\x00", ".ttf", "fonts"),
    "application/json": (b"{", ".json", "data"),
    "text/plain": (b"text", ".txt", "data"),
}
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("extract_base64_assets.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class Base64Match:
    file_path: Path
    start_pos: int
    end_pos: int
    base64_str: str
    context: str
    match_type: str


@dataclass
class ExtractedAsset:
    original_file: Path
    asset_path: Path
    asset_url: str
    base64_match: Base64Match
    extracted_bytes: bytes


@dataclass
class ProcessingResult:
    file_path: Path
    success: bool
    extracted_count: int
    replaced_count: int
    error: Optional[str] = None
    duration: float = 0.0


@lru_cache(maxsize=256)
def detect_base64_mime_type(
    data: bytes,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not data or len(data) < 4:
        return (None, None, None)
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ("image/png", ".png", "images")
    if data.startswith(b"\xff\xd8\xff"):
        return ("image/jpeg", ".jpg", "images")
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ("image/gif", ".gif", "images")
    if data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
        return ("image/webp", ".webp", "images")
    if b"<?xml" in data[:100] or b"<svg" in data[:100]:
        return ("image/svg+xml", ".svg", "images")
    if data.startswith(b"wOF2"):
        return ("font/woff2", ".woff2", "fonts")
    if data.startswith(b"wOFF"):
        return ("font/woff", ".woff", "fonts")
    if data.startswith(b"\x00\x01\x00\x00") or data.startswith(b"true"):
        return ("font/ttf", ".ttf", "fonts")
    if data.startswith(b"OTTO"):
        return ("font/otf", ".otf", "fonts")
    if data.startswith(b"{") or data.startswith(b"["):
        return ("application/json", ".json", "data")
    if data.startswith(b"\x00\x00\x00\x18ftypmp42"):
        return ("video/mp4", ".mp4", "videos")
    if data.startswith(b"\x00\x00\x00\x20ftypmp42"):
        return ("video/mp4", ".mp4", "videos")
    if data.startswith(b"\x00\x00\x01\x00"):
        return ("image/x-icon", ".ico", "images")
    if data.startswith(b"BM"):
        return ("image/bmp", ".bmp", "images")
    try:
        text_chars = sum(1 for b in data[:256] if 32 <= b < 127 or b in (9, 10, 13))
        if text_chars / min(256, len(data)) > 0.8:
            return ("text/plain", ".txt", "data")
    except:
        pass
    return (None, None, None)


class Base64PatternDetector:
    PATTERNS = {
        "url": re.compile(
            r'url\s*\(\s*["\']?data:([^;]+);base64,([A-Za-z0-9+/=]+)["\']?\s*\)',
            re.IGNORECASE,
        ),
        "src": re.compile(
            r'src\s*=\s*["\']data:([^;]+);base64,([A-Za-z0-9+/=]+)["\']', re.IGNORECASE
        ),
        "href": re.compile(
            r'href\s*=\s*["\']data:([^;]+);base64,([A-Za-z0-9+/=]+)["\']', re.IGNORECASE
        ),
        "data_uri": re.compile(r"data:([^;]+);base64,([A-Za-z0-9+/=]+)", re.IGNORECASE),
        "background": re.compile(
            r'background(?:-image)?\s*:\s*url\s*\(\s*["\']?data:([^;]+);base64,([A-Za-z0-9+/=]+)["\']?\s*\)',
            re.IGNORECASE,
        ),
    }

    @staticmethod
    def find_all_base64(text: str, file_path: Path) -> list[Base64Match]:
        matches: list[Base64Match] = []
        seen_hashes: set[str] = set()
        for pattern_name, pattern in Base64PatternDetector.PATTERNS.items():
            for match in pattern.finditer(text):
                mime_type = match.group(1)
                base64_str = match.group(2)
                if not Base64PatternDetector.is_valid_base64(base64_str):
                    continue
                hash_key = hashlib.md5(base64_str.encode()).hexdigest()
                if hash_key in seen_hashes:
                    continue
                seen_hashes.add(hash_key)
                if len(base64_str) < 64:
                    continue
                matches.append(
                    Base64Match(
                        file_path=file_path,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        base64_str=base64_str,
                        context=match.group(0),
                        match_type=pattern_name,
                    )
                )
        return matches

    @staticmethod
    def is_valid_base64(s: str) -> bool:
        try:
            if isinstance(s, str):
                s_bytes = bytes(s, "utf-8")
            else:
                s_bytes = s
            if len(s_bytes) % 4 != 0:
                s_bytes = s_bytes + b"=" * (4 - len(s_bytes) % 4)
            base64.b64decode(s_bytes, validate=True)
            return True
        except Exception:
            return False


class TreeSitterParser:
    def __init__(self):
        self.available = TREE_SITTER_AVAILABLE
        self.parsers: dict[str, Any] = {}
        if self.available:
            try:
                self._init_parsers()
            except Exception as e:
                logger.warning(
                    f"Tree-sitter initialization failed: {e}, falling back to regex"
                )
                self.available = False

    def _init_parsers(self):
        try:
            pass
        except Exception as e:
            logger.debug(f"Could not init tree-sitter parsers: {e}")
            self.available = False

    def parse_file(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None


class AssetExtractor:
    def __init__(self, assets_dir: Path = ASSETS_DIR):
        self.assets_dir = assets_dir
        self.extracted_assets: list[ExtractedAsset] = []
        self._ensure_assets_dir()

    def _ensure_assets_dir(self):
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ["images", "fonts", "videos", "data"]:
            (self.assets_dir / subdir).mkdir(exist_ok=True)

    def extract_asset(self, match: Base64Match) -> Optional[ExtractedAsset]:
        try:
            base64_data = match.base64_str.replace("\n", "").replace("\r", "")
            padding = 4 - (len(base64_data) % 4)
            if padding != 4:
                base64_data += "=" * padding
            decoded_bytes = base64.b64decode(base64_data, validate=True)
            mime_type, ext, category = detect_base64_mime_type(decoded_bytes)
            if not mime_type:
                logger.warning(
                    f"Could not detect MIME type for base64 in {match.file_path}"
                )
                if "data:" in match.context:
                    try:
                        hint = match.context.split("data:")[1].split(";")[0]
                        ext = mimetypes.guess_extension(hint) or ".bin"
                        category = "data"
                    except:
                        ext = ".bin"
                        category = "data"
                else:
                    ext = ".bin"
                    category = "data"
            file_hash = hashlib.sha256(decoded_bytes).hexdigest()[:16]
            filename = f"{file_hash}{ext}"
            asset_path = self.assets_dir / category / filename
            if asset_path.exists():
                logger.debug(f"Asset already exists: {asset_path}")
                asset_url = asset_path.relative_to(match.file_path.parent).as_posix()
                return ExtractedAsset(
                    original_file=match.file_path,
                    asset_path=asset_path,
                    asset_url=asset_url,
                    base64_match=match,
                    extracted_bytes=decoded_bytes,
                )
            with open(asset_path, "wb") as f:
                f.write(decoded_bytes)
            logger.debug(f"Extracted asset: {asset_path} ({len(decoded_bytes)} bytes)")
            asset_url = asset_path.relative_to(match.file_path.parent).as_posix()
            return ExtractedAsset(
                original_file=match.file_path,
                asset_path=asset_path,
                asset_url=asset_url,
                base64_match=match,
                extracted_bytes=decoded_bytes,
            )
        except Exception as e:
            logger.error(f"Failed to extract asset from {match.file_path}: {e}")
            return None


class FileProcessor:
    def __init__(self, asset_extractor: AssetExtractor):
        self.extractor = asset_extractor
        self.parser = TreeSitterParser()

    def process_file(self, file_path: Path) -> ProcessingResult:
        start_time = datetime.now()
        try:
            if not file_path.exists():
                return ProcessingResult(
                    file_path=file_path,
                    success=False,
                    extracted_count=0,
                    replaced_count=0,
                    error=f"File not found: {file_path}",
                    duration=(datetime.now() - start_time).total_seconds(),
                )
            if file_path.stat().st_size > MAX_FILE_SIZE:
                return ProcessingResult(
                    file_path=file_path,
                    success=False,
                    extracted_count=0,
                    replaced_count=0,
                    error=f"File too large: {file_path.stat().st_size} bytes",
                    duration=(datetime.now() - start_time).total_seconds(),
                )
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return ProcessingResult(
                    file_path=file_path,
                    success=False,
                    extracted_count=0,
                    replaced_count=0,
                    error=f"Failed to read file: {e}",
                    duration=(datetime.now() - start_time).total_seconds(),
                )
            matches = Base64PatternDetector.find_all_base64(content, file_path)
            if not matches:
                logger.debug(f"No base64 found in {file_path}")
                return ProcessingResult(
                    file_path=file_path,
                    success=True,
                    extracted_count=0,
                    replaced_count=0,
                    duration=(datetime.now() - start_time).total_seconds(),
                )
            replacements: list[tuple[str, str]] = []
            extracted_count = 0
            for match in matches:
                extracted_asset = self.extractor.extract_asset(match)
                if extracted_asset:
                    extracted_count += 1
                    if file_path.suffix.lower() == ".css":
                        new_reference = f"url('{extracted_asset.asset_url}')"
                    elif file_path.suffix.lower() in {".html", ".htm"}:
                        if "href=" in match.context:
                            new_reference = f'href="{extracted_asset.asset_url}"'
                        else:
                            new_reference = f'src="{extracted_asset.asset_url}"'
                    else:
                        new_reference = f'"{extracted_asset.asset_url}"'
                    replacements.append((match.context, new_reference))
            if not replacements:
                return ProcessingResult(
                    file_path=file_path,
                    success=True,
                    extracted_count=0,
                    replaced_count=0,
                    duration=(datetime.now() - start_time).total_seconds(),
                )
            modified_content = content
            for old_ref, new_ref in replacements:
                modified_content = modified_content.replace(old_ref, new_ref)
            self._write_file_atomic(file_path, modified_content)
            logger.info(
                f"Processed {file_path.name}: "
                f"extracted={extracted_count}, "
                f"replaced={len(replacements)}"
            )
            return ProcessingResult(
                file_path=file_path,
                success=True,
                extracted_count=extracted_count,
                replaced_count=len(replacements),
                duration=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            return ProcessingResult(
                file_path=file_path,
                success=False,
                extracted_count=0,
                replaced_count=0,
                error=str(e),
                duration=(datetime.now() - start_time).total_seconds(),
            )

    @staticmethod
    def _write_file_atomic(file_path: Path, content: str):
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)
        try:
            temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            temp_path.replace(file_path)
            logger.debug(f"Updated file: {file_path}")
        except Exception as e:
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
            raise e
        finally:
            if backup_path.exists():
                backup_path.unlink()


class FileDiscovery:
    SKIP_DIRS = {
        ".git",
        ".svn",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        ".egg-info",
        "dist",
        "build",
        ".idea",
        ".vscode",
        ".pytest_cache",
        ".tox",
        ".coverage",
        ".mypy_cache",
        "target",
        "out",
        "bin",
        ".gradle",
        "assets",
    }

    @staticmethod
    def discover_files(paths: list[str]) -> list[Path]:
        discovered: list[Path] = []
        seen: set[Path] = set()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for path_str in paths:
                path = Path(path_str).resolve()
                if not path.exists():
                    logger.warning(f"Path not found: {path}")
                    continue
                if path.is_file():
                    if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        discovered.append(path)
                else:
                    futures.append(
                        executor.submit(FileDiscovery._discover_in_directory, path)
                    )
            for future in futures:
                try:
                    discovered.extend(future.result())
                except Exception as e:
                    logger.error(f"Error during file discovery: {e}")
        unique_files = []
        for f in discovered:
            if f not in seen:
                unique_files.append(f)
                seen.add(f)
        return sorted(unique_files)

    @staticmethod
    def _discover_in_directory(directory: Path) -> list[Path]:
        files: list[Path] = []
        try:
            for item in directory.rglob("*"):
                if any(part in FileDiscovery.SKIP_DIRS for part in item.parts):
                    continue
                if item.is_symlink():
                    continue
                if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(item)
        except Exception as e:
            logger.error(f"Error discovering files in {directory}: {e}")
        return files


def process_file_task(args: tuple[Path, AssetExtractor]) -> ProcessingResult:
    file_path, asset_extractor = args
    processor = FileProcessor(asset_extractor)
    return processor.process_file(file_path)


class Base64AssetExtractor:
    def __init__(self, paths: Optional[list[str]] = None):
        self.paths = paths or ["."]
        self.asset_extractor = AssetExtractor()
        self.results: list[ProcessingResult] = []

    def run(self):
        logger.info("=" * 70)
        logger.info("Base64 Asset Extractor")
        logger.info("=" * 70)
        logger.info(f"Discovering files in: {', '.join(self.paths)}")
        files = FileDiscovery.discover_files(self.paths)
        if not files:
            logger.warning("No supported files found")
            return
        logger.info(f"Found {len(files):,} supported files")
        logger.info(f"Processing with {WORKERS} workers...")
        tasks = [(f, self.asset_extractor) for f in files]
        with Pool(WORKERS) as pool:
            async_results = []
            for task in tasks:
                result = pool.apply_async(process_file_task, (task,))
                async_results.append(result)
            for i, async_result in enumerate(async_results, 1):
                try:
                    result = async_result.get(timeout=60)
                    self.results.append(result)
                    if i % 10 == 0 or i == len(async_results):
                        logger.info(f"Progress: {i}/{len(async_results)} files")
                except Exception as e:
                    logger.error(f"Error retrieving result: {e}")
        self._print_summary()

    def _print_summary(self):
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        total_extracted = sum(r.extracted_count for r in self.results)
        total_replaced = sum(r.replaced_count for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        logger.info(f"Total files processed: {len(self.results)}")
        logger.info(f"  ✓ Successful: {successful}")
        logger.info(f"  ✗ Failed: {failed}")
        logger.info(f"Total base64 assets extracted: {total_extracted:,}")
        logger.info(f"Total replacements made: {total_replaced:,}")
        logger.info(f"Total processing time: {total_duration:.2f}s")
        if failed > 0:
            logger.info("\nFailed files:")
            for result in self.results:
                if not result.success:
                    logger.info(f"  - {result.file_path}: {result.error}")
        if self.results:
            logger.info("\nDetailed results:")
            for result in sorted(
                self.results, key=lambda r: r.extracted_count, reverse=True
            ):
                if result.extracted_count > 0 or result.replaced_count > 0:
                    logger.info(
                        f"  {result.file_path.name:40} "
                        f"extracted={result.extracted_count:3} "
                        f"replaced={result.replaced_count:3} "
                        f"time={result.duration:.3f}s"
                    )
        logger.info(f"\nAssets saved to: {ASSETS_DIR.resolve()}")
        if ASSETS_DIR.exists():
            asset_count = sum(1 for _ in ASSETS_DIR.rglob("*") if _.is_file())
            if asset_count > 0:
                logger.info(f"Total asset files: {asset_count}")
                for category in ["images", "fonts", "videos", "data"]:
                    cat_dir = ASSETS_DIR / category
                    if cat_dir.exists():
                        count = sum(1 for _ in cat_dir.iterdir() if _.is_file())
                        if count > 0:
                            size = sum(
                                _.stat().st_size
                                for _ in cat_dir.iterdir()
                                if _.is_file()
                            )
                            logger.info(
                                f"  {category:8}: {count:4} files ({size / 1024:.1f} KB)"
                            )


def main():
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        paths = ["."]
    extractor = Base64AssetExtractor(paths)
    extractor.run()


if __name__ == "__main__":
    main()
