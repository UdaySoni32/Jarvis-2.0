"""
Tests for semantic memory and vector store.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.memory.vector_store import VectorStore
from core.memory.manager import MemoryManager
from datetime import datetime
import tempfile
import shutil


def test_vector_store():
    """Test vector store basic operations."""
    print("\n🧪 Testing VectorStore...")
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize vector store
        vector_store = VectorStore(persist_directory=temp_dir)
        print("✓ VectorStore initialized")
        
        # Test adding messages
        vector_store.add_message(
            message_id="msg1",
            content="What's the weather like today?",
            session_id="session1",
            role="user",
            timestamp=datetime.now()
        )
        
        vector_store.add_message(
            message_id="msg2",
            content="It's sunny with a temperature of 22 degrees.",
            session_id="session1",
            role="assistant",
            timestamp=datetime.now()
        )
        
        vector_store.add_message(
            message_id="msg3",
            content="Can you help me with Python coding?",
            session_id="session2",
            role="user",
            timestamp=datetime.now()
        )
        print("✓ Added test messages")
        
        # Test semantic search
        results = vector_store.search_similar_messages(
            query="How's the weather?",
            n_results=2
        )
        print(f"✓ Semantic search found {len(results)} results")
        
        # Verify results
        assert len(results) > 0, "Should find similar messages"
        assert "weather" in results[0]['content'].lower(), "Should find weather-related message"
        print("✓ Semantic search accuracy verified")
        
        # Test adding knowledge
        vector_store.add_knowledge(
            knowledge_id="k1",
            content="User prefers dark mode for all applications",
            category="preference",
            importance=0.8
        )
        
        vector_store.add_knowledge(
            knowledge_id="k2",
            content="Python is a high-level programming language",
            category="fact",
            importance=0.5
        )
        print("✓ Added knowledge items")
        
        # Test knowledge search
        knowledge = vector_store.search_knowledge(
            query="user interface settings",
            n_results=2
        )
        print(f"✓ Knowledge search found {len(knowledge)} results")
        
        # Get statistics
        stats = vector_store.get_statistics()
        print(f"✓ Statistics: {stats['conversations_count']} messages, {stats['knowledge_count']} knowledge items")
        
        print("\n✅ All VectorStore tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ VectorStore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_memory_manager_semantic():
    """Test memory manager with semantic search."""
    print("\n🧪 Testing MemoryManager with semantic search...")
    
    try:
        # Initialize memory manager
        manager = MemoryManager(enable_semantic_search=True)
        print("✓ MemoryManager initialized with semantic search")
        
        # Start session
        session = manager.start_session(title="Test Session")
        print(f"✓ Started session: {session.session_id}")
        
        # Add messages
        manager.add_message("user", "I love programming in Python")
        manager.add_message("assistant", "Python is a great language! What would you like to build?")
        manager.add_message("user", "I want to create a web application")
        manager.add_message("assistant", "Great! You could use Flask or Django for that.")
        print("✓ Added messages with semantic embeddings")
        
        # Wait a moment for indexing
        await asyncio.sleep(1)
        
        # Test semantic search
        similar = manager.search_similar_conversations(
            query="web development frameworks",
            n_results=2
        )
        print(f"✓ Found {len(similar)} semantically similar messages")
        
        # Add knowledge
        success = manager.add_knowledge(
            knowledge_id="pref1",
            content="User enjoys Python programming",
            category="preference",
            importance=0.9
        )
        assert success, "Should successfully add knowledge"
        print("✓ Added knowledge to long-term memory")
        
        # Search knowledge
        knowledge = manager.search_knowledge(
            query="programming languages the user likes",
            n_results=2
        )
        print(f"✓ Found {len(knowledge)} relevant knowledge items")
        
        # Get semantic context
        context = manager.get_semantic_context(
            query="building websites with Python",
            max_messages=3
        )
        print(f"✓ Retrieved {len(context)} semantically relevant messages")
        
        # Get stats
        stats = manager.get_memory_stats()
        print(f"✓ Memory stats: {stats}")
        
        print("\n✅ All MemoryManager semantic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ MemoryManager semantic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all semantic memory tests."""
    print("=" * 70)
    print("SEMANTIC MEMORY SYSTEM TESTS")
    print("=" * 70)
    
    # Test 1: Vector Store
    test1 = test_vector_store()
    
    # Test 2: Memory Manager Integration
    test2 = await test_memory_manager_semantic()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"VectorStore: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"MemoryManager Semantic: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    all_passed = test1 and test2
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
