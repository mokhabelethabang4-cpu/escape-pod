from pathlib import Path
import re
import sys

from pypdf import PdfReader


PROJECT_FOLDER = Path(__file__).resolve().parent
DOWNLOADS_FOLDER = Path.home() / "storage" / "downloads"
OUTPUT_FOLDER = PROJECT_FOLDER / "imports"


def clean_extracted_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x00", "")
    lines = []
    for line in text.split("\n"):
        line = line.rstrip()
        line = re.sub(r"[ \t]+", " ", line)
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip()


def looks_like_heading(line):
    line = line.strip()
    if not line or len(line) > 100:
        return False
    words = line.split()
    if len(words) > 12 or line.endswith((".", ",", ";", ":")):
        return False
    if re.match(r"^\d+(?:\.\d+)*\.?\s+\S", line):
        return True
    letters = [char for char in line if char.isalpha()]
    if len(letters) >= 4:
        ratio = sum(char.isupper() for char in letters) / len(letters)
        if ratio >= 0.8:
            return True
    return False


def convert_to_markdown(text, title):
    text = clean_extracted_text(text)
    if not text:
        return f"# {title}\n\n"

    output_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            output_lines.append("")
        elif stripped.startswith(("# ", "## ", "### ")):
            output_lines.append(stripped)
        elif stripped.startswith(("- ", "* ", "> ")):
            output_lines.append(stripped)
        elif re.match(r"^(?:\d+[.)]|[A-Za-z][.)])\s+", stripped):
            output_lines.append(stripped)
        elif looks_like_heading(stripped):
            output_lines.append(f"## {stripped}")
        else:
            output_lines.append(stripped)

    body = "\n".join(output_lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return f"# {title}\n\n{body}\n"


def write_new_file(destination, content):
    created = False
    try:
        with destination.open("x", encoding="utf-8") as file:
            created = True
            file.write(content)
        destination.chmod(0o600)
    except Exception:
        if created:
            try:
                destination.unlink()
            except OSError:
                pass
        raise


def import_pdf(filename):
    if Path(filename).name != filename or filename in (".", ".."):
        raise ValueError("Enter just the PDF filename, not a folder path.")
    if not filename.lower().endswith(".pdf"):
        raise ValueError("This importer currently accepts PDF files only.")

    downloads = DOWNLOADS_FOLDER.resolve()
    source = (DOWNLOADS_FOLDER / filename).resolve()

    try:
        source.relative_to(downloads)
    except ValueError:
        raise ValueError("The selected PDF must be inside Downloads.") from None

    if not source.is_file():
        raise FileNotFoundError(f"PDF not found in Downloads: {filename}")

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.chmod(0o700)
    destination = OUTPUT_FOLDER / f"{source.stem}.md"

    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError(
            "This PDF is password-protected; this importer does not handle it yet."
        )

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            raise ValueError(
                f"Could not extract text from PDF page {page_number}."
            ) from None
        if page_text.strip():
            pages.append(page_text)

    extracted_text = "\n\n".join(pages).strip()
    if not extracted_text:
        raise ValueError(
            "No selectable text found. This may be a scanned PDF that needs OCR."
        )

    title = source.stem.replace("_", " ").replace("-", " ")
    markdown = convert_to_markdown(extracted_text, title)
    write_new_file(destination, markdown)

    print("PDF import successful.")
    print(f"Pages: {len(reader.pages)}")
    print(f"Markdown saved to: {destination}")


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python import_document.py <PDF-filename>")
        print("Example:")
        print("  python import_document.py example.pdf")
        sys.exit(1)
    try:
        import_pdf(sys.argv[1])
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
