from fastapi import APIRouter
from routes.chats import router as chats_router
from routes.userchats import router as userchats_router
from routes.upload import router as upload_router
from routes.admin_flags import router as admin_flags_router
from routes.preferences import router as preferences_router
from routes.memory import router as memory_router
from routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(chats_router)
api_router.include_router(userchats_router)
api_router.include_router(upload_router)
api_router.include_router(admin_flags_router)
api_router.include_router(preferences_router)
api_router.include_router(memory_router)
api_router.include_router(users_router)
