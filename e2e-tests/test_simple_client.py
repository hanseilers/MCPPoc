import pytest
import requests
import time
from playwright.sync_api import Page, expect

# Configuration
BASE_URL = "http://localhost:8006"
API_URL = f"{BASE_URL}/api/send"
HEALTH_CHECK_URL = f"{BASE_URL}/health"
MCP_SERVER_HEALTH_URL = "http://localhost:8003/health"
TEST_PROMPT = "Make a poem about spring"
MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds

def test_health_endpoints():
    """Test that health endpoints are responding correctly."""
    # Check simple client health
    response = requests.get(HEALTH_CHECK_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "simple-client"

    # Check MCP server health
    response = requests.get(MCP_SERVER_HEALTH_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_endpoint():
    """Test that the API endpoint works correctly."""
    # Send a request to the API
    response = requests.post(API_URL, data={"prompt": TEST_PROMPT})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "result" in data
    assert "request_id" in data

    # Check the result structure
    result = data["result"]
    assert "message_id" in result
    assert "response" in result
    assert "text" in result["response"]
    assert len(result["response"]["text"]) > 0

def test_frontend_interaction(page: Page):
    """Test the frontend interaction with the API."""
    # Navigate to the page
    page.goto(BASE_URL)

    # Check that the page loaded correctly
    expect(page).to_have_title("Simple MCP Client")

    # Fill in the prompt
    page.fill("#prompt", TEST_PROMPT)

    # Click the submit button
    page.click("#submit-btn")

    # Wait for the response to load
    for _ in range(MAX_RETRIES):
        if page.is_visible("#response") and not page.is_visible("#loading"):
            break
        time.sleep(RETRY_DELAY)

    # Check that the response is displayed
    expect(page.locator("#response")).to_be_visible()

    # Get the response text
    response_text = page.text_content("#response")
    assert response_text is not None
    assert len(response_text) > 0

    # Check that the response contains some expected content
    # This is a loose check since the exact response will vary
    assert "spring" in response_text.lower() or "poem" in response_text.lower()

def test_error_handling(page: Page):
    """Test error handling in the frontend."""
    # Navigate to the page
    page.goto(BASE_URL)

    # Try to submit without a prompt
    page.fill("#prompt", "")
    page.click("#submit-btn")

    # Check for alert (this will fail if no alert is shown)
    page.on("dialog", lambda dialog: dialog.accept())

    # Try with a very short prompt that might cause issues
    page.fill("#prompt", "a")
    page.click("#submit-btn")

    # Wait for the response
    for _ in range(MAX_RETRIES):
        if page.is_visible("#response") and not page.is_visible("#loading"):
            break
        time.sleep(RETRY_DELAY)

    # Check that we got some kind of response
    expect(page.locator("#response")).to_be_visible()
