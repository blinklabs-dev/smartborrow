from fastapi import FastAPI

from .core.database import engine, Base
from .routers import users
from .models import user, snowflake_connection, optimization_check # Import models to ensure they are registered with Base

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Snowflake Optimization Agent")

app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Snowflake Optimization Agent API"}
