# RoadAudit AI presentation dashboard

This is the handoff's Next.js presentation interface. It displays fixed sample inspection data and bundled demo media. It does not connect to the live Python app or accept live uploads. For real image and video inspection, run the root Streamlit and FastAPI application.

Requirements: Node.js 20.9 or newer.

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. Run `npm run build` to check the production build.
