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


# def dot_trivia(nick):
    # """"""
    # n = random.randint(9,32)  # general knowledge to cartoons
    # trivia_api = f"https://opentdb.com/api.php?amount=1&difficulty=medium&type=multiple&category={n}"
    # response = requests.get(trivia_api).json()
    # if response['response_code'] != 0:
        # return f"{nick}: Sorry, I couldn't fetch a trivia question right now."
    # question_data = response['results'][0]
    # category = question_data['category']
    # question = unescape(question_data['question'])
    # correct_answer = unescape(question_data['correct_answer'])
    # incorrect_answers = [unescape(ans) for ans in question_data['incorrect_answers']]
    # options = incorrect_answers + [correct_answer]
    # random.shuffle(options)
    # options_str = ' '.join(f"({l}) {opt}" for l, opt in zip('abcd', options))
    # return f"{nick}: 15,01TRIVIA 🧐 04{category}: {question} {options_str}"


class Trivia(gevent.Greenlet):
    """"""

    def __init__(self, writer, stop_event, app_config):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._writer = writer
        self._stop_event = stop_event
        self._main_channel = app_config.irc_main_channel
        self._trivia_url = "https://the-trivia-api.com/v2/questions"
        self._deck = []
        self._players = {}

    def _play(self, turn):
        """"""
        player = turn[0]
        regex_match = turn[1].group(2) # group 2 is the answer part of the regex
        if not self._deck:
            params = {"limit": 30, "difficulties": "medium,hard"}
            response = requests.get(self._trivia_url, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch trivia questions: {response.status_code}")
                return
            self._deck = response.json()
        if player not in self._players:
            self._create_player(player)
        if not regex_match:
            category, question, options_str, correct_option = self._create_trivia_question()
            self._players[player]['current_answer'] = correct_option
            self._players[player]['score'] -= 1  # Deduct a point for asking a question
            reponse = f"{player}: 15,01TRIVIA 🧐 04{category}: {question} {options_str}"
            self._writer.inbox.put(f"PRIVMSG {self._main_channel} :{reponse}")
            return
        answer = regex_match.strip().lower()
        reply = self._compare_answers(player, answer)
        self._writer.inbox.put(f"PRIVMSG {self._main_channel} :{reply}")
        self._players[player]['current_answer'] = None

    def _create_player(self, player):
        """"""
        self._players[player] = {"score": 0, "current_answer": None}

    def _compare_answers(self, player, player_answer):
        """"""
        if not self._players[player]['current_answer']:
            reply = f"{player}: You don't have an active question. Use .tr[ivia] to get one."
        elif player_answer == self._players[player]['current_answer']:
            self._players[player]['score'] += 2
            reply = f"{player}: Correct! Your score is now {self._players[player]['score']}."
        else:
            reply = f"{player}: Incorrect. The correct answer was ({self._players[player]['current_answer']}). Your score is {self._players[player]['score']}."
        return reply

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

    def _run(self):
        logger.info("Trivia started.")
        while not self._stop_event.is_set():
            try:
                turn = self.inbox.get(timeout=1)
            except Empty:
                continue
            self._play(turn)
