from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from scraper import app

import os
from configparser import RawConfigParser

here = os.path.dirname(__file__)
parser = RawConfigParser()
parser.read(os.path.join(here, "config"))

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(parser.get("config", "port"))
IOLoop.instance().start()
