# SignalWatch RM Dashboard

Run the persistent application server from the repo root:

```powershell
python -m server.manage_users create --username admin --display-name "Security Admin" --role admin
```

Then start the server:

```powershell
python -m server.app --port 8765 --workers 4
```

Open:

```text
http://localhost:8765/dashboard/
```

The dashboard loads its state from `/api/bootstrap`. Extracted and enriched documents are held in schema-free TinyDB collections:

- Seed database: `storage/signalwatch.seed.json`
- Runtime document database: `runtime/signalwatch.documents.json`
- Structured RM/job state: `runtime/signalwatch.db`

RM review actions, watchlists, notification preferences, refresh jobs, and notification queues are server-side and scoped to the selected relationship manager. Column widths and the last selected RM are the only browser-local preferences.
