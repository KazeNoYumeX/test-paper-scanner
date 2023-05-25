import configparser

from flask import Blueprint

config = configparser.ConfigParser()
config.read('test_paper_scanner_config.ini')
config_bp = Blueprint('config', __name__)
