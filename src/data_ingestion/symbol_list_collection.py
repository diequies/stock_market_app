import os
import requests
import logging
from typing import Set, Optional
from tenacity import (retry, stop_after_attempt, wait_exponential,
                      retry_if_exception_type)

from requests import RequestException

from config.sentry_config import init_sentry
from data_ingestion.data_ingestion_constants import MAIN_FINANCIAL_MODELING_PREP_URL
from utils.data_models import TradedObject
from utils.db_helpers import get_all_traded_objects_from_db, \
    save_new_traded_objects_in_db
from utils.enums import TradedObjectType

init_sentry()

# Set up logger for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_RETRY = 3
MIN_RETRY_WAIT_TIME = 2
MAX_RETRY_WAIT_TIME = 10


class SymbolListCollector:
    """ Class to update the list of symbols if required """

    def __init__(self):
        self.current_symbol_list: Set[TradedObject] = get_all_traded_objects_from_db()
        self.new_symbol_list: Optional[Set[TradedObject]] = None

    def update_traded_objects(self) -> None:
        self._get_traded_objects_from_online()
        if self.new_symbol_list:
            objects_to_save = self.new_symbol_list.difference(self.current_symbol_list)
            if len(objects_to_save):
                save_new_traded_objects_in_db(traded_objects=objects_to_save)
            else:
                logger.warning(
                    "All traded objects are available in the database already")
        else:
            logger.warning(
                "No new traded objects found or an error occurred while fetching.")

    def _get_traded_objects_from_online(self) -> None:
        try:
            stock_set = self._get_traded_objects_by_type(
                trade_object_type=TradedObjectType.STOCK
            )

            etf_set = self._get_traded_objects_by_type(
                trade_object_type=TradedObjectType.ETF
            )

            self.new_symbol_list = stock_set.union(etf_set)
            logger.info(
                f"Fetched {len(self.new_symbol_list)} availble traded objects.")
        except Exception as e:
            logger.error(f"Error fetching traded objects: {e}")
            self.new_symbol_list = set()

    @staticmethod
    @retry(
        stop=stop_after_attempt(MAX_RETRY),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_TIME,
                              max=MAX_RETRY_WAIT_TIME),
        retry=retry_if_exception_type((RequestException, ValueError))
    )
    def _get_traded_objects_by_type(trade_object_type: TradedObjectType) -> (
            Set)[TradedObject]:

        api_token = os.environ.get('FINANCIAL_MODELING_PREP_TOKEN')
        if not api_token:
            logger.error("API token not found. Please set the "
                         "FINANCIAL_MODELING_PREP_TOKEN environment variable.")
            return set()

        endpoint_url = (f"{MAIN_FINANCIAL_MODELING_PREP_URL}/"
                        f"{trade_object_type.value['endpoint_name']}/list?"
                        f"apikey={api_token}")

        valid_traded_objects = set()
        invalid_entries = 0

        try:
            response = requests.get(endpoint_url, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            if not isinstance(response_data, list):
                raise ValueError(
                    "Unexpected response format, expected a list of objects.")

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

        except RequestException as req_err:
            logger.error(
                f"Request error while fetching {trade_object_type.name}: {req_err}")
            raise

        except ValueError as val_err:
            logger.error(f"Data format error for {trade_object_type.name}: {val_err}")
            raise

        except Exception as gen_err:
            logger.error(f"Unexpected error for {trade_object_type.name}: {gen_err}")

        return set()


if __name__ == '__main__':

    SymbolListCollector().update_traded_objects()
