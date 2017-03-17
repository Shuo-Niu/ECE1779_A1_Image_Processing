from flask import render_template
from app import webapp

import os

@webapp.route('/',methods=['GET'])
#Return html with pointers to the examples
def main():

    os.system("rm -rf app/static/* ")

    return render_template("main.html",
                           title="Main Page")

