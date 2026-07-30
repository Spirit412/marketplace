from fastapi.middleware.cors import CORSMiddleware

CORS_MIDDLEWARE = (
    CORSMiddleware,
    {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    },
)
