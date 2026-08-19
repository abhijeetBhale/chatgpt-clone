from fastapi import APIRouter
from routes.chats import router as chats_router
from routes.userchats import router as userchats_router
from routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(chats_router)
api_router.include_router(userchats_router)
api_router.include_router(upload_router)
