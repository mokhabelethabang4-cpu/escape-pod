# Escape Pod

Escape Pod is a Python command-line project for importing text-based PDFs, encrypting files, and decrypting files.

## Features

- Import text from PDFs in the Termux Downloads folder.
- Convert extracted text into basic Markdown.
- Encrypt and decrypt files using AES-GCM.
- Protect the encryption key using Scrypt and AES-GCM.
- Refuse to overwrite existing output files.

## Requirements

- Android with Termux
- Python 3
- The `cryptography` and `pypdf` Python packages

## Installation

Install Python:

    pkg update
    pkg install python

Install the required Python packages:

    python -m pip install cryptography pypdf

For Downloads access, run:

    termux-setup-storage

## First-time key setup

From the project directory, run:

    python key_manager.py --setup

Choose a strong passphrase of at least 14 characters. Never share it or put it in GitHub.

The protected key is stored in `~/.escape-pod-public-keys/`. Losing the protected key or forgetting its passphrase may make encrypted files unrecoverable.

## Run the application

From the project directory, run:

    python menu.py

Follow the menu prompts.

## PDF limitations

Scanned PDFs containing only images may need OCR before their text can be imported.

## Security

- Review files carefully before publishing them.
- Never publish private documents, encryption outputs, passphrases, or protected key files.
- `.gitignore` helps exclude sensitive files but is not a guarantee.
- This project has not been independently security-audited.
- Keep secure backups of important files and their protected keys.

## License

No license has been selected. Reuse and redistribution are not automatically granted without an applicable license.
