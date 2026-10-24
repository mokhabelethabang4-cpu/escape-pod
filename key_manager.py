from pathlib import Path
import getpass
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


KEY_FOLDER = Path.home() / ".escape-pod-public-keys"
PROTECTED_FILE = KEY_FOLDER / "protected_key.bin"
AAD = b"Escape Pod protected key v1"
MAGIC = b"EPK1"


def _derive_wrapping_key(passphrase, salt):
    kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
    return kdf.derive(passphrase.encode("utf-8"))


def create_key():
    """Create a fresh AES-256 key protected by a passphrase."""
    if PROTECTED_FILE.exists():
        raise FileExistsError(
            "A protected key already exists. Refusing to replace it."
        )

    passphrase = getpass.getpass("Create a passphrase (at least 14 characters): ")
    confirmation = getpass.getpass("Enter the passphrase again: ")

    if len(passphrase) < 14:
        raise ValueError("Passphrase must be at least 14 characters.")
    if not hmac.compare_digest(passphrase, confirmation):
        raise ValueError("Passphrases do not match.")

    KEY_FOLDER.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        KEY_FOLDER.chmod(0o700)
    except OSError:
        pass

    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = AESGCM.generate_key(bit_length=256)
    wrapping_key = _derive_wrapping_key(passphrase, salt)
    encrypted_key = AESGCM(wrapping_key).encrypt(nonce, key, AAD)
    payload = MAGIC + salt + nonce + encrypted_key

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(PROTECTED_FILE, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
        try:
            PROTECTED_FILE.chmod(0o600)
        except OSError:
            pass
    except Exception:
        try:
            PROTECTED_FILE.unlink()
        except OSError:
            pass
        raise

    print("A new protected key was created.")
    print("Keep your passphrase safe: losing it may make your files unrecoverable.")


def unlock_key():
    """Unlock the AES-256 key without saving the raw key to disk."""
    if not PROTECTED_FILE.is_file():
        raise FileNotFoundError(
            "Protected key not found. Run 'python key_manager.py --setup' first."
        )

    payload = PROTECTED_FILE.read_bytes()
    if len(payload) != 80 or payload[:4] != MAGIC:
        raise ValueError("Protected key file format is invalid.")

    salt = payload[4:20]
    nonce = payload[20:32]
    encrypted_key = payload[32:]

    passphrase = getpass.getpass("Enter your Escape Pod passphrase: ")
    if not passphrase:
        raise ValueError("Passphrase cannot be empty.")

    wrapping_key = _derive_wrapping_key(passphrase, salt)
    try:
        key = AESGCM(wrapping_key).decrypt(nonce, encrypted_key, AAD)
    except InvalidTag:
        raise ValueError(
            "Could not unlock key: incorrect passphrase or damaged file."
        ) from None

    if len(key) != 32:
        raise ValueError("Recovered AES-256 key has invalid length.")
    return key


def load_key():
    return unlock_key()


def check_key():
    key = load_key()
    AESGCM(key)
    return True


if __name__ == "__main__":
    import sys

    try:
        if len(sys.argv) == 2 and sys.argv[1] == "--setup":
            create_key()
        elif len(sys.argv) == 1:
            check_key()
            print("Protected-key check passed.")
            print("The key was not displayed or saved to disk.")
        else:
            print("Usage: python key_manager.py [--setup]")
            raise SystemExit(2)
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
