import os
from unittest.mock import patch

import pytest
import requests
from pymysql.constants.ER import WRONG_VALUE_FOR_TYPE
from tenacity import RetryError

from data_ingestion.symbol_list_collection import SymbolListCollector
from utils.data_models import TradedObject
from utils.enums import TradedObjectType

MOCK_API_TOKEN = "mocked_token"
MOCK_MAIN_FINANCIAL_MODELING_PREP_URL = "https://mocked_api_url"

NUMBER_OF_RETRY_TIMES = 3

# Mock data for API response
MOCK_API_RESPONSE = [
    {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ",
     "exchangeShortName": "NASDAQ", "type": "stock"},
    {"symbol": "GOOG", "name": "Alphabet Inc.", "exchange": "NASDAQ",
     "exchangeShortName": "NASDAQ", "type": "stock"},
]

MOCK_API_RESPONSE_WRONG = [
    {"symbol": "INVALID", "name": "Invalid Object"}
]


# Helper to mock a traded object
def mock_traded_object(symbol, name="Test Object", exchange="NYSE",
                       object_type=TradedObjectType.STOCK):
    return TradedObject(
        name=name,
        symbol=symbol,
        exchange=exchange,
        exchange_short_name=exchange,
        object_type=object_type
    )


@pytest.fixture
def symbol_collector():
    """Fixture to initialize SymbolListCollector."""
    with patch('data_ingestion.symbol_list_collection'
               '.get_all_traded_objects_from_db',
               return_value=set()):
        yield SymbolListCollector()


@patch('requests.get')
@patch.dict(os.environ, {"FINANCIAL_MODELING_PREP_TOKEN": MOCK_API_TOKEN})
@patch('data_ingestion.symbol_list_collection.save_new_traded_objects_in_db')
def test_update_traded_objects(mock_save_db, mock_requests, symbol_collector):
    """Test update_traded_objects fetches and saves new symbols."""

    # Mock API response
    mock_requests.return_value.json.return_value = MOCK_API_RESPONSE
    mock_requests.return_value.status_code = 200

    # Execute the method
    symbol_collector.update_traded_objects()

    # Ensure requests were made and data was saved
    assert mock_requests.call_count == 2  # One for STOCK, one for ETF
    assert mock_save_db.called


@patch('requests.get')
@patch.dict(os.environ, {"FINANCIAL_MODELING_PREP_TOKEN": MOCK_API_TOKEN})
@patch('data_ingestion.symbol_list_collection.save_new_traded_objects_in_db')
def test_api_fetch_failures_retries(mock_save_db, mock_requests, symbol_collector):
    """Test retry behavior on API failure."""

    # Simulate request failure
    mock_requests.side_effect = requests.RequestException("API request failed")

    symbol_collector.update_traded_objects()

    assert mock_requests.call_count == NUMBER_OF_RETRY_TIMES
    assert not mock_save_db.called


@patch('data_ingestion.symbol_list_collection.get_all_traded_objects_from_db')
def test_no_new_traded_objects(symbol_collector):
    """Test behavior when no new traded objects are fetched."""

    symbol_collector.current_symbol_list = {
        mock_traded_object(symbol="AAPL")
    }

    symbol_collector.new_symbol_list = {
        mock_traded_object(symbol="AAPL")
    }

    with patch('data_ingestion.symbol_list_collection'
               '.save_new_traded_objects_in_db') as mock_save_db:
        symbol_collector._save_new_traded_objects()
        mock_save_db.assert_not_called()


@patch.dict(os.environ, {"FINANCIAL_MODELING_PREP_TOKEN": ""})
def test_missing_api_token(symbol_collector):
    """Test that missing API token raises EnvironmentError."""

    with pytest.raises(EnvironmentError, match="API token not found"):
        symbol_collector._get_traded_objects_by_type(TradedObjectType.STOCK)


def test_new_traded_objects(symbol_collector):
    """Test behavior when new traded objects are fetched and saved."""

    existing_object = mock_traded_object(symbol="AAPL")
    symbol_collector.current_symbol_list = {existing_object}

    new_object = mock_traded_object(symbol="TSLA")
    symbol_collector.new_symbol_list = {existing_object, new_object}

    with patch('data_ingestion.symbol_list_collection'
               '.save_new_traded_objects_in_db') as mock_save_db:
        symbol_collector._save_new_traded_objects()

        # Assert that the new object was saved
        mock_save_db.assert_called_once_with(traded_objects={new_object})


@patch('requests.get')
@patch.dict(os.environ, {"FINANCIAL_MODELING_PREP_TOKEN": MOCK_API_TOKEN})
def test_handle_invalid_data(mock_requests, symbol_collector):
    """Test behavior when invalid data is received from the API."""

    mock_requests.return_value.json.return_value = WRONG_VALUE_FOR_TYPE
    mock_requests.return_value.status_code = 200

    with pytest.raises(RetryError):
        symbol_collector._get_traded_objects_from_online()
