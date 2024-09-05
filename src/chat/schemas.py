from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class ChatMessageSchema(BaseModel):
    id: int
    chat_room_id: int
    sender_id: int
    content: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class ChatRoomCreate(BaseModel):
    veterinarian_id: Optional[int] = None
    listing_id: Optional[int] = None

class ChatRoomSchema(BaseModel):
    id: int
    user_id: int
    veterinarian_id: Optional[int] = None
    listing_id: Optional[int] = None
    created_at: datetime
    messages: List[ChatMessageSchema]

    class Config:
        from_attributes = True
