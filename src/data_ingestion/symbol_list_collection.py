import os
import requests
from typing import Set, Optional

from data_ingestion.data_ingestion_constants import MAIN_FINANCIAL_MODELING_PREP_URL
from utils.data_models import TradedObject
from utils.db_helpers import get_all_traded_objects_from_db, \
    save_new_traded_objects_in_db
from utils.enums import TradedObjectType


class SymbolListCollector:
    """ Class to update the list of symbols if required """

    def __init__(self):
        self.current_symbol_list: Set[TradedObject] = get_all_traded_objects_from_db()
        self.new_symbol_list: Optional[Set[TradedObject]] = None

    def update_traded_objects(self) -> None:
        self._get_traded_objects_from_online()
        objects_to_save = self.new_symbol_list.difference(self.new_symbol_list)
        save_new_traded_objects_in_db(traded_objects=objects_to_save)

    def _get_traded_objects_from_online(self) -> None:

        stock_set = self._get_traded_objects_by_type(
            trade_object_type=TradedObjectType.STOCK
        )

        etf_set = self._get_traded_objects_by_type(
            trade_object_type=TradedObjectType.ETF
        )

        self.new_symbol_list = stock_set.union(etf_set)

    @staticmethod
    def _get_traded_objects_by_type(trade_object_type: TradedObjectType) -> (
            Set)[TradedObject]:

        endpoint_url = (f"{MAIN_FINANCIAL_MODELING_PREP_URL}/"
                        f"{trade_object_type.value['endpoint_name']}/list?"
                        f"apikey={os.environ.get('FINANCIAL_MODELING_PREP_TOKEN')}")

        response = requests.get(endpoint_url).json()

        return {
            TradedObject(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                exchange_short_name=data['exchangeShortName'],
                object_type=TradedObjectType.get_traded_object_type_from_name(
                    data['type'])
            ) for data in response
        }


