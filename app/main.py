from fastapi import FastAPI

app = FastAPI(title="StyleAgent Backend")

@app.get("/health")
def health():
    return {"status": "ok"}
