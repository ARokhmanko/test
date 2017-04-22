# coding: utf-8
import json
import logging

from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, CallbackQueryHandler
from utils import object_to_str
from providers import LogsParser

class FilterNotContact(BaseFilter):
    def filter(self, message):
        return message.contact is None


filter_not_contact = FilterNotContact()

class TelegramWrapper(object):
    CHATBOT_MODE = "chatbot"
    OPERATOR_MODE = "operator"
    CHATBOT_ENTERING_CITIES_MODE = "settings_cities_entering"

    def __init__(self, tg_token, static_filename, operators, clients):
        self.TG_TOKEN = tg_token
        self.operators = operators
        self.clients = clients
        self.static_filename = static_filename
        self.refresh_static()

    def refresh_static(self):
        self.static = json.loads(open(self.static_filename, encoding='utf8').read())
        self.admins = self.static["admin_chat_ids"]
        self._REQUEST_CONTACT_MARKUP = ReplyKeyboardMarkup([
            [
                KeyboardButton(text=self.static["request_contact_button_text"], request_contact=True)
            ]
        ], resize_keyboard=True)
        self._OPERATOR_MARKUP = {i: ReplyKeyboardMarkup([
                [
                    KeyboardButton(text=self.static["operator_button_on_off"][str(i)])
                ],
                [
                    KeyboardButton(text=self.static["operator_button_history"])
                ]
            ], resize_keyboard=True)
            for i in {0,1}}
        self._AUTHORIZED_MARKUP = ReplyKeyboardMarkup([
            [
                KeyboardButton(text=self.static["button_info_text"])
            ],
            [
                KeyboardButton(text=self.static["open_chat_button_text"])
            ],
            [
                KeyboardButton(text=self.static["button_settings_text"])
            ]
        ], resize_keyboard=True)
        self._CLOSE_CHAT_MARKUP = ReplyKeyboardMarkup([[self.static["close_chat_button_text"]]], resize_keyboard=True)
        self.logs_parser = LogsParser(self.static["logs_filename"])

    def _rewrite_static(self):
        with open(self.static_filename, 'w', encoding='utf8') as outfile:
            outfile.write(json.dumps(self.static, ensure_ascii=False, indent=2))

# help funcs
    def update_to_str(self, update):
        msg = {k:v for k,v in update.message.__dict__.items() if k in self.static["interesting_fields_to_log"] and v}
        return msg.get("text") or object_to_str(msg)

    def log_msg(self, update=None, chat_id=None, text=None, sender=None, orignal_chat_id=None, mode=None):
        if mode == TelegramWrapper.OPERATOR_MODE and update:
            try:
                chat_id = chat_id or update.message.reply_to_message.forward_from.id
            except:
                pass
            sender = sender or  "operator"
        logging.info('%d - %s - %d: %s',
                     chat_id or update.message.chat_id,
                     sender or "client",
                     orignal_chat_id or (update.message.chat_id if update and update.message else chat_id),
                     text or self.update_to_str(update))

    def error(self, bot, update, error):
        logging.debug('Update "%s" caused error "%s"'.format(update, error))

    def get_info_about_user(self, chat_id):
        client = self.clients.get_client(chat_id)
        resp = dict(is_admin=chat_id in self.admins,
                    is_operator=self.operators.is_operator(chat_id),
                    is_authorized_client=self.clients.is_authorized_client(chat_id),
                    state=client.get("state") if client else None)
        resp["is_known"] = resp["is_authorized_client"] or resp["is_operator"] or resp["is_admin"]
        return resp

    def get_markup(self, chat_id):
        user_info = self.get_info_about_user(chat_id)
        if user_info["state"] == TelegramWrapper.OPERATOR_MODE and user_info["is_authorized_client"]:
            return self._CLOSE_CHAT_MARKUP
        if not user_info["is_known"]:
            return self._REQUEST_CONTACT_MARKUP
        if user_info["is_authorized_client"]:
            return self._AUTHORIZED_MARKUP
        if user_info["is_operator"]:
            return self._OPERATOR_MARKUP[self.operators.get_availability(chat_id)]
        return ReplyKeyboardRemove()

    def msg_with_buttons(self, bot, update, text, options, chat_id=None, message_id=None):
        chat_id = chat_id or update.message.chat_id
        text = text[:self.static["max_msg_size"]]
        if len(options) > 0:
            buttons = [InlineKeyboardButton(o[0], callback_data=o[1][:30]) for o in options]
            keyboard = [[b] for b in buttons]  # customize form
            reply_markup = InlineKeyboardMarkup(keyboard)
            if not message_id:
                bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)
            else:
                bot.editMessageText(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
        else:
            if not message_id:
                bot.sendMessage(chat_id=chat_id, text=text)
            else:
                bot.editMessageText(chat_id=chat_id, message_id=message_id, text=text)

# commands
    def slash_start(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        user_info = self.get_info_about_user(chat_id)
        who_is = []
        if user_info["is_authorized_client"]:
            who_is.append("клиент")
        if user_info["is_operator"]:
            who_is.append("оператор")
        if user_info["is_admin"]:
            who_is.append("администратор")
        who_is = ", ".join(who_is)
        resp = self.static['slash_start_known'].format(who_is) if who_is else self.static["slash_start_unknown"]
        bot.sendMessage(chat_id, text=resp, reply_markup=self.get_markup(chat_id))
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")

    def slash_help(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        resp = self.static['slash_help']
        if chat_id in self.static["admin_chat_ids"] and not self.operators.is_operator(chat_id):
            resp = self.static["admin_help"]
        elif chat_id not in self.static["admin_chat_ids"] and self.operators.is_operator(chat_id):
            resp = self.static["operator_help"]
        elif chat_id in self.static["admin_chat_ids"] and self.operators.is_operator(chat_id):
            resp = self.static["admin_operator_help"]
        bot.sendMessage(chat_id, text=resp, reply_markup=self.get_markup(chat_id))
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")

    def slash_about(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        resp = self.static['slash_about']
        bot.sendMessage(chat_id, text=resp, reply_markup=self.get_markup(chat_id))
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")

    def slash_settings(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        text, options = self.settings_menu('s', chat_id, bot)
        self.msg_with_buttons(bot, update, text, options)
        self.log_msg(chat_id=chat_id, text=text + '\noptions: ' + str([o[0] for o in options]), sender="bot")

    def slash_info(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        resp = self.static["slash_info"]
        bot.sendMessage(chat_id, text=resp, reply_markup=self.get_markup(chat_id))
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")

    def slash_refresh(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        self.refresh_static()
        self.clients.refresh()
        self.operators.refresh()
        if chat_id in self.static["admin_chat_ids"]:
            resp = "success"
            self.log_msg(chat_id=chat_id, text=resp, sender="bot")
            bot.sendMessage(chat_id, resp, reply_markup=self.get_markup(chat_id))

    def slash_history(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        if chat_id in self.static["admin_chat_ids"] or chat_id in self.operators.operator_chat_ids:
            clients_of_operators = self.operators.clients_of_operators.get(chat_id)
            if not clients_of_operators:
                resp = self.static["history_no_chats"]
                self.log_msg(chat_id=chat_id, text=resp, sender="bot")
                bot.sendMessage(chat_id, resp, reply_markup=self.get_markup(chat_id))
            for client in clients_of_operators:
                resp = self.logs_parser.get_text(client, tech=True, max_len=30)
                self.log_msg(chat_id=chat_id, text=resp, sender="bot")
                bot.sendMessage(chat_id, resp[-4090:],
                                reply_markup=self.get_markup(chat_id),
                                parse_mode = "Markdown")

    def slash_on(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        if chat_id in self.operators.operator_chat_ids:
            self.operators.set_availability(chat_id, 1)
            resp = "Вы готовы принимать сообщения"
            self.log_msg(chat_id=chat_id, text=resp, sender="bot")
            bot.sendMessage(chat_id, resp, reply_markup=self.get_markup(chat_id))

    def slash_off(self, bot, update, internal=False):
        chat_id = update.message.chat_id
        if not internal:
            self.log_msg(update=update, sender="any")
        if chat_id in self.operators.operator_chat_ids:
            self.operators.set_availability(chat_id, 0)
            resp = "Вы больше не будете принимать сообщения"
            self.log_msg(chat_id=chat_id, text=resp, sender="bot")
            bot.sendMessage(chat_id, resp, reply_markup=self.get_markup(chat_id))

    def slash_add(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            try:
                new_op = int(update.message.text[5:])
                self.operators.set_availability(new_op, 0)
                bot.sendMessage(chat_id, "{} добавлен как оператор".format(new_op))
            except ValueError:
                bot.sendMessage(chat_id, self.static["admin_not_properly_add"])

    def slash_del(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            try:
                del_op = int(update.message.text[5:])
                self.operators.delete_operator(del_op)
                bot.sendMessage(chat_id, "{} больше не оператор".format(del_op))
            except:
                bot.sendMessage(chat_id, self.static["admin_not_properly_del"])

    def slash_add_admin(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            try:
                new_admin = int(update.message.text[11:])
                self.admins = list(set(self.admins) | {new_admin})
                self._rewrite_static()
                bot.sendMessage(chat_id, "{} добавлен как администратор".format(new_admin))
            except ValueError:
                bot.sendMessage(chat_id, self.static["admin_not_properly_add_admin"])

    def slash_del_admin(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            try:
                del_admin = int(update.message.text[11:])
                self.admins = list(set(self.admins) - {del_admin})
                self._rewrite_static()
                bot.sendMessage(chat_id, "{} больше не администратор".format(del_admin))
            except ValueError:
                bot.sendMessage(chat_id, self.static["admin_not_properly_del_admin"])

    def slash_admins(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            bot.sendMessage(chat_id, str(self.admins))


    def slash_logs(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            max_len = update.message.text[6:]
            try:
                max_len = int(max_len)
            except:
                max_len = self.static["logs_len_default"]
            bot.sendMessage(chat_id, self.logs_parser.get_text(max_len=max_len, tech=True), parse_mode="Markdown")

    def slash_operators(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id in self.static["admin_chat_ids"]:
            bot.sendMessage(chat_id, str(self.operators.operators))

 # idle - chatbot mode
    def idle_chatbot_mode(self, bot, update):
        chat_id = update.message.chat_id
        resp = self.static["chatbot_did_not_understand_user_message"]
        bot.sendMessage(chat_id, text=resp)
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")

# idle - chat with operator mode
    def forward_message_to_operator(self, bot, update):
        chat_id = update.message.chat_id
        operator_chat_id, changed_operator = self.operators.get_operator_chat_id(chat_id)
        if operator_chat_id:
            hist = None
            if changed_operator:
                hist = self.logs_parser.get_text(chat_id)
                bot.sendMessage(chat_id=operator_chat_id, text = hist, parse_mode="Markdown")
            bot.forwardMessage(chat_id=operator_chat_id, from_chat_id=chat_id, message_id=update.message.message_id)
            if changed_operator and hist:
                self.log_msg(chat_id=chat_id, text=hist, sender="bot_to_operator", orignal_chat_id=chat_id)
        else:
            self.clients.set_field(chat_id, "state", TelegramWrapper.CHATBOT_MODE)
            self.operators.close_session(chat_id)
            resp = self.static["client_got_no_free_operator"]
            bot.sendMessage(chat_id, resp, reply_markup=self._AUTHORIZED_MARKUP)
            self.log_msg(chat_id=chat_id, text=resp, sender="bot", orignal_chat_id=chat_id)

    def send_message_to_client(self, bot, update):
        operator_chat_id = update.message.chat_id
        try:
            client_chat_id = update.message.reply_to_message.forward_from.id
        except AttributeError:
            resp = self.static["operator_sent_without_reply_text"]
            bot.sendMessage(operator_chat_id, text=resp, reply_markup=self.get_markup(operator_chat_id))
            self.log_msg(chat_id=operator_chat_id, text=resp, sender="bot_to_operator")
        else:
            if self.clients.get_client(client_chat_id)["state"] != TelegramWrapper.OPERATOR_MODE:
                resp = self.static["operator_sent_message_to_closed_chat_text"]
                bot.sendMessage(chat_id=operator_chat_id, text=resp, reply_markup=self.get_markup(operator_chat_id))
                self.log_msg(chat_id=operator_chat_id, text=resp, sender="bot_to_operator")
            else:
                bot.sendMessage(chat_id=client_chat_id, text=update.message.text,
                                reply_markup=self.get_markup(client_chat_id))

    def turn_on_operator(self, bot, update, check=True):
        chat_id = update.message.chat_id
        new_operator, changed_operator = self.operators.get_operator_chat_id(chat_id)
        if new_operator:
            self.clients.set_field(chat_id, "state", TelegramWrapper.OPERATOR_MODE)
            bot.sendMessage(chat_id=chat_id, text=self.static["client_opened_chat"], reply_markup=self._CLOSE_CHAT_MARKUP)
            resp = self.static["operator_new_session"]
            bot.sendMessage(new_operator, resp)
            self.forward_message_to_operator(bot, update)
            self.log_msg(chat_id=chat_id, text=resp, sender="bot_to_operator", orignal_chat_id=new_operator)
        else:
            resp = self.static["client_got_no_free_operator"]
            bot.sendMessage(chat_id=chat_id, text=resp)
            self.log_msg(update=update, text=resp, sender="bot")

    def turn_off_operator(self, bot, update, check=True):
        chat_id = update.message.chat_id
        self.clients.set_field(chat_id, "state", TelegramWrapper.CHATBOT_MODE)
        resp = self.static["client_closed_chat"]
        bot.sendMessage(chat_id, resp, reply_markup=self._AUTHORIZED_MARKUP)
        self.log_msg(chat_id=chat_id, text=resp, sender="bot")
        self.forward_message_to_operator(bot, update)
        operator_chat_id, changed_operator = self.operators.get_operator_chat_id(chat_id)
        self.operators.close_session(chat_id)
        if not changed_operator:
            bot.sendMessage(operator_chat_id, self.static["operator_sent_message_to_closed_chat_text"])

    def get_contact(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id == update.message.contact.user_id:
            if self.clients.is_client(update.message.contact.phone_number):
                resp = self.static["contact_accepted"]
                self.clients.authorize_client(update.message.contact.__dict__, self.static["settings_default"])
                bot.sendMessage(chat_id, resp, reply_markup=self._AUTHORIZED_MARKUP)
            else:
                # self.send_text_to_operator(bot, update, self.static['contact_not_person_msg_to_operator'])
                resp = self.static['not_known_contact']
                bot.sendMessage(chat_id, resp)
        else:
            # self.send_text_to_operator(bot, update, self.static['contact_not_person_msg_to_operator'])
            resp = self.static['contact_not_yours']
            bot.sendMessage(chat_id, resp)
        self.log_msg(chat_id=chat_id, sender="bot", text=resp)

    def send_message_that_should_auth(self, bot, update):
        resp = self.static["should_auth"]
        bot.sendMessage(update.message.chat_id, resp, reply_markup=self._REQUEST_CONTACT_MARKUP)
        self.log_msg(chat_id=update.message.chat_id,
                     sender="bot",
                     text=resp + "; options: " + self.static["request_contact_button_text"])

# settings story
    def add_cities_to_settings(self, bot, update, client=None):
        txt = update.message.text.replace(';', ',').replace('.', ',').replace('\n', ',').split(',')
        client = client or self.clients.get_client(update.message.chat_id)
        client['city'] = list(set([i.strip().capitalize() for i in client['city'] + txt]))
        if u'Питер' in client['city']:
            client['city'].remove(u'Питер')
            client['city'].append(u'Санкт-Петербург')
        if u'Спб' in client['city']:
            client['city'].remove(u'Спб')
            client['city'].append(u'Санкт-Петербург')
        if u'Мск' in client['city']:
            client['city'].remove(u'Мск')
            client['city'].append(u'Москва')
        client['state'] = TelegramWrapper.CHATBOT_MODE
        self.clients.set_client(update.message.chat_id, client)
        resp = self.static["settings_city_add_approve"].format(', '.join(client['city']))
        bot.sendMessage(update.message.chat_id, text=resp)
        self.log_msg(chat_id=update.message.chat_id, text=resp, sender="bot")

    def settings_menu(self, callback, chat_id, bot):
        # ad-hoc func for inline button(): defines which text and buttons to send depending on entry inline query
        text = ''
        options = []
        settings = self.clients.get_client(chat_id)
        if callback == 's':
            text = u'Текущие настройки:'
            text += u'\n🔸 Города: '
            if len(settings['city']) == 0:
                text += u'не указаны'
            else:
                text += ", ".join(settings['city'])
            text += u'\n🔸 Подписки: '
            if settings['subscribe']:
                text += ", ".join(settings['subscribe'])
            else:
                text += 'отсутствуют'
            options.append([u'Города', 'city'])
            options.append([u'Подписки', 'sub'])
        # cities story
        elif callback == 's♞city':
            text = self.static["settings_city"]
            options.append([u'Добавить', 'add'])
            if len(settings['city']) > 0:
                text += u'. Выбранные города: %s' % ', '.join(settings['city'])
                options.append([u'Удалить', 'del'])
                options.append([u'Удалить все', 'delall'])
        elif callback == 's♞city♞add':
            self.clients.set_field(chat_id, 'state', TelegramWrapper.CHATBOT_ENTERING_CITIES_MODE)
            bot.sendMessage(chat_id, text=self.static["settings_city_add_which"])
        elif callback == 's♞city♞del':
            text = self.static["settings_city_del_which"]
            for city in settings['city']:
                options.append([city, city])
        elif callback == 's♞city♞delall':
            self.clients.set_field(chat_id, "city", [])
            text = self.static["settings_city_del_all_success"]
        elif callback.startswith('s♞city♞del♞'):
            city_to_delete = callback[len('s♞city♞del♞'):]
            cities = set(settings['city'])
            try:
                cities.remove(city_to_delete)
            except:
                pass
            self.clients.set_field(chat_id, "city", list(cities))
            text = self.static["settings_city_del_success"].format(city_to_delete)
        # subscribe story
        elif callback == 's♞sub':
            text = self.static["settings_subscribe"]
            options.append([u'Добавить', 'add'])
            if len(settings['subscribe']) > 0:
                text += u'. Выбранные подписки: {}'.format(', '.join(settings['subscribe']))
                options.append([u'Удалить', 'del'])
                options.append([u'Удалить все', 'delall'])
        elif callback == 's♞sub♞add':
            all_subscribes = self.static["chatbot_subscribes"]
            user_subscribes = self.clients.get_client(chat_id)["subscribe"]
            available_subscribes = [s for s in all_subscribes if s not in user_subscribes]
            if available_subscribes:
                text = self.static["settings_subscribe_add_which"]
                for s in available_subscribes:
                    options.append([s, s])
            else:
                text = self.static["settings_subscribe_add_already_all"]
        elif callback == 's♞sub♞del':
            text = self.static["settings_subscribe_del_which"]
            for s in settings['subscribe']:
                options.append([s, s])
        elif callback == 's♞sub♞delall':
            self.clients.set_field(chat_id, "subscribe", [])
            text = self.static["settings_subscribe_del_all_success"]
        elif callback.startswith('s♞sub♞del♞'):
            sub_to_delete = callback[len('s♞sub♞del♞'):]
            user_subscribes = set(settings['subscribe'])
            try:
                user_subscribes.remove(sub_to_delete)
            except:
                pass
            self.clients.set_field(chat_id, "subscribe", list(user_subscribes))
            text = self.static["settings_subscribe_del_success"].format(sub_to_delete)
        elif callback.startswith('s♞sub♞add♞'):
            sub_to_add = callback[len('s♞sub♞add♞'):]
            user_subscribes = set(settings['subscribe'])
            try:
                user_subscribes.add(sub_to_add)
            except:
                pass
            self.clients.set_field(chat_id, "subscribe", list(user_subscribes))
            text = self.static["settings_subscribe_add_success"].format(sub_to_add)

        # adding path for every command
        for o in options:
            o[1] = callback + '♞' + str(o[1])
        # adding 'back' button to all menu's but start menu
        if callback != 's':
            options = [['⬅', '♞'.join(callback.split('♞')[:-1])]] + options
        return (text, options)

# inline story
    def button(self, bot, update):
        query = update.callback_query
        txt = query.data
        chat_id = query.message.chat_id
        self.log_msg(chat_id=chat_id, text="button "+txt, sender="any", orignal_chat_id=chat_id)
        # TODO: text для логгирования дополнить оригинальным текстом поверх кнопки
        # TODO: chat_id для логгирования не тот в случае оператора

        text, options = self.settings_menu(txt, chat_id, bot)
        if len(text) > 0:
            self.msg_with_buttons(bot, update, text, options, chat_id, query.message.message_id)
        return True

# main
    def idle_main(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id not in {34600304, 240443804}:
            print(object_to_str(update.message, ignore_null=True))
        is_admin = chat_id in self.admins
        is_operator = self.operators.is_operator(chat_id)
        is_authorized_client = self.clients.is_authorized_client(chat_id)

        if is_authorized_client and not is_operator:
            self.log_msg(update)
            if update.message.text == self.static["close_chat_button_text"]:
                self.turn_off_operator(bot, update)
                return
            if update.message.text == self.static["open_chat_button_text"]:
                self.turn_on_operator(bot, update)
                return
            if update.message.text == self.static["button_info_text"]:
                self.slash_info(bot, update, internal=True)
                return
            if update.message.text == self.static["button_settings_text"]:
                self.slash_settings(bot, update, internal=True)
                return
            client = self.clients.get_client(chat_id)
            state = client.get("state")
            if state == TelegramWrapper.CHATBOT_ENTERING_CITIES_MODE:
                self.add_cities_to_settings(bot, update, client)
                return
            if state == TelegramWrapper.OPERATOR_MODE:
                self.forward_message_to_operator(bot, update)
            else:
                self.idle_chatbot_mode(bot, update)
            return
        if is_operator:
            self.log_msg(update, mode=TelegramWrapper.OPERATOR_MODE)
            if update.message.text == self.static["operator_button_on_off"]["0"]:
                self.slash_on(bot, update, internal=True)
                return
            if update.message.text == self.static["operator_button_on_off"]["1"]:
                self.slash_off(bot, update, internal=True)
                return
            if update.message.text == self.static["operator_button_history"]:
                self.slash_history(bot, update, internal=True)
                return
            self.send_message_to_client(bot, update)
            return
        self.log_msg(update)
        self.send_message_that_should_auth(bot, update)

    def main(self):
        # Create the EventHandler and pass it your bot's token.
        updater = Updater(self.TG_TOKEN)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))

# all
        dp.add_handler(CommandHandler("start", self.slash_start), group=0)
        dp.add_handler(CommandHandler("help", self.slash_help), group=0)
        dp.add_handler(CommandHandler("h", self.slash_help), group=0)
        dp.add_handler(CommandHandler("about", self.slash_about), group=0)
        dp.add_handler(CommandHandler("settings", self.slash_settings), group=0)
# operator
        dp.add_handler(CommandHandler("on", self.slash_on), group=0)
        dp.add_handler(CommandHandler("off", self.slash_off), group=0)
        dp.add_handler(CommandHandler("history", self.slash_history), group=0)
# admin
        dp.add_handler(CommandHandler("refresh", self.slash_refresh), group=0)
        dp.add_handler(CommandHandler("logs", self.slash_logs), group=0)
        dp.add_handler(CommandHandler("operators", self.slash_operators), group=0)
        dp.add_handler(CommandHandler("add", self.slash_add), group=0)
        dp.add_handler(CommandHandler("del", self.slash_del), group=0)
        dp.add_handler(CommandHandler("admins", self.slash_admins), group=0)
        dp.add_handler(CommandHandler("add_admin", self.slash_add_admin), group=0)
        dp.add_handler(CommandHandler("del_admin", self.slash_del_admin), group=0)

        # on noncommand message
        dp.add_handler(MessageHandler(filter_not_contact, self.idle_main))
        dp.add_handler(MessageHandler(Filters.contact, self.get_contact))

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot
        updater.idle()
