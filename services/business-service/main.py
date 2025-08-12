from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Business Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "business-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/business/info")
async def business_info():
    return {
        "service": "business-service",
        "version": "1.0.0",
        "description": "Domain-specific business logic service"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
