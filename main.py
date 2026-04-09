from fastapi import FastAPI

from routers.ask import router as ask_router


app = FastAPI(title="AI Assistant Service", version="1.0.0")
app.include_router(ask_router)

