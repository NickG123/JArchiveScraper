import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from retrying import retry

ENDPOINT = "http://j-archive.com"


class JeopardyException(Exception):
    pass


class LinkClueException(JeopardyException):
    pass


class GameMissingException(JeopardyException):
    pass


class ClueMissingException(JeopardyException):
    pass


def retry_if_jeopardy_error(exception):
    return isinstance(exception, JeopardyException)


class JeopardyScraper(object):
    def __init__(self):
        self.max_game = None
        self.latest_update = datetime.now()
        self.update()
        self.banned_games = set()

    def get_latest_id(self):
        resp = requests.get(ENDPOINT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        footers = soup.findAll("td", {"class": "splash_clue_footer"})
        return max(int(x.a['href'].split('=')[-1]) for x in footers)

    def get_game(self, game_id):
        resp = requests.get("{0}/showgame.php".format(ENDPOINT), params={'game_id': game_id})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        if soup.find("div", {"id": "jeopardy_round"}) is None or soup.find("div", {"id": "double_jeopardy_round"}) is None:
            self.banned_games.add(id)
            raise GameMissingException("Game does not exist")
        return soup

    def get_categories(self, game, jeopardy_round):
        categories = game.findAll("td", {"class": "category_name"})
        names = [x.text for x in categories]
        return names[(jeopardy_round - 1) * 6:jeopardy_round * 6]

    def get_question(self, game, jeopardy_round, category, value):
        clue = game.findAll("td", {"class": "clue"})[(jeopardy_round - 1) * 30 + (category - 1) + (value - 1) * 6]
        if len(list(clue.children)) == 1:
            raise ClueMissingException("Clue does not exist")
        rows = clue.table.findChildren("tr", recursive=False)
        question = rows[1].td
        answer_mouseover = rows[0].td.div["onmouseover"]
        answer_text = answer_mouseover.split(",", 2)[2].strip("') ")
        soup = BeautifulSoup(answer_text, "html.parser")
        answer = soup.em.text

        if question.a is not None or "seen here" in question.text.lower():
            raise LinkClueException("Question contains a link")
        return question.text, answer

    def get_date(self, game):
        title = game.find("div", {"id": "game_title"})
        date_str = title.h1.text.split("-")[-1].strip()
        return date_str

    @retry(retry_on_exception=retry_if_jeopardy_error, stop_max_attempt_number=5)
    def get_random_clue_from_game(self, game):
        jeopardy_round = random.randint(1, 2)
        category = random.randint(1, 6)
        category_name = self.get_categories(game, jeopardy_round)[category - 1]
        value = random.randint(1, 5)

        question, answer = self.get_question(game, jeopardy_round, category, value)

        return category_name, value, jeopardy_round, question, answer

    def get_random_category_from_game(self, game, jeopardy_round):
        category = random.randint(1, 6)
        category_name = self.get_categories(game, jeopardy_round)[category - 1]
        questions, answers = zip(*[self.get_question(game, jeopardy_round, category, value) for value in range(1, 6)])
        return category_name, questions, answers

    def get_random_game_id(self):
        self.update()
        game_id = None
        while game_id is None or game_id in self.banned_games:
            game_id = random.randint(1, self.max_game)
        return game_id

    @retry(retry_on_exception=retry_if_jeopardy_error)
    def get_random_clue(self):
        game_id = self.get_random_game_id()
        game = self.get_game(game_id)
        category_name, value, jeopardy_round, question, answer = self.get_random_clue_from_game(game)
        date = self.get_date(game)
        return category_name, value, game_id, jeopardy_round, question, answer, date

    @retry(retry_on_exception=retry_if_jeopardy_error)
    def get_random_category(self, jeopardy_round):
        game_id = self.get_random_game_id()
        game = self.get_game(game_id)
        category_name, questions, answers = self.get_random_category_from_game(game, jeopardy_round)
        date = self.get_date(game)
        return category_name, game_id, questions, answers, date

    def update(self):
        if self.max_game is None or datetime.now() - self.latest_update > timedelta(days=1):
            self.max_game = self.get_latest_id()
            self.latest_update = datetime.now()
