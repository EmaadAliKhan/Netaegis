# Training data (`data/`)

Place one or more **CICIDS2017-style** CSV files here (extension `.csv`) before running `run_training.py`.

## Required columns

The pipeline expects these headers (names are configurable in `data_pipeline.ColumnMapping`; defaults below):

| Column | Example |
|--------|---------|
| `Protocol` | IANA number (e.g. `6` TCP, `17` UDP) |
| `Destination Port` | e.g. `80`, `443` |
| `Flow Duration` | numeric |
| `Flow Packets/s` | numeric (packet rate) |
| `Label` | Must include **`BENIGN`** for benign rows (case-insensitive match) |

## Large files

If CSVs are too big for GitHub, keep them local or use Git LFS. Optionally set `TRAINING_DATA_DIR` in `.env` to point at another folder on disk.
