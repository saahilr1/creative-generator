#!/usr/bin/env bash
# One-time setup. Runs quietly (full logs in setup.log) so an agent running this
# doesn't pull ~hundreds of install lines into its context. Re-runnable.
set -e
echo "Setting up creative-generator (detailed logs -> setup.log)…"

python3 -m pip install -q -r requirements.txt   > setup.log 2>&1
python3 -m playwright install chromium          >> setup.log 2>&1
echo "  ✅ Python deps + headless browser installed."

if [ ! -f .env ]; then cp .env.example .env; echo "  ✅ created .env from template."; fi
if grep -q "^NVIDIA_API_KEY=nvapi-" .env 2>/dev/null; then
  echo "  ✅ NVIDIA key found in .env."
else
  echo "  →  ADD your free NVIDIA key to .env  (get one: build.nvidia.com → 'Get API Key')."
fi

echo "Done. Next: in your coding agent, say \"onboard me\"."
