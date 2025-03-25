from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middlewares import LoggingMiddleware
from app.api.routes import auth_router, game_content_router, profile_router, games_managment_router, analysis_router
from app.utils.logging import setup_logging


def main():
    # FastAPI
    app = FastAPI()

    # Configure CORS to allow requests from the frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3002"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    app.include_router(auth_router)
    app.include_router(game_content_router)
    app.include_router(profile_router)
    app.include_router(games_managment_router)
    app.include_router(analysis_router)

    # Logging
    setup_logging()

    return app

if __name__ == "__main__":
    import uvicorn

    app = main()

    uvicorn.run(app, host="0.0.0.0", port=8000, use_colors=True)
