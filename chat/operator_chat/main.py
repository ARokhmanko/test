import json
import logging

from providers import Operators, Clients
from wrapper import TelegramWrapper

STATIC_FILENAME = 'workdata/static.json'

STATIC = json.loads(open(STATIC_FILENAME, encoding='utf8').read())
tg_token = json.loads(open(STATIC["credentials_filename"]).read())['tg_token']
logging.basicConfig(filename=STATIC["logs_filename"],
                    level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(message)s')

operator_router = Operators(operators_data_filename=STATIC["operators_data_filename"],
                            sessions_data_filename=STATIC["sessions_data_filename"])
clients = Clients(STATIC["authorized_clients_data_filename"], STATIC["all_clients_filename"])

tg = TelegramWrapper(tg_token=tg_token,
                     static_filename=STATIC_FILENAME,
                     operators=operator_router,
                     clients=clients)
tg.main()
