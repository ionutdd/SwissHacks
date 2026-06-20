# SignalWatch RM Dashboard

Run from the repo root:

```powershell
python -m http.server 8765
```

Open:

```text
http://localhost:8765/dashboard/
```

The dashboard reads:

- `data_01/baseline_snapshots.json`
- `data_02/documents.json`
- `data_03/facts.json`
- `data_03/alerts.json`

RM review actions are stored locally in the browser under `signalwatch.reviewActions.v1`.
