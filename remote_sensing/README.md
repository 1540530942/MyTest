# Remote Sensing Module

This is the executable scaffold for the `sensing.wangyutang.com` module route.

It intentionally keeps the first surface small: health, module metadata, and a simple landing page. Add imagery ingestion, map layers, timelines, and alert APIs here as the remote-sensing design becomes concrete.

## Run Locally

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Health endpoint:

```text
http://127.0.0.1:8090/api/health
```
