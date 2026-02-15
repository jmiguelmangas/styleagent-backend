from fastapi import FastAPI

from app.api.routers import artifacts_router, styles_router

app = FastAPI(title="StyleAgent Backend")

app.include_router(styles_router)
app.include_router(artifacts_router)

@app.get("/health")
def health():
    return {"status": "ok"}
