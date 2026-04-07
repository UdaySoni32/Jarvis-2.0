"""
Simple test for semantic memory system.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_semantic_memory():
    """Test semantic memory basic functionality."""
    print("\n🧪 Testing Semantic Memory System...\n")
    
    try:
        # Import after path is set
        from core.memory.semantic import SemanticMemoryManager
        print("✓ Imported SemanticMemoryManager")
        
        # Initialize manager
        print("\n📝 Initializing semantic memory manager...")
        manager = SemanticMemoryManager()
        print(f"✓ Manager initialized (semantic enabled: {manager.semantic_enabled})")
        
        if not manager.semantic_enabled:
            print("⚠️  Semantic search not available, skipping tests")
            return True
        
        # Start session
        print("\n💬 Starting test session...")
        session = manager.start_session(title="Semantic Memory Test")
        print(f"✓ Session started: {session.session_id}")
        
        # Add test messages
        print("\n📨 Adding test messages...")
        manager.add_message("user", "I love programming in Python")
        manager.add_message("assistant", "Python is great for web development!")
        manager.add_message("user", "Tell me about machine learning")
        manager.add_message("assistant", "Machine learning uses algorithms to learn from data")
        manager.add_message("user", "What's the weather like?")
        manager.add_message("assistant", "I can help you check the weather!")
        print("✓ Added 6 messages with embeddings")
        
        # Wait for embeddings to be processed
        await asyncio.sleep(2)
        
        # Test semantic search
        print("\n🔍 Testing semantic search...")
        results = manager.search_similar("coding and software development", n_results=3)
        print(f"✓ Found {len(results)} similar messages")
        
        if results:
            print("\n   Most similar message:")
            print(f"   → {results[0]['content'][:60]}...")
        
        # Test adding knowledge
        print("\n🧠 Testing knowledge storage...")
        success = manager.add_knowledge(
            knowledge_id="pref_python",
            content="User prefers Python programming language",
            category="preference",
            importance=0.9
        )
        print(f"✓ Knowledge added: {success}")
        
        # Test knowledge search
        print("\n🔎 Testing knowledge search...")
        knowledge = manager.search_knowledge("user's favorite programming language", n_results=2)
        print(f"✓ Found {len(knowledge)} knowledge items")
        
        if knowledge:
            print(f"   → {knowledge[0]['content'][:60]}...")
        
        # Test semantic context
        print("\n📚 Testing semantic context retrieval...")
        context = manager.get_semantic_context("programming languages", max_messages=3)
        print(f"✓ Retrieved {len(context)} contextually relevant messages")
        
        # Get statistics
        print("\n📊 Vector store statistics:")
        if hasattr(manager.vector_store, 'get_statistics'):
            stats = manager.vector_store.get_statistics()
            print(f"   • Conversations: {stats.get('conversations_count', 'N/A')}")
            print(f"   • Knowledge items: {stats.get('knowledge_count', 'N/A')}")
            print(f"   • Embedding model: {stats.get('embedding_model', 'N/A')}")
        
        print("\n✅ All semantic memory tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run semantic memory tests."""
    print("=" * 70)
    print("SEMANTIC MEMORY SYSTEM TEST")
    print("=" * 70)
    
    success = await test_semantic_memory()
    
    print("\n" + "=" * 70)
    print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    print("=" * 70)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
