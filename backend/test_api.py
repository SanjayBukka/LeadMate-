"""
Test script to verify Gemini API and backend endpoints
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_service():
    """Test Gemini service initialization"""
    print("\n" + "="*60)
    print("TESTING GEMINI SERVICE")
    print("="*60)
    
    try:
        from services.gemini_service import gemini_service
        
        print(f"\n[OK] Gemini Service imported successfully")
        print(f"   LLM Type: {gemini_service.llm_type}")
        print(f"   Model: {gemini_service.model}")
        print(f"   CrewAI Model: {gemini_service.crewai_model}")
        
        # Test getting LLM
        try:
            llm = gemini_service.get_llm()
            print(f"   LLM Instance: {type(llm).__name__ if hasattr(llm, '__class__') else llm}")
        except Exception as e:
            print(f"   [WARNING] Error getting LLM: {e}")
        
        # Test extract_document_content
        try:
            test_text = "This is a test document. It contains important information about a project."
            result = gemini_service.extract_document_content(test_text, "test.txt")
            print(f"\n[OK] Document extraction test passed")
            print(f"   Result length: {len(result)} characters")
            print(f"   Preview: {result[:100]}...")
        except Exception as e:
            print(f"   [ERROR] Document extraction test failed: {e}")
        
        # Test chat interface
        try:
            response = gemini_service.chat(
                model=gemini_service.model,
                messages=[{'role': 'user', 'content': 'Say hello in one word'}]
            )
            if response and 'message' in response:
                print(f"\n[OK] Chat interface test passed")
                print(f"   Response: {response['message'].get('content', 'No content')[:100]}")
            else:
                print(f"   [WARNING] Chat response format unexpected: {response}")
        except Exception as e:
            print(f"   [ERROR] Chat interface test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Gemini Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_health():
    """Test if backend server is running"""
    print("\n" + "="*60)
    print("TESTING BACKEND SERVER")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"\n[OK] Backend server is running")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Backend server is NOT running")
        print(f"   Please start the backend with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"\n[WARNING] Error connecting to backend: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("/", "Root endpoint"),
        ("/api", "API root"),
        ("/docs", "API documentation"),
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "[OK]" if response.status_code == 200 else "[WARNING]"
            print(f"\n{status} {name}: {endpoint}")
            print(f"   Status: {response.status_code}")
            results.append(True)
        except Exception as e:
            print(f"\n[ERROR] {name}: {endpoint}")
            print(f"   Error: {e}")
            results.append(False)
    
    return all(results)

def test_agent_initialization():
    """Test if agents can be initialized"""
    print("\n" + "="*60)
    print("TESTING AGENT INITIALIZATION")
    print("="*60)
    
    test_company_id = "test_company_123"
    test_lead_id = "test_lead_456"
    
    agents_to_test = [
        ("DocumentAgent", "agents.document_agent", "DocumentAgent"),
        ("StackAgent", "agents.stack_agent", "StackAgent"),
        ("TaskAgent", "agents.task_agent", "TaskAgent"),
    ]
    
    results = []
    for agent_name, module_path, class_name in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            AgentClass = getattr(module, class_name)
            agent = AgentClass(test_company_id, test_lead_id)
            
            if agent and agent.llm:
                llm_info = type(agent.llm).__name__ if hasattr(agent.llm, '__class__') else str(agent.llm)
                print(f"\n[OK] {agent_name} initialized successfully")
                print(f"   LLM: {llm_info}")
                results.append(True)
            else:
                print(f"\n[WARNING] {agent_name} initialized but LLM is None")
                results.append(False)
                
        except Exception as e:
            print(f"\n[ERROR] {agent_name} initialization failed: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LEADMATE API TEST SUITE")
    print("="*60)
    
    results = {
        "Gemini Service": test_gemini_service(),
        "Backend Server": test_backend_health(),
        "API Endpoints": test_backend_health() and test_api_endpoints(),
        "Agent Initialization": test_agent_initialization(),
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
        print("\nNext steps:")
        if not results["Backend Server"]:
            print("   1. Start backend: cd backend && python main.py")
        if not results["Gemini Service"]:
            print("   2. Check Gemini API keys in config.py")
            print("   3. Install: pip install google-generativeai")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

