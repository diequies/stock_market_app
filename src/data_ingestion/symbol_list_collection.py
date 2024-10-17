import os
import requests
import logging
from typing import Set, Optional, List
from tenacity import (retry, stop_after_attempt, wait_exponential,
                      retry_if_exception_type)

from requests import RequestException

from config.sentry_config import init_sentry
from data_ingestion.data_ingestion_constants import MAIN_FINANCIAL_MODELING_PREP_URL
from utils.data_models import TradedObject
from utils.db_helpers import get_all_traded_objects_from_db, \
    save_new_traded_objects_in_db
from utils.enums import TradedObjectType

# Set up logger for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SymbolListCollector:
    """ Class to update the list of symbols if required """

    MAX_RETRY = 3
    MIN_RETRY_WAIT_TIME = 2
    MAX_RETRY_WAIT_TIME = 10

    def __init__(self):
        self.current_symbol_list: Set[TradedObject] = get_all_traded_objects_from_db()
        self.new_symbol_list: Set[TradedObject] = None

    def update_traded_objects(self) -> None:
        try:
            self._get_traded_objects_from_online()
            self._save_new_traded_objects()
        except Exception as e:
            logger.error(f"Error updating traded objects: {e}")

    def _save_new_traded_objects(self) -> None:
        if not self.new_symbol_list:
            logger.warning(
                "No new traded objects found or an error occurred while fetching.")
            return
        objects_to_save = self.new_symbol_list.difference(self.current_symbol_list)
        if len(objects_to_save):
            save_new_traded_objects_in_db(traded_objects=objects_to_save)
            logger.info(f"Saved {len(objects_to_save)} new traded objects to the "
                        f"database.")
        else:
            logger.warning("All traded objects are available in the database already")

    def _get_traded_objects_from_online(self) -> None:
        stock_set = self._get_traded_objects_by_type(
            trade_object_type=TradedObjectType.STOCK
        )

        etf_set = self._get_traded_objects_by_type(
            trade_object_type=TradedObjectType.ETF
        )

        self.new_symbol_list = stock_set.union(etf_set)
        logger.info(
            f"Fetched {len(self.new_symbol_list)} availble traded objects.")

    @staticmethod
    def _fetch_data_from_api(url: str) -> list:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Unexpected response format; expected a list.")
            return data
        except RequestException as req_err:
            logger.error(f"Request error: {req_err}")
            raise
        except ValueError as val_err:
            logger.error(f"Data format error: {val_err}")
            raise

    @staticmethod
    def _process_traded_objects(
            response_data: List,
            trade_object_type: TradedObjectType
    ) -> Set[TradedObject]:

        valid_traded_objects = set()
        invalid_entries = 0

        for data in response_data:
            try:
                traded_object = TradedObject(
                    name=data['name'],
                    symbol=data['symbol'],
                    exchange=data['exchange'],
                    exchange_short_name=data['exchangeShortName'],
                    object_type=TradedObjectType.get_traded_object_type_from_name(
                        data['type'])
                )
                valid_traded_objects.add(traded_object)

            except KeyError as e:
                logger.warning(f"Missing key {e} in entry: {data}")
                invalid_entries += 1
            except Exception as gen_err:
                logger.warning(f"Error processing entry {data}: {gen_err}")
                invalid_entries += 1

        if invalid_entries > 0:
            logger.warning(f"Skipped {invalid_entries} invalid "
                           f"{trade_object_type.name.lower()} objects.")

        logger.info(f"Fetched {len(valid_traded_objects)} "
                    f"{trade_object_type.name.lower()} objects.")

        return valid_traded_objects

    @retry(
        stop=stop_after_attempt(MAX_RETRY),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_TIME,
                              max=MAX_RETRY_WAIT_TIME),
        retry=retry_if_exception_type((RequestException, ValueError))
    )
    def _get_traded_objects_by_type(self, trade_object_type: TradedObjectType) -> (
            Set)[TradedObject]:

        api_token = os.environ.get('FINANCIAL_MODELING_PREP_TOKEN')
        if not api_token:
            raise EnvironmentError("API token not found.")

        endpoint_url = (f"{MAIN_FINANCIAL_MODELING_PREP_URL}/"
                        f"{trade_object_type.value['endpoint_name']}/list?"
                        f"apikey={api_token}")

        response_data = self._fetch_data_from_api(endpoint_url)
        return self._process_traded_objects(response_data=response_data,
                                            trade_object_type=trade_object_type)


def main():
    init_sentry()
    SymbolListCollector().update_traded_objects()


if __name__ == '__main__':
    main()
