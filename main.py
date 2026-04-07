from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI()

# include API routes
app.include_router(router)

# serve frontend (HTML)
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")
