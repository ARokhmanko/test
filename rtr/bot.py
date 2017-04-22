'''
Created on 15 апр. 2017 г.

@author: ARokhmanko
'''
# -*- coding: utf-8 -*-

import telebot
from rtr import config

bot = telebot.TeleBot(config.token)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, важно не повторяться
    bot.send_message(message.chat.id, message.text)


if __name__ == "__main__":
    bot.polling(none_stop=True)
