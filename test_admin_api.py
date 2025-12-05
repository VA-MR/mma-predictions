#!/usr/bin/env python3
"""Test script to verify admin API endpoints work correctly."""

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_api_endpoints():
    """Test all admin API endpoints."""
    
    print("=" * 60)
    print("TESTING ADMIN API ENDPOINTS")
    print("=" * 60)
    
    # Test organizations
    print("\n1. Testing /api/admin/organizations...")
    response = client.get("/api/admin/organizations")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Organizations found: {len(data)}")
        if data:
            print(f"   First org: {data[0]}")
    else:
        print(f"   Error: {response.text}")
    
    # Test fighters
    print("\n2. Testing /api/admin/fighters...")
    response = client.get("/api/admin/fighters?limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Fighters found: {len(data)}")
        if data:
            print(f"   First fighter: {data[0]['name']} ({data[0]['record']})")
    else:
        print(f"   Error: {response.text}")
    
    # Test events
    print("\n3. Testing /api/admin/events...")
    response = client.get("/api/admin/events?limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Events found: {len(data)}")
        if data:
            print(f"   First event: {data[0]['name']} ({data[0]['organization']})")
    else:
        print(f"   Error: {response.text}")
    
    # Test fights
    print("\n4. Testing /api/admin/fights...")
    response = client.get("/api/admin/fights?limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Fights found: {len(data)}")
        if data:
            fight = data[0]
            f1 = fight.get('fighter1', {}).get('name', 'TBA') if fight.get('fighter1') else 'TBA'
            f2 = fight.get('fighter2', {}).get('name', 'TBA') if fight.get('fighter2') else 'TBA'
            print(f"   First fight: {f1} vs {f2}")
    else:
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_api_endpoints()

