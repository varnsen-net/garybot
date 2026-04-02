""""""
from src.client.logger import Logger
from src.client.writer import Writer
from src.client.dispatcher import Dispatcher
from src.client.listener import Listener
from src.channel_functions.trivia import Trivia


def build_actors(sock, stop_event, app_config):
    """"""
    writer = Writer(sock, stop_event)
    logger_ = Logger(stop_event, app_config)
    trivia = Trivia(writer, stop_event, app_config)
    dispatcher = Dispatcher(writer, logger_, trivia, stop_event, app_config)
    listener = Listener(dispatcher, sock, stop_event)
    return [writer, logger_, trivia, dispatcher, listener]
