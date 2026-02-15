#!/usr/bin/env python3
"""
Simple WebSocket test script to verify WebSocket functionality.
This script tests the WebSocket connection without needing a browser.
"""

import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to the test endpoint."""
    uri = "ws://localhost:8000/ws/test/"
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket successfully!")
            
            # Test 1: Send echo message
            print("\n--- Test 1: Echo Message ---")
            echo_message = {
                "type": "echo",
                "message": "Hello from Python test script!",
                "timestamp": "2026-02-13T07:00:00Z"
            }
            
            await websocket.send(json.dumps(echo_message))
            print(f"Sent: {echo_message}")
            
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test 2: Send ping message
            print("\n--- Test 2: Ping Message ---")
            ping_message = {
                "type": "ping",
                "message": "Testing ping/pong",
                "timestamp": "2026-02-13T07:00:01Z"
            }
            
            await websocket.send(json.dumps(ping_message))
            print(f"Sent: {ping_message}")
            
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test 3: Test authentication
            print("\n--- Test 3: Authentication Test ---")
            auth_message = {
                "type": "test_auth",
                "message": "Testing authentication",
                "timestamp": "2026-02-13T07:00:02Z"
            }
            
            await websocket.send(json.dumps(auth_message))
            print(f"Sent: {auth_message}")
            
            response = await websocket.recv()
            print(f"Received: {response}")
            
            print("\n✅ All WebSocket tests completed successfully!")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")
        print("Make sure the Django server is running with ASGI support (Daphne)")

if __name__ == "__main__":
    print("WebSocket Test Script")
    print("====================")
    print("This script tests WebSocket functionality without a browser.")
    print("Make sure the Django server is running on http://localhost:8001/")
    print()
    
    asyncio.run(test_websocket())