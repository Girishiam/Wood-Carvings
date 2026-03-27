#!/usr/bin/env python3
"""
Health check script for monitoring application status.
Returns exit code 0 if healthy, 1 if unhealthy.
"""
import sys
import os

try:
    import requests

    port = os.getenv("PORT", "8000")
    url = f"http://localhost:{port}/health"

    response = requests.get(url, timeout=5)

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "active":
            print("✓ Service is healthy")
            sys.exit(0)
        else:
            print("✗ Service returned unexpected status")
            sys.exit(1)
    else:
        print(f"✗ Service returned status code {response.status_code}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Health check failed: {e}")
    sys.exit(1)
