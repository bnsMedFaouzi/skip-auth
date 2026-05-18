from fastapi import FastAPI

from auth import AuthContext, RequireAuth

app = FastAPI()


@app.get("/protected")
async def protected_route(auth: RequireAuth) -> dict:
    return {
        "message": "Access granted",
        "user": auth.user,
        "method": auth.method,
        "is_internal": auth.is_internal,
    }


@app.get("/public")
async def public_route() -> dict:
    return {"message": "Public route"}
