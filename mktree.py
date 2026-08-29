#!/data/data/com.termux/files/home/.local/bin/python

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Optional OCR imports
try:
    import cv2
    import pytesseract
    from PIL import Image

    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class TreeParser:
    """Parse various tree text formats and extract paths."""

    TREE_SYMBOLS = ["├", "└", "│", "┌", "─", "┐"]

    def __init__(self, base_path: Path = Path.cwd()):
        self.base_path = base_path
        self.entries: List[Dict[str, Any]] = []

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse text and return list of entries.
        Auto-detects the format.
        """
        lines = [line.rstrip() for line in text.split("\n") if line.strip()]

        if not lines:
            return []

        # Detect format
        format_type = self._detect_format(lines)

        if format_type == "tree":
            self._parse_tree_format(lines)
        elif format_type == "indented":
            self._parse_indented_format(lines)
        else:
            self._parse_simple_format(lines)

        # Post-process to determine if entries are files or directories
        self._determine_file_types()

        return self.entries

    def _detect_format(self, lines: List[str]) -> str:
        """Detect the format of the input."""
        has_tree_symbols = any(
            any(sym in line for sym in self.TREE_SYMBOLS) for line in lines
        )

        has_indentation = any(
            line.startswith(" ") or line.startswith("\t") for line in lines
        )

        has_paths = any("/" in line or "\\" in line for line in lines)

        if has_tree_symbols:
            return "tree"
        elif has_indentation:
            return "indented"
        else:
            return "simple"

    def _parse_tree_format(self, lines: List[str]) -> None:
        """
        Parse standard tree command output format.
        Optimized for speed and accuracy.
        """
        stack: List[Tuple[int, Path]] = []  # (depth, path)

        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Find tree symbols
            tree_matches = []
            for sym in ["├── ", "└── ", "│   ", "    "]:
                if line.startswith(sym):
                    tree_matches.append((len(sym), sym))

            if tree_matches:
                # Found tree format
                depth = len(tree_matches) // 4
                name = line[len(tree_matches[0][1]) :].strip()
            else:
                # Try to find any tree symbol
                match = re.match(r"^([\s\|┌└├─]+)([^\s]+)(.*)$", line)
                if match:
                    prefix, name, _ = match.groups()
                    # Count the number of 4-char blocks
                    depth = len(prefix) // 4
                else:
                    # Root or simple entry
                    name = line.strip()
                    depth = 0

            # Clean name
            name = self._clean_name(name)

            if not name:
                continue

            # Handle root
            if name in (".", "./", ".\\"):
                self.entries.append(
                    {
                        "depth": 0,
                        "name": ".",
                        "is_dir": True,
                        "explicit_dir": True,
                        "raw": name,
                    }
                )
                stack = [(0, self.base_path)]
                continue

            # Pop stack to find parent
            while stack and stack[-1][0] >= depth:
                stack.pop()

            # Build path
            if stack:
                parent_path = stack[-1][1]
                current_path = parent_path / name
            else:
                current_path = self.base_path / name

            # Determine if it's explicitly a directory
            explicit_dir = name.endswith("/") or name.endswith("\\")

            self.entries.append(
                {
                    "depth": depth,
                    "name": name,
                    "path": current_path,
                    "is_dir": explicit_dir,
                    "explicit_dir": explicit_dir,
                    "raw": name,
                }
            )

            if not explicit_dir:
                stack.append((depth, current_path))

    def _parse_indented_format(self, lines: List[str]) -> None:
        """Parse indented format (spaces or tabs)."""
        stack: List[Tuple[int, Path]] = []

        for line in lines:
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Calculate indent
            stripped = line.lstrip()
            indent_len = len(line) - len(stripped)

            # Normalize indent (tab = 4 spaces)
            indent = indent_len // 4

            name = stripped.strip()
            name = self._clean_name(name)

            if not name:
                continue

            # Pop stack
            while stack and stack[-1][0] >= indent:
                stack.pop()

            # Build path
            if stack:
                parent_path = stack[-1][1]
                current_path = parent_path / name
            else:
                current_path = self.base_path / name

            explicit_dir = name.endswith("/") or name.endswith("\\")

            self.entries.append(
                {
                    "depth": indent,
                    "name": name,
                    "path": current_path,
                    "is_dir": explicit_dir,
                    "explicit_dir": explicit_dir,
                    "raw": name,
                }
            )

            if not explicit_dir:
                stack.append((indent, current_path))

    def _parse_simple_format(self, lines: List[str]) -> None:
        """Parse simple path format (one path per line)."""
        for line in lines:
            if not line.strip() or line.strip().startswith("#"):
                continue

            name = line.strip()
            name = self._clean_name(name)

            if not name:
                continue

            explicit_dir = name.endswith("/") or name.endswith("\\")
            clean_name = name.rstrip("/\\")

            self.entries.append(
                {
                    "depth": 0,
                    "name": clean_name,
                    "path": self.base_path / clean_name,
                    "is_dir": explicit_dir,
                    "explicit_dir": explicit_dir,
                    "raw": name,
                }
            )

    def _clean_name(self, name: str) -> str:
        """Clean entry name by removing comments and whitespace."""
        # Remove inline comments
        name = re.sub(r"\s+#.*$", "", name)
        name = name.strip()

        # Remove trailing slashes for comparison
        # But keep them for explicit_dir detection
        return name

    def _determine_file_types(self) -> None:
        """
        Determine which entries are files vs directories.
        Uses heuristics: explicit /, has extension, or has children.
        """
        # First pass: mark explicit directories
        for entry in self.entries:
            if entry["explicit_dir"] or entry["name"] in (".", "./", ".\\"):
                entry["is_dir"] = True

        # Second pass: mark entries with children as directories
        depths = [e["depth"] for e in self.entries]
        for i, entry in enumerate(self.entries):
            if entry["is_dir"]:
                continue

            # Check if next entry is a child
            if i + 1 < len(self.entries):
                next_entry = self.entries[i + 1]
                if next_entry["depth"] > entry["depth"]:
                    entry["is_dir"] = True

        # Third pass: mark entries with extensions as files
        for entry in self.entries:
            if not entry["is_dir"]:
                # Check if it looks like a file (has extension)
                if "." in entry["name"].split("/")[-1].split("\\")[-1]:
                    entry["is_dir"] = False


class ImageProcessor:
    """Process images for OCR to extract tree structure."""

    @staticmethod
    def is_image_file(path: Path) -> bool:
        """Check if file is an image."""
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]
        return path.suffix.lower() in image_extensions

    @staticmethod
    def preprocess_image(image_path: Path) -> Optional[Image.Image]:
        """
        Preprocess image for better OCR results.
        Converts to grayscale, applies thresholding, and enhances contrast.
        """
        try:
            # Open image
            img = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Convert to numpy array for OpenCV processing
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Convert back to PIL Image
            result = Image.fromarray(cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB))

            return result

        except Exception as e:
            print(f"Warning: Image preprocessing failed: {e}")
            return None

    @staticmethod
    def extract_text_from_image(image_path: Path) -> str:
        """Extract text from image using OCR."""
        if not HAS_OCR:
            raise ImportError(
                "OCR libraries not installed. "
                "Install with: pip install pytesseract opencv-python pillow"
            )

        # Try to preprocess
        processed_img = ImageProcessor.preprocess_image(image_path)
        if processed_img:
            img_to_ocr = processed_img
        else:
            img_to_ocr = Image.open(image_path)

        # Use pytesseract to extract text
        try:
            # Configure tesseract for better tree structure recognition
            custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=./\abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-\|"
            text = pytesseract.image_to_string(img_to_ocr, config=custom_config)
            return text
        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}")


def read_input(source: str) -> str:
    """Read input from file, stdin, or image."""
    path = Path(source)

    if source == "-":
        # Read from stdin
        return sys.stdin.read()

    if not path.exists():
        raise FileNotFoundError(f"Input not found: {source}")

    # Check if it's an image
    if ImageProcessor.is_image_file(path):
        if not HAS_OCR:
            raise ImportError(
                "Image input requires OCR libraries. "
                "Install with: pip install pytesseract opencv-python pillow numpy"
            )
        text = ImageProcessor.extract_text_from_image(path)
        return text

    # Read as text file
    return path.read_text(encoding="utf-8", errors="replace")


def create_tree(
    entries: List[Dict[str, Any]],
    base_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> Tuple[int, int]:
    """
    Create the folder tree from parsed entries.
    Returns (created_dirs, created_files).
    """
    created_dirs = 0
    created_files = 0

    # Sort entries by depth and path for proper ordering
    sorted_entries = sorted(entries, key=lambda x: (x["depth"], str(x["path"])))

    for entry in sorted_entries:
        name = entry["name"]
        path = entry["path"]
        is_dir = entry["is_dir"]

        # Skip root
        if name == ".":
            continue

        # Make path relative to base
        try:
            relative_path = path.relative_to(base_path)
        except ValueError:
            relative_path = path

        if dry_run:
            item_type = "dir" if is_dir else "file"
            print(f"  [{item_type.upper()}] {relative_path}")
            if is_dir:
                created_dirs += 1
            else:
                created_files += 1
            continue

        # Ensure parent directories exist
        parent = path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"  Created parent dir: {parent.relative_to(base_path)}/")

        # Create file or directory
        if is_dir:
            if not path.exists():
                path.mkdir(exist_ok=True)
                created_dirs += 1
                if verbose:
                    print(f"  Created dir:  {relative_path}/")
            else:
                if verbose:
                    print(f"  Exists dir:  {relative_path}/")
        else:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                created_files += 1
                if verbose:
                    print(f"  Created file: {relative_path}")
            else:
                if verbose:
                    print(f"  Exists file: {relative_path}")

    return created_dirs, created_files


def validate_entries(entries: List[Dict[str, Any]]) -> bool:
    """Validate parsed entries."""
    if not entries:
        print("Warning: No valid entries found in input.")
        return False

    # Check for root
    has_root = any(e["name"] == "." for e in entries)

    # Check if all entries have required fields
    for entry in entries:
        if "path" not in entry:
            print(f"Warning: Entry missing path: {entry}")
            return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create folder tree from text file or image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From text file
  python create_tree.py tree.txt
  
  # From image (screenshot)
  python create_tree.py folder_tree.png
  
  # With output directory
  python create_tree.py tree.txt --output ./my_project
  
  # Dry run
  python create_tree.py tree.txt --dry-run
  
  # Verbose mode
  python create_tree.py tree.txt -v
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help='Input file (text or image) or "-" for stdin',
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="Output directory (default: current directory)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating",
    )

    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing files/directories"
    )

    parser.add_argument(
        "--format",
        choices=["auto", "tree", "simple", "indented"],
        default="auto",
        help="Force a specific input format (default: auto-detect)",
    )

    args = parser.parse_args()

    # Read input
    try:
        text = read_input(args.input)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
        print(f"Format: {args.format}")
        print(f"Text length: {len(text)} characters")
        print()

    # Parse
    base_path = Path(args.output).resolve()

    parser = TreeParser(base_path)
    entries = parser.parse(text)

    if not validate_entries(entries):
        print("No valid tree structure found in input.")
        sys.exit(1)

    if args.verbose:
        print(f"Parsed {len(entries)} entries:")
        for entry in entries:
            if entry["name"] != ".":
                item_type = "DIR" if entry["is_dir"] else "FILE"
                print(f"  [{item_type}] depth={entry['depth']} {entry['name']}")
        print()

    # Create tree
    created_dirs, created_files = create_tree(
        entries, base_path, dry_run=args.dry_run, verbose=args.verbose
    )

    if args.dry_run:
        print(
            f"\n[DRY RUN] Would create {created_dirs} directories and {created_files} files"
        )
    else:
        print(
            f"\nCreated {created_dirs} directories and {created_files} files in: {base_path}"
        )


if __name__ == "__main__":
    # Import numpy for image processing
    try:
        import numpy as np
    except ImportError:
        np = None

    main()
