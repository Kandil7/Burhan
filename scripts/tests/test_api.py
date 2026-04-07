"""
Quick test script to verify Athar API is working.
Run this after starting the Docker services.
"""
import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        if response.status == 200:
            data = json.loads(response.read().decode())
            print(f"  ✓ Health: {data.get('status', 'unknown')}")
            print(f"  ✓ Version: {data.get('version', 'unknown')}")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_query():
    """Test query endpoint."""
    print("\nTesting /api/v1/query endpoint...")
    try:
        data = json.dumps({
            "query": "السلام عليكم",
            "language": "ar"
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{BASE_URL}/api/v1/query",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        if response.status == 200:
            result = json.loads(response.read().decode())
            print(f"  ✓ Query successful")
            print(f"  ✓ Intent: {result.get('intent', 'unknown')}")
            print(f"  ✓ Answer: {result.get('answer', '')[:100]}...")
            return True
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error: {e.code}")
        print(f"  ✗ Response: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("="*60)
    print("ATHAR API TEST")
    print("="*60 + "\n")
    
    health_ok = test_health()
    
    if health_ok:
        test_query()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("\n1. Open http://localhost:8000/docs for interactive API docs")
    print("2. Open http://localhost:3000 for chat interface (if frontend running)")
    print("3. Try these queries:")
    print("   - السلام عليكم")
    print("   - ما حكم صلاة الجمعة؟")
    print("   - كم عدد آيات سورة البقرة؟")
    print("\nTo stop services:")
    print("  docker compose -f docker/docker-compose.dev.yml down\n")

if __name__ == "__main__":
    main()
