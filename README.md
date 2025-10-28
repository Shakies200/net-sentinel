# net-sentinel
lightweight network activity monitoring tool designed to detect and log suspicious outbound connections in real time.
This short guide explains how to install, verify, and run net_sentinel_v01 — a lightweight network activity monitoring tool for Linux and Windows.

⚙️ 1. Requirements

Python 3.9 or later

pipx (recommended for easy installation)

(Optional) GPG for verifying the authenticity of the downloaded files

Installing pipx (if not already installed)

Linux:

python3 -m pip install --user pipx
python3 -m pipx ensurepath


Windows (PowerShell):

python -m pip install --user pipx
python -m pipx ensurepath


Close and reopen your terminal after running ensurepath.

📦 2. Installing net_sentinel_v01

After downloading the release file (for example:
net_sentinel_v01-0.1.0-py3-none-any.whl) to your computer:

pipx install ./net_sentinel_v01-0.1.0-py3-none-any.whl


If installation succeeds, you’ll see something like:

installed package net_sentinel_v01 0.1.0
  - net-sentinel
done! 🌟


This means the command net-sentinel is now available globally.

▶️ 3. Running the tool

Simple one-time scan:

net-sentinel --once


Continuous monitoring (recommended on Linux):

sudo -E net-sentinel


Use a custom configuration:

net-sentinel -c my_config.toml


Example config file (my_config.toml):

[general]
interval_seconds = 3
baseline_samples = 2
log_file = "net_sentinel_events.jsonl"

[thresholds]
bytes_per_sec_threshold = 2000000
many_connections_threshold = 40

📁 4. Log file

All alerts are saved in:

net_sentinel_events.jsonl


To watch the log live:

tail -f net_sentinel_events.jsonl

🔐 5. Verifying the authenticity of the files (GPG signature)

Each official release of net_sentinel_v01 is digitally signed by the developer
(Abdulrahman Khawaji) to prove that the files are genuine and unmodified.

Step 1 — Install GPG

Linux:

sudo apt install gnupg


Windows:
Install Gpg4win
 and open the command prompt (gpg will work there).

Step 2 — Import the developer’s public key

You can find the public key file mypubkey.asc in the GitHub release page.
To import it:

gpg --import mypubkey.asc


(Alternatively, if a key ID or fingerprint is published, you can get it directly from a key server.)

Step 3 — Verify the downloaded files

Make sure you downloaded:

The .whl or .tar.gz file

The matching .asc signature file

Then verify:

gpg --verify net_sentinel_v01-0.1.0-py3-none-any.whl.asc net_sentinel_v01-0.1.0-py3-none-any.whl


If everything is valid, you’ll see:

gpg: Good signature from "Abdulrahman Khawaji <abdulrahman.khawaji@hotmail.com>"


If you see this message, it means the file is authentic and safe.

(A warning like “This key is not certified with a trusted signature” is normal — it just means you haven’t personally marked the key as trusted yet.)

Step 4 — Optional: verify the source archive

If you downloaded the source code archive (.tar.gz) instead, run:

gpg --verify net_sentinel_v01-0.1.0.tar.gz.asc net_sentinel_v01-0.1.0.tar.gz

🪪 6. Troubleshooting
Problem	Solution
pipx: command not found	Run python3 -m pip install --user pipx && python3 -m pipx ensurepath
gpg: no valid OpenPGP data found	Check that the .asc file is complete (re-download it)
“key not certified with a trusted signature”	Normal: it means the key is not marked as trusted locally
Permission denied	Use sudo -E when running continuous monitoring
🧠 7. Quick Summary

Install pipx and GPG

Verify the developer’s signature (gpg --verify ...)

Install the tool using pipx

Run net-sentinel --once or sudo -E net-sentinel

Monitor logs at net_sentinel_events.jsonl
