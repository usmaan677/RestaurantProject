from fastapi import FastAPI
import auth, notifications, services, queues, history

app = FastAPI(title="QueueSmart API")

app.include_router(auth.router)
app.include_router(notifications.router)
app.include_router(services.router)
app.include_router(queues.router)
app.include_router(history.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}