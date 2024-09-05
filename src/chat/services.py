from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.chat.models import ChatRoom, ChatMessage
from src.chat.schemas import ChatMessageCreate, ChatRoomCreate
from src.auth.models import User
from src.veterinarians.models import Veterinarian
from src.petlisting.models import PetListing
from src.notifications import send_push_notification
from typing import List

def create_chat_room(db: Session, user: User, room_data: ChatRoomCreate) -> ChatRoom:
    if room_data.veterinarian_id:
        vet = db.query(Veterinarian).filter(Veterinarian.id == room_data.veterinarian_id).first()
        if not vet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian not found")

    if room_data.listing_id:
        listing = db.query(PetListing).filter(PetListing.id == room_data.listing_id).first()
        if not listing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    chat_room = ChatRoom(user_id=user.id, veterinarian_id=room_data.veterinarian_id, listing_id=room_data.listing_id)
    db.add(chat_room)
    db.commit()
    db.refresh(chat_room)
    return chat_room

def create_chat_message(db: Session, chat_room: ChatRoom, sender: User, message_data: ChatMessageCreate) -> ChatMessage:
    message = ChatMessage(chat_room_id=chat_room.id, sender_id=sender.id, content=message_data.content)
    db.add(message)
    db.commit()
    db.refresh(message)

    # Send notification to the other party
    recipient_id = chat_room.veterinarian_id if chat_room.veterinarian_id != sender.id else chat_room.user_id
    recipient = db.query(User).filter(User.id == recipient_id).first()
    send_push_notification(recipient.expo_push_token, "New Message", f"New message from {sender.username}")

    return message

def get_chat_room_by_id(db: Session, chat_room_id: int) -> ChatRoom:
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
    if not chat_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found")
    return chat_room

def get_user_chat_rooms(db: Session, user: User) -> List[ChatRoom]:
    return db.query(ChatRoom).filter(ChatRoom.user_id == user.id).all()

def get_veterinarian_chat_rooms(db: Session, veterinarian_id: int) -> List[ChatRoom]:
    return db.query(ChatRoom).filter(ChatRoom.veterinarian_id == veterinarian_id).all()
