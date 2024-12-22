from fastapi import FastAPI
from endpoint.Admin import router as admin_router
from endpoint.Employe import router as employee_router
from endpoint.RH import router as rh_router
from endpoint.token import router as token_router


app = FastAPI()

# Inclure les routers dans l'application FastAPI
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(employee_router, prefix="/employee", tags=["employee"])
app.include_router(rh_router, prefix="/RH", tags=["RH"])
app.include_router(token_router, prefix="/token", tags=["token"])


