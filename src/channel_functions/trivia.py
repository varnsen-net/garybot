"""
sqlite> .schema user_logs
CREATE TABLE user_logs (
            nick text,
            target text,
            message text,
            timestamp real);
"""
import requests
import random

import gevent
from gevent.queue import Queue, Empty
from loguru import logger


class Trivia(gevent.Greenlet):
    """"""

    _CORRECT_SYNTAX = ".tr [AaBbCcDd]"

    def __init__(self, writer, stop_event, app_config):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._writer = writer
        self._stop_event = stop_event
        self._main_channel = app_config.irc_main_channel
        self._trivia_url = "https://the-trivia-api.com/v2/questions"
        self._deck = []
        self._players = {}

    def _run(self):
        """"""
        logger.info("Trivia started.")
        while not self._stop_event.is_set():
            try:
                turn = self.inbox.get(timeout=1)
            except Empty:
                continue
            self._play(turn)

    def _play(self, turn):
        """"""
        player, word_list = turn
        if len(word_list) > 2:
            self._send(f"{player}: Correct syntax is {self._CORRECT_SYNTAX}")
            return
        if not self._deck:
            self._replenish_deck()
            if not self._deck:
                self._send(f"{player}: Sorry, I'm having trouble fetching trivia questions right now. Please try again later.")
                return
        if player not in self._players:
            self._create_player(player)
        if len(word_list) == 1:
            self._ask_question(player)
        elif (answer := word_list[1].lower()) in ('a', 'b', 'c', 'd'):
            reply = self._compare_answers(player, answer)
            self._send(reply)
            self._players[player]['current_answer'] = None
        else:
            self._send(f"{player}: Invalid answer. Use {self._CORRECT_SYNTAX}")

    def _send(self, message):
        """"""
        self._writer.inbox.put(f"PRIVMSG {self._main_channel} :{message}")

    def _replenish_deck(self):
        """"""
        params = {"limit": 30, "difficulties": "medium,hard"}
        response = requests.get(self._trivia_url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to replenish trivia deck: {response.status_code}")
            return
        self._deck = response.json()

    def _create_player(self, player):
        """"""
        self._players[player] = {"asked": 0, "correct": 0, "current_answer": None}

    def _ask_question(self, player):
        """"""
        category, question, options_str, correct_option = self._create_trivia_question()
        category = category.replace("_", " ")
        self._players[player]['current_answer'] = correct_option
        self._players[player]['asked'] += 1
        reponse = f"{player}: TRIVIA [{category}]: {question} {options_str}"
        self._send(reponse)

    def _create_trivia_question(self):
        """"""
        question_data = self._deck.pop(0)
        category = question_data['category']
        question = question_data['question']['text']
        correct_answer = question_data['correctAnswer']
        options = question_data['incorrectAnswers'] + [correct_answer]
        random.shuffle(options)
        options_str = ' '.join(f"({l}) {opt}" for l, opt in zip('abcd', options))
        correct_option = 'abcd'[options.index(correct_answer)]
        return category, question, options_str, correct_option

    def _compare_answers(self, player, player_answer):
        """"""
        if not self._players[player]['current_answer']:
            reply = f"{player}: You don't have an active question. Use .tr to get one."
        elif player_answer == self._players[player]['current_answer']:
            self._players[player]['correct'] += 1
            reply = f"{player}: Correct! Your score is now {self._report_accuracy(player)}."
        else:
            reply = f"{player}: Incorrect. The correct answer was ({self._players[player]['current_answer']}). Your score is {self._report_accuracy(player)}."
        return reply

    def _report_accuracy(self, player):
        """"""
        asked = self._players[player]['asked']
        correct = self._players[player]['correct']
        accuracy = (correct / asked) * 100
        return f"{int(accuracy)}% ({correct}/{asked})"

