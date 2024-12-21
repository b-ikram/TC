from fastapi import FastAPI
from Employe import router as employe_router

# Create the FastAPI app
app = FastAPI()

# Include the router from Employe
app.include_router(employe_router, prefix="/employe", tags=["Employe"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Employee API"}