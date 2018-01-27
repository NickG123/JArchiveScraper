import logging
import random

from flask import Flask, jsonify, abort, request
from scraper import JeopardyScraper

app = Flask(__name__)
scraper = JeopardyScraper()


@app.route("/")
def get_random():
    try:
        category_name, value, _game_id, jeopardy_round, question, answer, date = scraper.get_random_clue()
        result = {"category": category_name, "value": value * 200 * jeopardy_round, "round": "Jeopardy" if round == 1 else "Double Jeopardy", "question": question, "answer": answer, "date": date}
        return jsonify(result)
    except Exception as ex:
        logging.error("An unexpected error occurred", exc_info=ex)
        abort(500)


@app.route("/category")
def get_category():
    try:
        jeopardy_round = request.args.get('round', None)
        jeopardy_round = int(jeopardy_round) if jeopardy_round is not None else random.randint(1, 2)
        category_name, _game_id, questions, answers, date = scraper.get_random_category(jeopardy_round)
        result = {"category": category_name, "round": "Jeopardy" if round == 1 else "Double Jeopardy", "questions": questions, "answers": answers, "date": date}
        return jsonify(result)
    except Exception as ex:
        logging.error("An unexpected error occurred", exc_info=ex)
        abort(500)
