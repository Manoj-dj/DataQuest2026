"""
Comprehensive backend test script.
Tests all endpoints to verify backend is working.
"""

import requests
import json
import sys

API_BASE = "http://localhost:8080"

def test_health():
    """Test health endpoints."""
    print("=" * 60)
    print("Testing Health Endpoints")
    print("=" * 60)
    
    try:
        # Test /health
        print("\n1. Testing GET /health...")
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Status: {data.get('status', 'N/A')}")
            print(f"   [OK] Active Events: {data.get('active_events', 'N/A')}")
            print(f"   [OK] Uptime: {data.get('uptime_seconds', 'N/A')}s")
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            return False
        
        # Test /api/health
        print("\n2. Testing GET /api/health...")
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status', 'N/A')}")
            print(f"   ✅ Events Count: {data.get('events_count', 'N/A')}")
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print("   [FAIL] Could not connect to backend server.")
        print("   Make sure the backend is running on http://localhost:8080")
        return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

def test_events():
    """Test events endpoints."""
    print("\n" + "=" * 60)
    print("Testing Events Endpoints")
    print("=" * 60)
    
    try:
        print("\n1. Testing GET /api/events/latest...")
        response = requests.get(f"{API_BASE}/api/events/latest?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Found {data.get('count', 0)} events")
            return True
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

def test_predictions():
    """Test predictions endpoint."""
    print("\n" + "=" * 60)
    print("Testing Predictions Endpoint")
    print("=" * 60)
    
    try:
        print("\n1. Testing GET /api/predictions...")
        response = requests.get(f"{API_BASE}/api/predictions", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Found {data.get('total', 0)} predictions")
            return True
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

def test_alerts():
    """Test alerts endpoints."""
    print("\n" + "=" * 60)
    print("Testing Alerts Endpoints")
    print("=" * 60)
    
    try:
        print("\n1. Testing GET /api/alerts/recent...")
        response = requests.get(f"{API_BASE}/api/alerts/recent?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Found {data.get('count', 0)} alerts")
            return True
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

def test_alert_settings():
    """Test alert settings endpoints."""
    print("\n" + "=" * 60)
    print("Testing Alert Settings Endpoints")
    print("=" * 60)
    
    try:
        print("\n1. Testing GET /api/alert-settings/citizen...")
        response = requests.get(f"{API_BASE}/api/alert-settings/citizen", timeout=10)
        if response.status_code == 200:
            data = response.json()
            settings = data.get('settings', {})
            print(f"   [OK] Min Severity: {settings.get('min_severity', 'N/A')}")
            print(f"   [OK] Channels: {settings.get('channels', [])}")
            return True
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

def test_simulate():
    """Test simulate endpoint."""
    print("\n" + "=" * 60)
    print("Testing Scenario Simulator Endpoint")
    print("=" * 60)
    
    try:
        print("\n1. Testing POST /api/simulate...")
        test_data = {
            "hazard_type": "earthquake",
            "magnitude": 7.2,
            "location": "San Francisco, CA",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "population_density": 2000,
            "infrastructure_score": 8.0
        }
        
        response = requests.post(
            f"{API_BASE}/api/simulate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Predicted Risk Score: {data.get('predicted_risk_score', 'N/A')}/10")
            print(f"   [OK] Predicted Impacts: {len(data.get('predicted_impacts', []))} items")
            return True
        else:
            print(f"   [FAIL] Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DisasterLens AI - Backend Test Suite")
    print("=" * 60)
    print("\nMake sure the backend is running on http://localhost:8080")
    print("=" * 60)
    
    results = []
    results.append(("Health Endpoints", test_health()))
    results.append(("Events Endpoint", test_events()))
    results.append(("Predictions Endpoint", test_predictions()))
    results.append(("Alerts Endpoint", test_alerts()))
    results.append(("Alert Settings Endpoint", test_alert_settings()))
    results.append(("Simulate Endpoint", test_simulate()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name:.<40} {status}")
    
    all_passed = all(r[1] for r in results)
    passed_count = sum(1 for r in results if r[1])
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! Backend is working correctly.")
    else:
        print(f"[WARNING] {passed_count}/{len(results)} tests passed.")
        print("Some endpoints may not be working. Check the errors above.")
    print("=" * 60 + "\n")
