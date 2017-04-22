import json
from collections import Counter

class Operators:
    def __init__(self, operators_data_filename, sessions_data_filename):
        self.operators_data_filename = operators_data_filename
        self.sessions_data_filename = sessions_data_filename
        self.refresh()

    def refresh(self):
        with open(self.operators_data_filename, encoding='utf8') as f:
            operators = json.loads(f.read())
        with open(self.sessions_data_filename, encoding='utf8') as f:
            sessions = json.loads(f.read())
        self.operators = {int(k):v for k,v in operators.items()}
        self.sessions = {int(k):int(v) for k,v in sessions.items()}

    def _rewrite_operators(self):
        with open(self.operators_data_filename, 'w', encoding='utf8') as outfile:
            outfile.write(json.dumps(self.operators, ensure_ascii=False, indent=2))

    def _rewrite_sessions(self):
        with open(self.sessions_data_filename, 'w', encoding='utf8') as outfile:
            outfile.write(json.dumps(self.sessions, ensure_ascii=False, indent=2))
        self.refresh()

    @property
    def operator_chat_ids(self):
        return [k for k in self.operators]

    @property
    def available_operator_chat_ids(self):
        return [k for k, v in self.operators.items() if v]

    @property
    def clients_of_operators(self):
        clients_of_operators = {}
        for op in self.operator_chat_ids:
            clients_of_operators[op] = [c for c, o in self.sessions.items() if o==op]
        return clients_of_operators

    @property
    def sessions_per_available_operator(self):
        sessions_per_operator = {}
        for op in self.available_operator_chat_ids:
            if op not in self.sessions.values():
                sessions_per_operator[op] = 0
            else:
                sessions_per_operator[op] = len([s_op for s_op in self.sessions.values() if s_op == op])
        return sessions_per_operator

    @property
    def min_busy_available_operator(self):
        sessions_per_available_operator = self.sessions_per_available_operator
        if not sessions_per_available_operator:
            return None
        return min(sessions_per_available_operator, key = sessions_per_available_operator.get)

    def get_operator_chat_id(self, client_chat_id):
        changed_operator = False
        operator_chat_id = self.sessions.get(client_chat_id)
        if operator_chat_id:
            if operator_chat_id in self.available_operator_chat_ids:
                return operator_chat_id, changed_operator
            else:
                changed_operator = True
        new_operator = self.min_busy_available_operator
        if not new_operator:
            return None, changed_operator
        self.sessions[client_chat_id] = new_operator
        self._rewrite_sessions()
        return new_operator, changed_operator

    def is_operator(self, chat_id):
        return chat_id in self.operator_chat_ids

    def set_availability(self, chat_id, value):
        self.operators.update({chat_id:value})
        self._rewrite_operators()

    def get_availability(self, chat_id):
        return self.operators.get(chat_id)

    def close_session(self, chat_id):
        self.sessions.pop(chat_id)
        self._rewrite_sessions()

    def delete_operator(self, chat_id):
        self.operators.pop(chat_id)
        self._rewrite_operators()