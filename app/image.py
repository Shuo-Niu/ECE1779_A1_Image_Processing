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

@webapp.route('/<int:id>/images_view',methods=['GET'])
def images_view(id):
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT key1 FROM images WHERE userId = %s '''
    cursor.execute(query,(id,))

    images = []
    s3 = boto3.client('s3')
    for key in cursor:
        fname = os.path.join('app/static',str(key)[2:-3])
        with open(fname,"wb") as img:
            s3.download_fileobj("ece1779",str(id) + "_ORI_" + str(key)[2:-3],img)
            images.append(fname[3:])

    return render_template("images/thumbnail.html",
                           title="Thumbnails",
                           images=images,
                           id=id)

@webapp.route('/<int:id>/<image>',methods=['GET'])
def image_trans(id,image):
    trans = []
    fname = os.path.join('app/static',image)
    trans.append(fname[3:])

    s3 = boto3.client('s3')

    fname_tr1 = os.path.join('app/static',"TR1_" + image)
    with open(fname_tr1,"wb") as img1:
        s3.download_fileobj("ece1779",str(id) + "_TR1_" + image,img1)
        trans.append(fname_tr1[3:])

    fname_tr2 = os.path.join('app/static',"TR2_" + image)
    with open(fname_tr2,"wb") as img2:
        s3.download_fileobj("ece1779",str(id) + "_TR2_" + image,img2)
        trans.append(fname_tr2[3:])

    fname_tr3 = os.path.join('app/static',"TR3_" + image)
    with open(fname_tr3,"wb") as img3:
        s3.download_fileobj("ece1779",str(id) + "_TR3_" + image,img3)
        trans.append(fname_tr3[3:])

    return render_template("images/trans.html",
                           title="View Image",
                           id=id,
                           image=image,
                           trans=trans)

@webapp.route('/<int:id>/<image>/delete',methods=['POST'])
def image_delete(id,image):
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' DELETE FROM images WHERE userId = %s and key1 = %s '''
    cursor.execute(query,(id,image))
    cnx.commit()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket("ece1779")
    key = image
    response = bucket.delete_objects(
        Delete={
            'Objects':[
                {'Key':str(id) + "_ORI_" + key},
                {'Key':str(id) + "_TR1_" + key},
                {'Key':str(id) + "_TR2_" + key},
                {'Key':str(id) + "_TR3_" + key}
            ]
        }
    )

    return redirect(url_for('images_view',id=id))

@webapp.route('/<int:id>/images_upload',methods=['GET'])
def image_upload(id):
    return render_template("images/new.html",
                           title="Upload Image",
                           id=id)

@webapp.route('/<int:id>/images_upload',methods=['POST'])
def image_upload_save(id):
    if 'uploadedfile' not in request.files:
        return redirect(url_for('image_upload',id=id))
    
    new_image = request.files['uploadedfile']
    
    if new_image.filename == "":
        return redirect(url_for('image_upload',id=id))

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' SELECT * FROM images WHERE userId = %s and key1 = %s '''
    cursor.execute(query,(id,new_image.filename))
    row = cursor.fetchone()

    if row != None:
        return render_template("images/new.html",
                               title="Upload Image",
                               id=id,
                               error_msg="Image exsited!")

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

    return redirect(url_for('images_view',id=id))
