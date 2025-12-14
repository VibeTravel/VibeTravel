from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.health import router as health_router
from routes.phase1 import router as phase1_router
from routes.ratings import router as ratings_router  
from routes.phase2 import router as phase2_router
from routes.phase3 import router as phase3_router 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(phase1_router)
app.include_router(ratings_router)
app.include_router(phase2_router)
app.include_router(phase3_router)