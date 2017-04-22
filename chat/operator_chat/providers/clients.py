import json
import pandas as pd

class Clients:
    def __init__(self, authorized_userdata_filename, all_clients_data_filename):
        self._authorized_userdata_filename = authorized_userdata_filename
        self._all_clients_data_filename = all_clients_data_filename
        self.refresh()

    def _refresh_authorized(self):
        authorized_clients = json.loads(open(self._authorized_userdata_filename, encoding='utf8').read())
        self.authorized_clients = {int(k):v for k,v in authorized_clients.items()}

    def _refresh_all(self):
        self.all_clients_data = pd.read_excel(self._all_clients_data_filename)

    def refresh(self):
        self._refresh_authorized()
        self._refresh_all()

    def _rewrite_file(self):
        with open(self._authorized_userdata_filename, 'w', encoding='utf8') as outfile:
            outfile.write(json.dumps(self.authorized_clients, ensure_ascii=False, indent=2))

    @property
    def authorized_clients_chat_ids(self):
        return [k for k in self.authorized_clients]

    def is_client(self, phone):
        return int(phone) in list(self.all_clients_data.phone)

    def is_authorized_client(self, chat_id):
        return chat_id in self.authorized_clients_chat_ids

    def authorize_client(self, contact, additional_fields=None):
        self.authorized_clients[contact["user_id"]] = {k:v for k,v in contact.items() if k!="user_id"}
        if additional_fields:
            self.authorized_clients[contact["user_id"]].update(additional_fields)
        self._rewrite_file()

    def get_client(self, chat_id):
        return self.authorized_clients.get(chat_id)

    def get_field(self, chat_id, field):
        client = self.get_client(chat_id)
        return client.get(field) if client else None

    def set_client(self, chat_id, client):
        self.authorized_clients[chat_id] = client
        self._rewrite_file()

    def set_field(self, chat_id, field, value):
        self.authorized_clients[chat_id][field] = value
        self._rewrite_file()

if __name__ == '__main__':
    clients = Clients("../userdata/clients_authorized_data.json", "../userdata/all_clients.xlsx")
    print(clients.all_clients_data)
