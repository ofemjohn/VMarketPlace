from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.auth.services import get_current_user
from src.chat.models import ChatRoom
from src.chat.schemas import ChatRoomCreate, ChatRoomSchema, ChatMessageCreate, ChatMessageSchema
from src.chat.services import create_chat_room, create_chat_message, get_chat_room_by_id, get_user_chat_rooms, get_veterinarian_chat_rooms

router = APIRouter(prefix="/chat", tags=["chat"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.post("/rooms", response_model=ChatRoomSchema)
async def create_chat_room_route(
    room_data: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    chat_room = create_chat_room(db, current_user, room_data)
    return chat_room

@router.post("/rooms/{chat_room_id}/messages", response_model=ChatMessageSchema)
async def send_message_route(
    chat_room_id: int,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    chat_room = get_chat_room_by_id(db, chat_room_id)
    message = create_chat_message(db, chat_room, current_user, message_data)
    return message

@router.websocket("/ws/{chat_room_id}")
async def websocket_endpoint(websocket: WebSocket, chat_room_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            chat_room = get_chat_room_by_id(db, chat_room_id)
            message = create_chat_message(db, chat_room, websocket, data)
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/user-rooms", response_model=List[ChatRoomSchema])
async def list_user_chat_rooms(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_user_chat_rooms(db, current_user)

@router.get("/vet-rooms", response_model=List[ChatRoomSchema])
async def list_veterinarian_chat_rooms(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    veterinarian = current_user.veterinarian
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return get_veterinarian_chat_rooms(db, veterinarian.id)
