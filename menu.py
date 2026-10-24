
from pathlib import Path
import subprocess
import sys


PROJECT_FOLDER = Path(__file__).resolve().parent


def show_menu():
    print()
    print("=" * 36)
    print("           ESCAPE POD")
    print("=" * 36)
    print("  1. Import a PDF from Downloads")
    print("  2. Encrypt a file")
    print("  3. Decrypt an archived file")
    print("  4. Exit")
    print("=" * 36)


def run_script(script_name, *arguments):
    script_path = PROJECT_FOLDER / script_name

    if not script_path.is_file():
        print(f"ERROR: Cannot find {script_name}.")
        print("Check that the file exists in your Escape Pod folder.")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), *arguments],
            cwd=str(PROJECT_FOLDER),
            check=False,
        )

        if result.returncode != 0:
            print()
            print("That operation did not finish successfully.")
            print("Read the error above, correct the problem, and try again.")

    except OSError as error:
        print(f"ERROR: Could not start {script_name}: {error}")


def ask_for_text(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print("\nNo input received.")
        return ""


def import_pdf():
    print()
    print("IMPORT A PDF")
    print("Enter the PDF's filename from your Downloads folder.")
    print("Example: my_document.pdf")

    filename = ask_for_text("PDF filename: ")

    if not filename:
        print("Cancelled: no filename entered.")
        return

    if Path(filename).name != filename or filename in (".", ".."):
        print("ERROR: Enter only the filename, not a folder path.")
        return

    if not filename.lower().endswith(".pdf"):
        print("ERROR: The filename must end in .pdf.")
        return

    run_script("import_document.py", filename)


def encrypt_file():
    print()
    print("ENCRYPT A FILE")
    print("Enter a file inside the Escape Pod folder or imports folder.")
    print("Example: imports/my_document.md")

    filename = ask_for_text("File path: ")

    if not filename:
        print("Cancelled: no file path entered.")
        return

    run_script("file_crypto.py", "encrypt", filename)


def decrypt_file():
    print()
    print("DECRYPT AN ARCHIVED FILE")
    print("Enter an encrypted file stored directly inside archive.")
    print("Example: archive/my_document.md.enc")

    filename = ask_for_text("Encrypted file path: ")

    if not filename:
        print("Cancelled: no file path entered.")
        return

    run_script("file_crypto.py", "decrypt", filename)


def main():
    print("\nWelcome to Escape Pod.")
    print("Your local document tool.")

    try:
        while True:
            show_menu()
            choice = ask_for_text("Choose an option (1-4): ")

            if choice == "1":
                import_pdf()
            elif choice == "2":
                encrypt_file()
            elif choice == "3":
                decrypt_file()
            elif choice == "4":
                print("\nEscape Pod closed. Goodbye!")
                break
            elif not choice:
                print("Please enter a choice from 1 to 4.")
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    except KeyboardInterrupt:
        print("\nEscape Pod closed safely. Goodbye!")


if __name__ == "__main__":
    main()
