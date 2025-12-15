"""
Debug script to test GenAI/Groq integration directly
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_groq_connectivity():
    print("=" * 60)
    print("GENAI/GROQ INTEGRATION DEBUG")
    print("=" * 60)
    
    # 1. Check environment variable
    from app.core.config import settings
    
    print("\n[1] CHECKING CONFIGURATION...")
    print(f"    GROQ_API_KEY: {'*****' + settings.GROQ_API_KEY[-8:] if settings.GROQ_API_KEY else 'NOT SET'}")
    print(f"    GROQ_MODEL: {settings.GROQ_MODEL}")
    print(f"    Key length: {len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else 0}")
    
    if not settings.GROQ_API_KEY:
        print("\n[ERROR] GROQ_API_KEY is not set!")
        return False
    
    # 2. Test Groq client directly
    print("\n[2] TESTING GROQ CLIENT DIRECTLY...")
    try:
        from groq import Groq
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        print("    [OK] Groq client created successfully")
        
        # Test API call
        print("\n[3] TESTING GROQ API CALL...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Use currently supported model
            messages=[{"role": "user", "content": "Say 'Hello, GenAI is working!' in exactly those words."}],
            max_tokens=50,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        print(f"    [OK] API Response: {content[:100]}...")
        print(f"    [OK] Tokens used: {tokens}")
        print("\n[SUCCESS] Groq API is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Groq API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_genai_service():
    print("\n" + "=" * 60)
    print("TESTING GENAI SERVICE")
    print("=" * 60)
    
    try:
        from app.services.genai_service import genai_service, GenAIRequest, PromptType
        
        print("\n[1] CHECKING SERVICE INITIALIZATION...")
        print(f"    API Key set: {bool(genai_service.groq_api_key)}")
        print(f"    Primary model: {genai_service.primary_model}")
        print(f"    Fallback model: {genai_service.fallback_model}")
        
        print("\n[2] TESTING CLIENT PROPERTY (lazy load)...")
        client = genai_service.client
        print(f"    Client initialized: {client is not None}")
        
        if not client:
            print("\n[ERROR] Groq client not initialized!")
            return False
        
        print("\n[3] TESTING GENERATE_RESPONSE...")
        request = GenAIRequest(
            prompt="Hello, respond with 'GenAI service is operational!'",
            prompt_type=PromptType.CHATBOT
        )
        
        response = await genai_service.generate_response(request)
        
        print(f"    Model used: {response.model}")
        print(f"    Tokens: {response.tokens_used}")
        print(f"    Response time: {response.response_time:.2f}s")
        print(f"    Cached: {response.cached}")
        print(f"    Content: {response.content[:150]}...")
        
        # Check if it's a fallback response
        if response.model == "fallback-local":
            print("\n[WARNING] Response is from FALLBACK (offline mode)!")
            return False
        else:
            print("\n[SUCCESS] GenAI service is working correctly!")
            return True
            
    except Exception as e:
        print(f"\n[ERROR] GenAI service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test 1: Direct Groq API
    groq_ok = test_groq_connectivity()
    
    # Test 2: GenAI Service
    service_ok = asyncio.run(test_genai_service())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Groq API Direct: {'OK' if groq_ok else 'FAILED'}")
    print(f"GenAI Service: {'OK' if service_ok else 'FAILED'}")
    
    if groq_ok and service_ok:
        print("\n[ALL TESTS PASSED] GenAI integration is working!")
    else:
        print("\n[TESTS FAILED] Check the errors above for details.")
