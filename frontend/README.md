# O2C Email Agent Frontend

Static dashboard (plain HTML/CSS/JS modules) for:
- 3 classification cards
- all emails table
- modal with Overview / Evidence / Reply tabs
- editable recommended reply + Send action

## Run

```bash
cd frontend
python3 -m http.server 5173
```

Open: `http://127.0.0.1:5173`

Docker:

```bash
docker compose up --build -d frontend
```

## Notes

- Entry file: `frontend/app.js` (module bootstrap)
- JS modules: `frontend/js/`
