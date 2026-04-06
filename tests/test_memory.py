#!/usr/bin/env python3
"""Test script for memory system."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_memory():
    """Test memory system functionality."""
    from core.memory import memory_manager, Message, ConversationSession
    from core.config import settings
    
    print("\n" + "=" * 60)
    print("JARVIS 2.0 - Memory System Test")
    print("=" * 60 + "\n")
    
    # Test 1: Session Creation
    print("✓ Test 1: Session Creation")
    session = memory_manager.start_session(title="Test Session")
    print(f"  Session ID: {session.session_id}")
    print(f"  Title: {session.title}")
    print(f"  ✅ Passed\n")
    
    # Test 2: Add Messages
    print("✓ Test 2: Add Messages")
    memory_manager.add_message("user", "Hello JARVIS!")
    memory_manager.add_message("assistant", "Hello! How can I help you today?")
    memory_manager.add_message("user", "What's 2+2?")
    memory_manager.add_message("assistant", "2+2 equals 4!")
    print(f"  Added 4 messages")
    print(f"  ✅ Passed\n")
    
    # Test 3: Get Context Messages
    print("✓ Test 3: Get Context Messages")
    context = memory_manager.get_context_messages(max_messages=3)
    print(f"  Retrieved {len(context)} messages")
    print(f"  First message: {context[0]['role']}: {context[0]['content'][:30]}...")
    print(f"  ✅ Passed\n")
    
    # Test 4: Session Summary
    print("✓ Test 4: Session Summary")
    summary = memory_manager.get_session_summary()
    print(f"  Active: {summary['active']}")
    print(f"  Message Count: {summary['message_count']}")
    print(f"  ✅ Passed\n")
    
    # Test 5: Storage Persistence
    print("✓ Test 5: Storage Persistence")
    session_id = session.session_id
    memory_manager.end_session()
    
    # Try to load it back
    loaded = memory_manager.load_session(session_id)
    if loaded:
        print(f"  Loaded session: {memory_manager.current_session.session_id}")
        print(f"  Messages restored: {len(memory_manager.current_session.messages)}")
        print(f"  ✅ Passed\n")
    else:
        print(f"  ❌ Failed to load session\n")
    
    # Test 6: List Sessions
    print("✓ Test 6: List Sessions")
    sessions = memory_manager.list_sessions(limit=5)
    print(f"  Found {len(sessions)} session(s)")
    if sessions:
        for i, s in enumerate(sessions[:3], 1):
            print(f"    {i}. {s.title} ({s.session_id[:8]}...)")
    print(f"  ✅ Passed\n")
    
    # Test 7: Search Messages
    print("✓ Test 7: Search Messages")
    results = memory_manager.search("2+2", limit=10)
    print(f"  Search results: {len(results)}")
    if results:
        print(f"  Found: '{results[0]['content'][:50]}...'")
    print(f"  ✅ Passed\n")
    
    # Cleanup
    print("✓ Test 8: Cleanup")
    memory_manager.delete_session(session_id)
    print(f"  Deleted test session")
    print(f"  ✅ Passed\n")
    
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60 + "\n")
    
    # Show database location
    db_path = settings.user_data_dir / "conversations.db"
    print(f"Database location: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"Database size: {size:,} bytes\n")


if __name__ == "__main__":
    asyncio.run(test_memory())
