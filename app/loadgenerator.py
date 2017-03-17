from flask import render_template,redirect,url_for,request,g
from app import webapp

import mysql.connector
import os
import boto3

from app.config import db_config
from wand.image import Image

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

@webapp.route('/test/FileUpload/form',methods=['GET'])
#Return file upload form
def upload_form():
    return render_template("loadgenerator.html")


@webapp.route('/test/FileUpload',methods=['POST'])
#Upload a new file and store in the systems temp directory
def file_upload():
    login = request.form.get("userID")
    password = request.form.get("password")

    error = False

    if login == "" or password == "":
        return "Missing username or password"

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM users WHERE login = %s '''
    cursor.execute(query,(login,))

    row = cursor.fetchone()

    if row == None:
        return "User not existed"

    id = row[0]
    _login = row[1]
    _password = row[2]

    if _password != password:
        return "Wrong password"

    #---------------------------------------------------------

    # check if the post request has the file part
    if 'uploadedfile' not in request.files:
        return "Missing uploaded file"

    new_image = request.files['uploadedfile']

    # if user does not select file, browser also
    # submit a empty part without filename
    if new_image.filename == '':
        return 'Missing file name'

    fname = os.path.join('app/static',new_image.filename)
    new_image.save(fname)

    img = Image(filename=fname)
    i1 = img.clone()
    i1.modulate(33,67,50)
    fname_tr1 = os.path.join('app/static',"TR1_" + new_image.filename)
    i1.save(filename=fname_tr1)
    i2 = img.clone()
    i2.flop()
    fname_tr2 = os.path.join('app/static',"TR2_" + new_image.filename)
    i2.save(filename=fname_tr2)
    i3 = img.clone()
    i3.transform('300*300','200%')
    fname_tr3 = os.path.join('app/static',"TR3_" + new_image.filename)
    i3.save(filename=fname_tr3)

    s3 = boto3.client('s3')
    with open(fname,"rb") as image1:
        s3.upload_fileobj(image1,"ece1779",str(id) + "_ORI_" + new_image.filename)
    with open(fname_tr1,"rb") as image2:
        s3.upload_fileobj(image2,"ece1779",str(id) + "_TR1_" + new_image.filename)
    with open(fname_tr2,"rb") as image3:
        s3.upload_fileobj(image3,"ece1779",str(id) + "_TR2_" + new_image.filename)
    with open(fname_tr3,"rb") as image4:
        s3.upload_fileobj(image4,"ece1779",str(id) + "_TR3_" + new_image.filename)

    os.remove(fname)
    os.remove(fname_tr1)
    os.remove(fname_tr2)
    os.remove(fname_tr3)

    query = ''' INSERT INTO images (userId,key1,key2,key3,key4) VALUES (%s,%s,%s,%s,%s)'''
    cursor.execute(query,(id,
                          new_image.filename,
                          "TR1_" + new_image.filename,
                          "TR2_" + new_image.filename,
                          "TR3_" + new_image.filename))
    cnx.commit()

    return "Success"
