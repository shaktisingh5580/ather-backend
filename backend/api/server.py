"""
FastAPI Server — Smart Parking System SCET
Entry point for the REST API. Run with:
    cd backend && python -m api.server
    OR
    cd backend && uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

# Import routers
from api.routes.gate import router as gate_router
from api.routes.user import router as user_router
from api.routes.admin import router as admin_router
from api.routes.visitor import router as visitor_router

app = FastAPI(
    title="🅿️ SCET Smart Parking System API",
    description=(
        "AI-driven parking automation for Sarvajanik College of Engineering & Technology. "
        "Handles ALPR gate events, user management, guardian mode, visitor registration, "
        "zone capacity, and admin analytics."
    ),
    version="1.0.0",
)

# Allow origins — dashboards may run on a different machine or Vercel
# Using explicit origins helps avoid strict-origin-when-cross-origin blocks
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://ather-admin-dashboard.vercel.app",
    "https://ather-user-frontend.vercel.app",
    "*"  # Wildcard fallback for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(gate_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(visitor_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "system": "SCET Smart Parking System",
        "status": "🟢 Online",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "gate": "/gate/trigger, /gate/manual-entry, /gate/resolve/{id}, /gate/events",
            "user": "/user/register, /user/login, /user/{id}, /user/vehicle, /user/guardian, /user/page-vehicle",
            "admin": "/admin/zones, /admin/alerts, /admin/analytics, /admin/lookup/{plate}, /admin/users, /admin/sessions",
            "visitor": "/visitor/register, /visitor/list",
        },
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "service": "smart-parking-api"}


# ── Direct execution: python -m api.server ──
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"\n🅿️  SCET Smart Parking API starting on http://{host}:{port}")
    print(f"   Swagger UI: http://{host}:{port}/docs")
    print(f"   Accepting connections from ALL machines on the network.\n")
    uvicorn.run("api.server:app", host=host, port=port, reload=True)
