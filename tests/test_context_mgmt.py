"""
Test context management system.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_context_manager():
    """Test context management features."""
    print("\n🧪 Testing Context Management System...\n")
    
    try:
        from core.memory.semantic import SemanticMemoryManager
        from core.memory.context import ContextManager
        from core.memory.models import Message
        
        print("✓ Imported modules")
        
        # Initialize managers
        memory = SemanticMemoryManager()
        context_mgr = ContextManager(memory)
        print("✓ Managers initialized")
        
        # Start session and add test messages
        print("\n📝 Creating test conversation...")
        session = memory.start_session(title="Context Test")
        
        # Add a conversation about Python
        memory.add_message("user", "I want to learn Python programming")
        memory.add_message("assistant", "Python is a great language to start with! What would you like to build?")
        memory.add_message("user", "I want to create web applications")
        memory.add_message("assistant", "Perfect! For web apps, I recommend learning Flask or Django.")
        
        # Topic change: machine learning
        memory.add_message("user", "What about machine learning?")
        memory.add_message("assistant", "Machine learning with Python is powerful! Start with scikit-learn and pandas.")
        memory.add_message("user", "Can you explain neural networks?")
        memory.add_message("assistant", "Neural networks are computational models inspired by the brain.")
        
        # Topic change: databases
        memory.add_message("user", "How do I work with databases?")
        memory.add_message("assistant", "For databases, you can use SQLAlchemy with Python.")
        
        print("✓ Added 10 messages across multiple topics")
        
        # Wait for embeddings
        await asyncio.sleep(1)
        
        # Test context prioritization
        print("\n📊 Testing context prioritization...")
        all_messages = memory.get_context_messages()
        prioritized = context_mgr.prioritize_context(
            all_messages,
            "web development with Python",
            max_messages=5
        )
        print(f"✓ Prioritized to {len(prioritized)} most relevant messages")
        
        # Test smart context
        print("\n🎯 Testing smart context retrieval...")
        smart_context = context_mgr.get_smart_context(
            "building web applications",
            use_semantic=True
        )
        print(f"✓ Retrieved {len(smart_context)} semantically relevant messages")
        
        # Test summarization
        print("\n📝 Testing conversation summarization...")
        summary = context_mgr.summarize_messages(all_messages, max_length=50)
        print(f"✓ Summary: {summary[:100]}...")
        
        # Test conversation summary
        print("\n📊 Testing conversation summary...")
        conv_summary = context_mgr.get_conversation_summary()
        print(f"✓ Active: {conv_summary['active']}")
        print(f"  Messages: {conv_summary['message_count']}")
        print(f"  Topics: {', '.join(conv_summary['topics'][:3])}")
        
        # Test conversation flow tracking
        print("\n🔄 Testing conversation flow tracking...")
        flow = context_mgr.track_conversation_flow()
        print(f"✓ Identified {len(flow)} conversation segments")
        for i, segment in enumerate(flow, 1):
            print(f"  Segment {i}: {segment['message_count']} messages, keywords: {segment['topic_keywords'][:3]}")
        
        # Test token estimation
        print("\n🔢 Testing token estimation...")
        tokens = context_mgr.estimate_token_count(all_messages)
        print(f"✓ Estimated {tokens} tokens for {len(all_messages)} messages")
        
        # Test context trimming
        print("\n✂️  Testing context trimming...")
        trimmed = context_mgr.trim_context_to_fit(all_messages, max_tokens=200)
        print(f"✓ Trimmed from {len(all_messages)} to {len(trimmed)} messages to fit token limit")
        
        print("\n✅ All context management tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run context management tests."""
    print("=" * 70)
    print("CONTEXT MANAGEMENT SYSTEM TEST")
    print("=" * 70)
    
    success = await test_context_manager()
    
    print("\n" + "=" * 70)
    print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    print("=" * 70)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
