
from flask import Flask

webapp = Flask(__name__)

from app import main
from app import user
from app import image
from app import loadgenerator

