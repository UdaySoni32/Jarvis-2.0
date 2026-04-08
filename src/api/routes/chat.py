"""
Chat Routes

LLM chat completions, streaming, and conversation management.
"""

from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import asyncio
import json

from . import chat_router
from ..schemas import ChatRequest, ChatResponse
from ..routes.auth import get_current_user
from ..utils import get_db
from ...core.llm.manager import llm_manager
from ...core.config import settings


@chat_router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create chat completion
    
    Send a message to the LLM and get a response.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Set model if specified
        if request.model:
            llm_manager.set_model(request.model)
        
        # Prepare context messages
        messages = []
        if request.context:
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.context
            ]
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Get completion from LLM
        response_text = await llm_manager.get_completion(messages)
        
        # Save to conversation history
        from ..models.conversation import ConversationHistory
        
        # Save user message
        user_msg = ConversationHistory(
            user_id=current_user.id,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            model_used=llm_manager.current_model,
        )
        db.add(user_msg)
        
        # Save assistant response
        assistant_msg = ConversationHistory(
            user_id=current_user.id,
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            model_used=llm_manager.current_model,
        )
        db.add(assistant_msg)
        db.commit()
        
        return ChatResponse(
            message=response_text,
            conversation_id=conversation_id,
            model_used=llm_manager.current_model,
            created_at=datetime.utcnow(),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}",
        )


@chat_router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create streaming chat completion
    
    Stream the LLM response in real-time.
    """
    async def generate():
        """Generate streaming response"""
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Set model if specified
            if request.model:
                llm_manager.set_model(request.model)
            
            # Prepare messages
            messages = []
            if request.context:
                messages = [
                    {"role": msg.role.value, "content": msg.content}
                    for msg in request.context
                ]
            messages.append({"role": "user", "content": request.message})
            
            # Stream response
            full_response = ""
            async for chunk in llm_manager.stream_completion(messages):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
            
            # Save to database
            from ..models.conversation import ConversationHistory
            
            user_msg = ConversationHistory(
                user_id=current_user.id,
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                model_used=llm_manager.current_model,
            )
            db.add(user_msg)
            
            assistant_msg = ConversationHistory(
                user_id=current_user.id,
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                model_used=llm_manager.current_model,
            )
            db.add(assistant_msg)
            db.commit()
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@chat_router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation history
    
    Retrieve all messages in a conversation.
    """
    from ..models.conversation import ConversationHistory
    
    messages = db.query(ConversationHistory).filter(
        ConversationHistory.conversation_id == conversation_id,
        ConversationHistory.user_id == current_user.id,
    ).order_by(ConversationHistory.created_at).all()
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
        "total": len(messages),
    }


@chat_router.get("/conversations")
async def list_conversations(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """
    List user's conversations
    
    Get a list of all conversation IDs for the current user.
    """
    from ..models.conversation import ConversationHistory
    from sqlalchemy import func, distinct
    
    # Get unique conversation IDs
    conversations = db.query(
        ConversationHistory.conversation_id,
        func.max(ConversationHistory.created_at).label("last_message"),
        func.count(ConversationHistory.id).label("message_count")
    ).filter(
        ConversationHistory.user_id == current_user.id
    ).group_by(
        ConversationHistory.conversation_id
    ).order_by(
        func.max(ConversationHistory.created_at).desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "conversations": [
            {
                "conversation_id": conv.conversation_id,
                "last_message": conv.last_message,
                "message_count": conv.message_count,
            }
            for conv in conversations
        ],
        "total": len(conversations),
    }
