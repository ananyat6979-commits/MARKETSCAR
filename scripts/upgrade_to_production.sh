#!/usr/bin/env bash
set -e
if [ -z "$1" ]; then
  echo "Usage: $0 <path-to-real-uci-csv>"
  exit 2
fi
REAL="$1"
python scripts/baseline_freezer.py --input "$REAL" \
  --out data/baselines/manifest.json \
  --source-url "https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx" \
  --note "Official UCI Online Retail II import"
python scripts/calibrate.py --input "$REAL" --rows 10000 --seed 42 --out config/frozen_thresholds.json
echo "Production baseline installed. Commit data/baselines/manifest.json and config/frozen_thresholds.json."
