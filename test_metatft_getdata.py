import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from metatft_getdata import MetaTFT

# test_metatft_getdata.py



@pytest.mark.asyncio
async def test_get_match_data_success(monkeypatch):
    # Arrange
    tft = MetaTFT()
    riot_id = "TestName#1234"
    region = "na"

    # Mock Playwright context and page
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_playwright = AsyncMock()
    mock_chromium = AsyncMock()
    mock_chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Mock page interactions
    mock_page.goto.return_value = None
    mock_page.wait_for_selector.return_value = AsyncMock()
    mock_page.query_selector_all.side_effect = [
        [AsyncMock(get_attribute=AsyncMock(return_value="match123"))],  # .PlayerGame
    ]
    # Patch get_match_details to return dummy match data
    dummy_match_data = {"match_id": "match123"}
    async def fake_get_match_details(page, match_id):
        return dummy_match_data
    tft.get_match_details = fake_get_match_details

    # Patch async_playwright context manager
    class DummyAsyncPlaywright:
        async def __aenter__(self):
            self.chromium = mock_chromium
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("metatft_getdata.async_playwright", lambda: DummyAsyncPlaywright())

    # Act
    result = await tft.get_match_data(riot_id, region)

    # Assert
    assert isinstance(result, list)
    assert result[0]["match_id"] == "match123"

@pytest.mark.asyncio
async def test_get_match_data_goto_exception(monkeypatch):
    tft = MetaTFT()
    riot_id = "TestName#1234"
    region = "na"

    # Mock Playwright context and page
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_playwright = AsyncMock()
    mock_chromium = AsyncMock()
    mock_chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Simulate page.goto raising an exception
    mock_page.goto.side_effect = Exception("Network error")

    class DummyAsyncPlaywright:
        async def __aenter__(self):
            self.chromium = mock_chromium
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("metatft_getdata.async_playwright", lambda: DummyAsyncPlaywright())

    # Act
    result = await tft.get_match_data(riot_id, region)

    # Assert
    assert result is None