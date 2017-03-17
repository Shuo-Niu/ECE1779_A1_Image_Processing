from flask import render_template,redirect,url_for,request,g
from app import webapp

import mysql.connector

import re

from app.config import db_config

def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/',methods=['POST'])
def user_login():
    login = request.form.get('userId',"")
    password = request.form.get('password',"")
    
    error = False
    
    if login == "" or password == "":
        error = True
        error_msg = "Error: All fields are required!"
        
    if error:
        return render_template("main.html",
                                title="Main Page",
                                error_msg=error_msg,
                                userId=login,
                                password="")

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM users WHERE login = %s '''
    cursor.execute(query,(login,))
    
    row = cursor.fetchone()
    
    if row == None:
        return render_template("main.html",
                               title="Main Page",
                               error_msg="User not existed!")#redirect(url_for('user_login'))    
    id = row[0]
    _login = row[1]
    _password = row[2]
    
    if _password == password:
        return redirect(url_for('images_view',id=row[0]))
    else:
        return render_template("main.html",
                               title="Main Page",
                               error_msg="Wrong password!")#redirect(url_for('user_login'))
    
@webapp.route('/user_create',methods=['GET'])
def user_create():
    return render_template("users/new.html",
                           title="New User")

@webapp.route('/user_create',methods=['POST'])
def user_create_save():
    login = request.form.get('userId',"")
    password = request.form.get('password',"")
    reenter = request.form.get('reenter',"")
    
    error = False
    
    if login == "" or password == "" or reenter == "":
        error = True
        error_msg = "Error: All fields are required!"
        
    if password != reenter:
        error = True
        error_msg = "Re-entered password unmatched!"
        
    if error:
        return render_template("users/new.html",
                               title="New User",
                               error_msg=error_msg,
                               userId=login)
    
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM users WHERE login = %s '''
    cursor.execute(query,(login,))
    
    row = cursor.fetchone()
    
    if row != None:
        return render_template("users/new.html",
                               title="New User",
                               error_msg="User ID exsited!")
    
    
    query = ''' INSERT INTO users (login,password) VALUES (%s,%s)'''
    cursor.execute(query,(login,password))
    cnx.commit()
    
    return redirect(url_for('main'))
