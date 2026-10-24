from pathlib import Path
import os
import sys

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from key_manager import load_key


PROJECT_FOLDER = Path(__file__).resolve().parent
ARCHIVE_FOLDER = PROJECT_FOLDER / "archive"
IMPORTS_FOLDER = PROJECT_FOLDER / "imports"

NONCE_SIZE = 12
TAG_SIZE = 16


def is_inside(path, folder):
    """Return True if path is inside folder, or is folder itself."""
    try:
        path.relative_to(folder)
        return True
    except ValueError:
        return False


def write_new_file(output, data):
    """Create a new private file and remove it if writing fails."""
    created = False
    try:
        with output.open("xb") as file:
            created = True
            file.write(data)
        output.chmod(0o600)
    except Exception:
        if created:
            try:
                output.unlink()
            except OSError:
                pass
        raise


def encrypt_file(source_path):
    source = Path(source_path).expanduser().resolve()
    project = PROJECT_FOLDER.resolve()
    archive = ARCHIVE_FOLDER.resolve()
    imports = IMPORTS_FOLDER.resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    if is_inside(source, archive):
        raise ValueError("Choose a source file outside the archive folder.")

    allowed_project_file = source.parent == project
    allowed_import_file = is_inside(source, imports)

    if not (allowed_project_file or allowed_import_file):
        raise ValueError(
            "For safety, encrypt files directly inside the Escape Pod "
            "project folder or inside imports."
        )

    ARCHIVE_FOLDER.mkdir(parents=True, exist_ok=True)
    ARCHIVE_FOLDER.chmod(0o700)

    output = archive / f"{source.name}.enc"
    if output.exists():
        raise FileExistsError(f"Encrypted output already exists: {output}")

    key = load_key()
    nonce = os.urandom(NONCE_SIZE)
    plaintext = source.read_bytes()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)

    write_new_file(output, nonce + ciphertext)
    return output


def decrypt_file(encrypted_path):
    encrypted = Path(encrypted_path).expanduser().resolve()
    archive = ARCHIVE_FOLDER.resolve()

    if not encrypted.is_file():
        raise FileNotFoundError(f"Encrypted file not found: {encrypted}")

    if encrypted.parent != archive:
        raise ValueError(
            "For safety, decrypt files stored directly inside the archive folder."
        )

    if not encrypted.name.endswith(".enc"):
        raise ValueError("Encrypted filenames must end with .enc.")

    data = encrypted.read_bytes()
    if len(data) < NONCE_SIZE + TAG_SIZE:
        raise ValueError("Encrypted file is too short or damaged.")

    nonce = data[:NONCE_SIZE]
    ciphertext = data[NONCE_SIZE:]
    key = load_key()

    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError(
            "Decryption failed: wrong key or damaged file."
        ) from None

    output_name = encrypted.name[:-4]
    output = PROJECT_FOLDER.resolve() / f"{output_name}.decrypted"

    if output.exists():
        raise FileExistsError(f"Decrypted output already exists: {output}")

    write_new_file(output, plaintext)
    return output


def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python file_crypto.py encrypt <file>")
        print("  python file_crypto.py decrypt <file>")
        sys.exit(1)

    action, filename = sys.argv[1], sys.argv[2]

    try:
        if action == "encrypt":
            result = encrypt_file(filename)
            print(f"Encryption successful: {result}")
        elif action == "decrypt":
            result = decrypt_file(filename)
            print(f"Decryption successful: {result}")
        else:
            print("ERROR: Action must be encrypt or decrypt.")
            sys.exit(1)
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
