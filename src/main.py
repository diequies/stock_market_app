from data_ingestion.symbol_list_collection import SymbolListCollector
from utils.db_helpers import get_mysql_connection

if __name__ == '__main__':

    SymbolListCollector().update_traded_objects()

    i=1
