#!/usr/bin/env python3
"""
Test script for the MCP Architecture.
This script tests the various components of the MCP architecture.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any


async def test_registry():
    """Test the registry service."""
    print("\n=== Testing Registry Service ===")
    
    async with httpx.AsyncClient() as client:
        # Get all services
        response = await client.get("http://localhost:8000/registry/services")
        if response.status_code == 200:
            services = response.json()
            print(f"Found {len(services)} registered services:")
            for service in services:
                print(f"  - {service.get('name')} ({service.get('type')})")
        else:
            print(f"Failed to get services: {response.text}")
            return False
    
    return True


async def test_rest_api():
    """Test the REST API server."""
    print("\n=== Testing REST API Server ===")
    
    async with httpx.AsyncClient() as client:
        # Test text generation
        response = await client.post(
            "http://localhost:8001/api/generate",
            json={
                "prompt": "Hello, world!",
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Text generation successful:")
            print(f"  Text: {result.get('text')}")
            print(f"  Confidence: {result.get('confidence')}")
            print(f"  Model: {result.get('model_used')}")
        else:
            print(f"Failed to generate text: {response.text}")
            return False
        
        # Test status
        response = await client.get("http://localhost:8001/api/status")
        if response.status_code == 200:
            status = response.json()
            print("Status check successful:")
            print(f"  Status: {status.get('status')}")
            print(f"  Load: {status.get('load')}")
            print(f"  Uptime: {status.get('uptime')} seconds")
        else:
            print(f"Failed to get status: {response.text}")
            return False
    
    return True


async def test_graphql_api():
    """Test the GraphQL API server."""
    print("\n=== Testing GraphQL API Server ===")
    
    async with httpx.AsyncClient() as client:
        # Test text generation
        response = await client.post(
            "http://localhost:8002/graphql",
            json={
                "query": """
                query {
                    generateText(prompt: "Hello, GraphQL!", maxTokens: 100) {
                        text
                        confidence
                        modelUsed
                    }
                }
                """
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                print(f"GraphQL errors: {result['errors']}")
                return False
            
            data = result.get("data", {}).get("generateText", {})
            print("Text generation successful:")
            print(f"  Text: {data.get('text')}")
            print(f"  Confidence: {data.get('confidence')}")
            print(f"  Model: {data.get('modelUsed')}")
        else:
            print(f"Failed to generate text: {response.text}")
            return False
        
        # Test status
        response = await client.post(
            "http://localhost:8002/graphql",
            json={
                "query": """
                query {
                    getStatus {
                        status
                        load
                        uptime
                    }
                }
                """
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                print(f"GraphQL errors: {result['errors']}")
                return False
            
            status = result.get("data", {}).get("getStatus", {})
            print("Status check successful:")
            print(f"  Status: {status.get('status')}")
            print(f"  Load: {status.get('load')}")
            print(f"  Uptime: {status.get('uptime')} seconds")
        else:
            print(f"Failed to get status: {response.text}")
            return False
    
    return True


async def test_mcp_server_1():
    """Test MCP Server 1 (REST)."""
    print("\n=== Testing MCP Server 1 (REST) ===")
    
    async with httpx.AsyncClient() as client:
        # Test MCP message
        response = await client.post(
            "http://localhost:8003/mcp/message",
            json={
                "message_id": "test-message",
                "source_id": "test-client",
                "target_id": "mcp-server-1",
                "content": {
                    "action": "generate_text",
                    "prompt": "Hello from MCP test!",
                    "max_tokens": 100
                },
                "timestamp": "2023-04-06T12:00:00Z"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("MCP message successful:")
            print(f"  Message ID: {result.get('message_id')}")
            response_data = result.get("response", {})
            print(f"  Text: {response_data.get('text')}")
            print(f"  Confidence: {response_data.get('confidence')}")
            print(f"  Model: {response_data.get('model_used')}")
        else:
            print(f"Failed to send MCP message: {response.text}")
            return False
        
        # Test status
        response = await client.get("http://localhost:8003/mcp/status")
        if response.status_code == 200:
            status = response.json()
            print("Status check successful:")
            print(f"  Status: {status.get('status')}")
            print(f"  Load: {status.get('load')}")
            print(f"  Uptime: {status.get('uptime')} seconds")
            print(f"  Connected services: {status.get('connected_services')}")
        else:
            print(f"Failed to get status: {response.text}")
            return False
    
    return True


async def test_mcp_server_2():
    """Test MCP Server 2 (GraphQL)."""
    print("\n=== Testing MCP Server 2 (GraphQL) ===")
    
    async with httpx.AsyncClient() as client:
        # Test MCP message
        response = await client.post(
            "http://localhost:8004/mcp/message",
            json={
                "message_id": "test-message",
                "source_id": "test-client",
                "target_id": "mcp-server-2",
                "content": {
                    "action": "generate_text",
                    "prompt": "Hello from MCP test to GraphQL!",
                    "max_tokens": 100
                },
                "timestamp": "2023-04-06T12:00:00Z"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("MCP message successful:")
            print(f"  Message ID: {result.get('message_id')}")
            response_data = result.get("response", {})
            print(f"  Text: {response_data.get('text')}")
            print(f"  Confidence: {response_data.get('confidence')}")
            print(f"  Model: {response_data.get('model_used')}")
        else:
            print(f"Failed to send MCP message: {response.text}")
            return False
        
        # Test status
        response = await client.get("http://localhost:8004/mcp/status")
        if response.status_code == 200:
            status = response.json()
            print("Status check successful:")
            print(f"  Status: {status.get('status')}")
            print(f"  Load: {status.get('load')}")
            print(f"  Uptime: {status.get('uptime')} seconds")
            print(f"  Connected services: {status.get('connected_services')}")
        else:
            print(f"Failed to get status: {response.text}")
            return False
    
    return True


async def test_mcp_client():
    """Test the MCP Client."""
    print("\n=== Testing MCP Client ===")
    print("MCP Client provides a web interface at http://localhost:8005")
    print("Please open this URL in your browser to interact with the client.")
    
    return True


async def main():
    """Run all tests."""
    print("=== MCP Architecture Test ===")
    print("This script tests the various components of the MCP architecture.")
    print("Make sure all services are running before executing this script.")
    
    # Wait for services to start up
    print("\nWaiting for services to start up...")
    await asyncio.sleep(5)
    
    # Run tests
    tests = [
        ("Registry Service", test_registry),
        ("REST API Server", test_rest_api),
        ("GraphQL API Server", test_graphql_api),
        ("MCP Server 1 (REST)", test_mcp_server_1),
        ("MCP Server 2 (GraphQL)", test_mcp_server_2),
        ("MCP Client", test_mcp_client)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            print(f"\nRunning test for {name}...")
            result = await test_func()
            results[name] = result
        except Exception as e:
            print(f"Error testing {name}: {str(e)}")
            results[name] = False
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        print(f"{name}: {status}")
    
    if all_passed:
        print("\nAll tests passed! The MCP architecture is working correctly.")
        return 0
    else:
        print("\nSome tests failed. Please check the output for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
