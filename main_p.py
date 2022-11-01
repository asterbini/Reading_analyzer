#   coding=utf-8

#imports

from flask import Flask, render_template, jsonify, flash, redirect, url_for, session, logging, request, current_app
from flask_wtf import FlaskForm, Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SubmitField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from _gFunctions import short_audio, long_audio, upload_file, download_blob, list_blobs
from PIL import ImageFont
from Diff import diff_t, get_errors, get_extensions
from Errors import *
from Text import nclean
from celery import Celery
import os, six, json
import soundfile
from datetime import datetime
import string
from Recorder import record, convert

BUCKET_NAME = 'speech-to-text-long-audio'
DEBUG=True
DEBUG=False

#//////////setting flask
app = Flask(__name__)
app.secret_key = 'secret123456'
app.config['UPLOAD_FOLDER'] = "static/audio_files/"


#//////////setting mysql connection
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:123456@localhost:3306/dsa_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dsa_reading:R5HX)pl-)z4).wf-@localhost:3306/dsa_reading?unix_socket=/var/lib/mysql/mysql.sock'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#//////////setting celery tasks
app.config['CELERY_BROKER_URL']='amqp://localhost'
#app.config['CELERY_RESULT_BACKEND']='amqp://localhost'
app.config['CELERY_RESULT_BACKEND']='celery_amqp_backend.AMQPBackend://localhost'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'],backend=app.config['CELERY_RESULT_BACKEND'])
#celery.conf.update(app.config)






#//////////gestione delle route della web app

@app.route('/')
def home():
    return render_template('home.html')
    #result = TranscriptionsDB.query().join(PatientDB, patient_id=PatientDB.id).join(SupervisorsDB, supervisor_id=SupervisorsDB.id).all()

    #return TranscriptionsDB.query.join(SupervisorsDB, TranscriptionsDB.supervisor_id==SupervisorsDB.id).join(PatientDB, TranscriptionsDB.patient_id==PatientDB.id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        id = form.id.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data.encode('utf-8')))

        new_supervisor = Supervisors(id, email, username, password)
        db.session.add(new_supervisor)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form fields
        username = request.form['username']
        password_candidate = str(request.form['password'].encode('utf-8'))


        #Get user by Username
        result = Supervisors.query.filter_by(username=username).first()
        if result:
            #get sotred hash
            #supervisor_id = result.id
            password = result.password

            #print(password_candidate, password)

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['id'] = result.id
                session['adjacents'] = 0
                #for i in algorithms:
                #    session[i] = False

                flash('You are now logged in', 'success')

                return redirect(url_for('analyzed_audios'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/analyzed_audios', methods=['GET', 'POST'])
@is_logged_in
def analyzed_audios():
    transcriptions = (db.session.query(Transcriptions, Patients, Working_texts)
                      .filter_by(supervisor_id=session['id'])
                      .outerjoin(Patients, Patients.cf==Transcriptions.patient_id)
                      .outerjoin(Working_texts, Working_texts.id==Transcriptions.text_id)
                      .add_columns(Patients.cf, 
                                   Patients.name,
                                   Patients.surname, 
                                   Transcriptions.update_date,
                                   Transcriptions.id, 
                                   Working_texts.title,
                                   Working_texts.schoolyear,
                                   Working_texts.period)
                      .all())

    return render_template('analyzed_audios.html', transcriptions=transcriptions)

@app.route('/record_audio')
@is_logged_in
def record_audio():
    record()
    id = request.referrer.split('/')[-1]
    text = Working_texts.query.filter_by(id=id).first()
    return render_template('read_text.html', text=text)

highlighted = dict()

@app.route('/record_audio_stop')
@is_logged_in
def record_audio_stop():
    convert()
    texts = Working_texts.query.all()
    global highlighted
    id = request.referrer.split('/')[-1]
    text = Working_texts.query.filter_by(id=id).first()
    user_id = session['id']
    words = Highlighted_words.query.filter_by(user=user_id, text=text.id).all()
    user_time = 0
    if words != None:
        for w in words:
            if w.user_time > user_time:
                user_time = w.user_time
    for value in highlighted.values():
        db.session.add(Highlighted_words(user_id, user_time + 1, text.id, value[0], value[1], value[2]))
        db.session.commit()
    highlighted.clear()
    return render_template('audio_upload.html', error=None, texts=texts)


@app.route('/add_word/<string:index>/<string:word>/<string:start>/<string:finish>')
@is_logged_in
def add_word(index, word, start, finish):
    id = request.referrer.split('/')[-1]
    text = Working_texts.query.filter_by(id=id).first()
    if '.' in start:
        start = start[:start.find('.') + 4]
    if '.' in finish:
        finish = finish[:finish.find('.') + 4]
    global highlighted
    if word[-1] in string.punctuation and word[-1] != '-':
        word = word[:-1]
    if word != '-':
        word_id = Words.query.filter_by(word=word).first().id
        text_word_id = Text_words.query.filter_by(word=word_id).first().id
        highlighted[word] = (text_word_id, index, start)
    return render_template('read_text.html', text=text)
    

@app.route('/audio_record_upload', methods=["POST"])
@is_logged_in
def audio_record_upload():
    from difflib import ndiff
    from pathlib2 import Path
    import glob
    import shutil
    import time

    error = None
    texts = Working_texts.query.all()
    
    if request.method == "POST":
        origin = request.referrer.split('/')[-1]
        patient_name = session['username']
        patient_surname = session['username']
        date = datetime.now()
        now = date.strftime('%Y-%m-%d %H:%M:%S')
        patient_bday = now
        patient_cf = session['id']
        patient_gender = 'M'
        text = Working_texts.query.filter_by(id=origin).first()
        text_title = text.title; 
        
        if patient_name == None or patient_name == '':
            error = "Please insert a patient name"
        elif patient_surname == None or patient_surname == '':
            error = "Please insert a patient surname"
        elif patient_cf == None or patient_cf == '':
            error = "Please insert a patient id"
        elif text_title =="Select a text":
            error = "Please select a text"
        else:     
            files = glob.glob('audio/*.flac')
            file = max(files, key=os.path.getctime)
            filename = file.split('.')[0].split('/')[1]
            ext = file[-5:]
        if ext != ".flac":
            error = "Only .flac file accepted. Plese select another file"
        else:  
            patient_name = patient_name[0].upper()+patient_name[1:].lower()
            patient_surname = patient_surname[0].upper()+patient_surname[1:].lower()
            typeoffile = 'audio/flac'
                
            file_name = (str(patient_cf)
                         +str(session['id'])
                         +str(Transcriptions.query.filter_by(supervisor_id=session['id']).count())
                         +ext)
            
            shutil.copy2(file, app.config['UPLOAD_FOLDER'])
            os.rename(os.path.join(app.config['UPLOAD_FOLDER'], file.split('/')[1]), os.path.join(app.config['UPLOAD_FOLDER'], file_name))
            
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
            
            q = Patients.query.filter_by(cf = patient_cf).first()
            if not q:
                new_patient = Patients(patient_cf, patient_name, patient_surname, patient_bday, patient_gender)
                db.session.add(new_patient)
                db.session.commit()
            #os.rename(os.path.join(app.config['UPLOAD_FOLDER'], file), os.path.join(app.config['UPLOAD_FOLDER'], file_name))
            #filename = file.split('/')[1]
            uploadTask.delay(session['id'], patient_cf, text_title, file_name, os.path.join(app.config['UPLOAD_FOLDER'], file_name), typeoffile)

            
            return redirect(url_for('analyzed_audios'))
    return render_template('audio_upload.html', error=error, texts=texts)

@app.route('/audio_upload', methods=["GET", "POST"])
@is_logged_in
def audio_upload():
    from difflib import ndiff
    import glob

    error = None
    texts = Working_texts.query.all()

    if request.method == "POST":
        patient_name = request.form['patient_name']
        patient_surname = request.form['patient_surname']
        patient_bday = request.form['birthday']
        patient_cf = request.form['patient_id']
        patient_gender = request.form['gender']
        text_title = request.form.get('text_select')


        if patient_name == None or patient_name == '':
            error = "Please insert a patient name"
        elif patient_surname == None or patient_surname == '':
            error = "Please insert a patient surname"
        elif patient_cf == None or patient_cf == '':
            error = "Please insert a patient id"
        elif text_title =="Select a text":
            error = "Please select a text"
        else:     
            filename, ext = os.path.splitext(request.files.get('audio_file').filename) 
            if ext != ".flac":
                error = "Only .flac file accepted. Plese select another file"
            else:  
                file = request.files.get('audio_file')
                patient_name = patient_name[0].upper()+patient_name[1:].lower()
                patient_surname = patient_surname[0].upper()+patient_surname[1:].lower()
                typeoffile =  request.files.get('audio_file').content_type     
                file = request.files.get('audio_file')

                
                file_name = (str(patient_cf)
                             +str(session['id'])
                             +str(Transcriptions.query.filter_by(supervisor_id=session['id']).count())
                             +ext)

                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))

                
                q = Patients.query.filter_by(cf = patient_cf).first()
                if not q:
                    new_patient = Patients(patient_cf, patient_name, patient_surname, patient_bday, patient_gender)
                    db.session.add(new_patient)
                    db.session.commit()

                uploadTask.delay(session['id'], patient_cf, text_title, file_name, os.path.join(app.config['UPLOAD_FOLDER'], file_name), typeoffile)

                
                return redirect(url_for('analyzed_audios'))
    return render_template('audio_upload.html', error=error, texts=texts)


@celery.task
def uploadTask(user_id, patient_cf, text_title, file_name, file, content_type):
    
    text_title = Working_texts.query.filter_by(title=text_title, outdated=0).first()
   
    if DEBUG:
        with open("transcription.txt", "r") as ft, open("offsets.txt", "r") as fo:
            offsets = json.load(fo)
            transcription = ft.read()
    else:
        with open(file, "rb") as af:
            print('Uploading file')
            audio_url = upload_file(
                        af.read(),
                        file_name,
                        content_type
                        )
        
        #file_name = "DGRGRG10L21G273U14.flac"
        transcription, offsets, confidence = long_audio(f"gs://{BUCKET_NAME}/{file_name}", text_title.body.split())
    
    #print "Transcription:\n{}\n\nWord offsets:\n{}\n\nConfidence: {}".format(transcription, offsets, confidence)

    #text_title = Working_texts.query.filter_by(title=text_title, outdated=0).first()
    date = datetime.now()
    now = date.strftime('%Y-%m-%d %H:%M:%S')
    new_transcription = Transcriptions(user_id, patient_cf, text_title.id, file_name, transcription, now)
    db.session.add(new_transcription)
    db.session.flush()
    db.session.refresh(new_transcription)
    nt_id = new_transcription.id
    db.session.commit()

    difflist  = diff_t(transcription, nclean(text_title.body.lower()))
    wrong_t   = get_extensions(difflist)
    diff_orig = get_errors(difflist)

    difflist = [{'word': x[2:], 'ext': x[0]} for x in difflist]

    for i in range(len(wrong_t)):
        if wrong_t[i]['word'][0] == ' ' or wrong_t[i]['word'][0] == '+':
            difflist[wrong_t[i]['pos']]['time'] = offsets[i]['start']

    with open('difflist.txt', mode='w') as F:
        json.dump(difflist, F)
    with open('diff_orig.txt', mode='w') as F:
        json.dump(diff_orig, F)

    tot = 0.
    flag = False
    for i in range(len(difflist)):

        if i>0:
            if difflist[i]['ext']!=' ':
                err_type = "Sostituzione"
                #print "Error! word: {}, time: {}".format(difflist[i]['word'].encode('utf-8'), difflist[i-1]['time'])
                difflist[i]['time'] = difflist[i-1]['time']
                if difflist[i]['ext']=='-':
                    if not flag:
                        j=i+1
                        while j<len(difflist):
                            if difflist[j]['ext']!='-':
                                if difflist[j]['ext']==' ':
                                    err_type = "Omissione"
                                break
                            j+=1

                        try:
                            pos_err_word = diff_orig.index({'word': "- "+difflist[i]['word'], 'pos':i})
                            id_err_word = Text_words.query.filter_by(text=text_title.id, position=pos_err_word).first()
                            new_error = Errors(id_err_word.id+1, nt_id, difflist[i-1]['time'], False, err_type, False)
                            db.session.add(new_error)
                            db.session.commit()
                            flag = True
                        except Exception as e:
                            print(f"Missing: {difflist[i]['word']}",e)
                elif difflist[i]['ext']=='+':
                    if not flag:
                        j=i-1
                        while j>=0:
                            if difflist[j]['ext']!='+':
                                if difflist[j]['ext']==' ':
                                    err_type = "Ripetizione/Aggiunta"
                                break
                            j-=1
                        try:
                            pos_err_word=diff_orig.index({'word': "  "+difflist[i-1]['word'], 'pos':i-1})
                            id_err_word = Text_words.query.filter_by(text=text_title.id, position=pos_err_word).first()
                            new_error = Errors(id_err_word.id+1, nt_id, difflist[i-1]['time'], False, err_type, False)
                            db.session.add(new_error)
                            db.session.commit()
                            flag = True
                        except Exception as e:
                            print(f"Missing: {difflist[i]['word']}",e)
            else:
                if flag: 
                    tot += difflist[i]['time']-difflist[i-1]['time']
                try:
                    pos_err_word = diff_orig.index({'word': "  "+difflist[i]['word'], 'pos':i})
                    id_right_word = Text_words.query.filter_by(text=text_title.id, position=pos_err_word+1).first()
                    if id_right_word:
                        new_pword = Spoken_words(id_right_word.id, nt_id, i, difflist[i]['time'])
                        db.session.add(new_pword)
                        db.session.commit()
                    flag = False
                except Exception as e:
                    print(f"Missing: {difflist[i]['word']}",e)


        else:
            if difflist[i]['ext']!=' ':
                difflist[i]['time'] = 0
                if difflist[i]['ext']=='-':                        
                    try:
                        pos_err_word = diff_orig.index({'word': "- "+difflist[i]['word'], 'pos':i})
                        id_err_word = Text_words.query.filter_by(text=text_title.id, position=pos_err_word).first()
                        new_error = Errors(id_err_word.id+1, nt_id, 0)
                        db.session.add(new_error)
                        db.session.commit()
                        flag = True
                    except Exception as e:
                        print(f"Missing: {difflist[i]['word']}",e)
            else:
                try:
                    pos_err_word = diff_orig.index({'word': "  "+difflist[i]['word'], 'pos':i})
                    print(pos_err_word)
                    id_right_word = Text_words.query.filter_by(text=text_title.id, position=pos_err_word+1).first()
                    new_pword = Spoken_words(id_right_word.id, nt_id, i, difflist[i]['time'])
                    db.session.add(new_pword)
                    db.session.commit()
                except Exception as e:
                    print(f"Missing: {difflist[i]['word']}",e)

    print("Tempo di ascolto: {}, tempo totale: {}, percentuale: {}".format(tot, offsets[-1]['end'], tot/(offsets[-1]['end'])*100))
        

@app.route('/uploaded_texts', methods=["GET", "POST"])
def uploaded_texts():
    texts = Working_texts.query.filter_by(outdated=False).all()
    return render_template('uploaded_texts.html', texts=texts)


@app.route('/edit_text/<string:id>', methods=["GET", "POST"])
@is_logged_in
def edit_text(id):
    text = Working_texts.query.filter_by(id=id).first()
    user = session['id']
    if request.method == "POST":
        '''
            implementa funzione di creazione nuovo testo e modifica outdate, o cancella vecchio se non esiste trascrizione legata
        '''
        if Transcriptions.query.filter_by(text_id=id).first() != None:
            q = Working_texts.query.filter_by(id=id).first()
            q.outdated = 1
            db.session.commit()
            text_info = (q.title, request.form['mod_text'], q.font, q.schoolyear, q.period, q.dictation, q.filename)
            
            text_upload_task.delay(text_info, [], user, '')
        else:

            print(request.form['mod_text'])
            Text_words.query.filter_by(text=id).delete()
            q = Working_texts.query.filter_by(id=id).first()
            text_info = (q.title, request.form['mod_text'], q.font, q.schoolyear, q.period, q.dictation, q.filename)
            text_upload_task.delay(text_info, [], user, '')
            Working_texts.query.filter_by(id=id).delete()
            db.session.commit()
        return redirect(url_for('uploaded_texts'))

    return render_template('edit_text.html', text=text)


@app.route('/delete_text/<string:id>', methods=["GET", "POST"])
@is_logged_in
def delete_text(id):

    #set outdated to true o se nessuna trascrizione legata a testo delete
    if Transcriptions.query.filter_by(text_id=id).first() != None:
        q = Working_texts.query.filter_by(id=id).first()
        q.outdated = 1
        db.session.commit()
        #print("ciao")
    else:
        #print("ciao")
        Text_words.query.filter_by(text=id).delete()
        Working_texts.query.filter_by(id=id).delete()
        db.session.commit()
    return redirect(url_for('uploaded_texts'))


@app.route('/read_text/<string:id>')
def read_text(id):
    text = Working_texts.query.filter_by(id=id).first()
    if os.path.exists(f'{text.title}.txt'):
        with open(f'{text.title}.txt', 'r+') as file:
            file.truncate(0)
    return render_template('read_text.html', text=text)

times = []

@app.route('/add_time/<string:time>')
@is_logged_in
def add_time(time):
    if '.' in time:
        time = time[:time.find('.') + 4]
    global times
    times.append(time)
    return render_template('text_upload.html') 

@app.route('/text_upload/', methods=["GET", "POST"])
@is_logged_in
def text_upload():
    from pathlib2 import Path
    error=''
    classes = ["3a elementare", "4a elementare", "5a elementare", "1a media", "2a media", "3a media", "Adulti"]
    if request.method == "POST":
        text_title = request.form['text_title']
        text_body = request.form['textarea']
        text_font = request.form['text_font']
        text_schoolyear = request.form['class']
        text_period = request.form['period']
        dictation = int(request.form['dictation'])
        filename = request.form['changeselection']
        
        #text_cont = get_font_param(text_body)
        #get_string_tlength(text_cont)

        if text_title==None or text_title=='':
            error="Please fill all the fields"
        elif text_font == 'Select a font':
            error="Please fill all the fields"
        elif len(text_body) <= 30:
            error="Please fill all the fields"
        else:
            text_info = (text_title, text_body, text_font, text_schoolyear, text_period, dictation, filename)
            #time = '1'
            user = session['id']
            global times
            text_upload_task.delay(text_info, times, user, filename)

            return redirect(url_for('analyzed_audios'))
    return render_template('text_upload.html', error=error, classes=classes)


@celery.task
def text_upload_task(text_info, times_up, user, filename):
    text_title, text_body, text_font, text_schoolyear, text_period, dictation, filename = text_info
    date = datetime.now()
    now = date.strftime('%Y-%m-%d %H:%M:%S')
    new_text = Working_texts(text_title, text_body, text_font, text_schoolyear, text_period, now, dictation, filename)
    with open("static/words_italian.txt", "r") as f:
        it_words = f.readlines()
    for line in range(len(it_words)):
        it_words[line] = it_words[line][:-1]
    db.session.add(new_text)
    db.session.commit()
    wdict = {"word": None, }

    text_lines = nclean(text_body).splitlines()
    count = 1
    q = Working_texts.query.filter_by(title = text_title).first()
    for i in range(len(text_lines)):
        text_words = text_lines[i].split()
        for w in range(len(text_words)):
            qw = Words.query.filter_by(word=text_words[w].lower()).first()
            if qw==None:
                qw = Words(text_words[w].lower())
                db.session.add(qw)
                db.session.commit()
                db.session.refresh(qw)
                for sim_w in it_words:
                    sim_ratio = ratio(text_words[w].lower(), sim_w.lower())
                    #sim_ratio = ratio(w.lower().encode('utf-8'), sim_w.encode('utf-8').lower())
                    if  sim_ratio>0.85 and sim_ratio<1:
                        sim_ratio = int(sim_ratio * 1000) / 1000
                        new_w = Words.query.filter_by(word=sim_w).first()
                        if new_w == None:
                            new_w = Words(sim_w)
                            db.session.add(new_w)
                            db.session.commit()
                            db.session.refresh(new_w)
                        db.session.add(Similar_words(qw.id, new_w.id, sim_ratio))
                        db.session.commit()
            new_tword = Text_words(qw.id, count, q.id, i+1)
            count += 1
            db.session.add(new_tword)
            db.session.commit()
            if len(times_up) > 0:
                db.session.add(Written_words(user, filename, q.id, new_tword.id, times_up[w]))
                db.session.commit()
            if w == len(text_words):
                db.session.add(Written_words(user, filename, q.id, new_tword.id, times_up[w + 1]))
                db.session.commit()
    global times
    times.clear();
        

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('home'))


@app.route('/workbench_<string:id>')
@is_logged_in
def workbench(id):
    from pathlib2 import Path

    data = []
    w_time = None
    q = Transcriptions.query.filter_by(id=id).first()
    patient = Patients.query.filter_by(cf=q.patient_id).first()
    read_text = Working_texts.query.filter_by(id=q.text_id).first()
    text_words = db.session.query(Text_words, Words).filter_by(text=q.text_id).join(Words, Words.id==Text_words.word).add_columns(Text_words.id, Text_words.position, Text_words.row, Words.word).order_by(Text_words.position).all()
    text_words2 = [text_words[0]]
    for i in range(1, len(text_words)):
        if text_words[i].word != text_words[i - 1].word:
            text_words2.append(text_words[i])
                
    transcriptions = (db.session.query(Transcriptions, Patients)
                      .filter_by(supervisor_id=session['id'])
                      .outerjoin(Patients, Patients.cf==Transcriptions.patient_id)
                      .add_columns(Patients.cf, Patients.name, Transcriptions.update_date, Transcriptions.id)
                      .all())

    err_count=0
    for w in text_words2:
        error = Errors.query.filter_by(transcription=id, word=w.id).first()
        selected = "False"
        isError = "False"
        checked = "False"
        list_probs = []
        count = 1
     

        if error!=None:
            err_count +=1
            w_id = Text_words.query.filter_by(id=w.id).first()
            sim_words = Similar_words.query.filter_by(word1=w_id.word).all()
            for word in sim_words:
                sim_ratio = int(word.sim_ratio * 1000) / 1000
                db.session.add(Prob_words(word.word2, error.id, sim_ratio, False))
                db.session.commit()
            prob_words = Prob_words.query.filter_by(error=error.id).all()
            isError = True
            w_time = error.time
            
            for p in prob_words:
                if p.selected == 1:
                    selected = "True"
                actual_word = Words.query.filter_by(id=p.word).first()
                list_probs.append({'id': p.id, 'num': count, 'word': actual_word.word, 'prob': p.probability, 'sel': selected})

            data.append({"id": w.id, 'pos': w.position, 'word': w.word, 'time': w_time, 'row': w.row, 'isError': True, 'prb_wrds': list_probs, 'err_type': error.type_e,
                     'err_weight': error.weight, 'autocorr': error.autocorrection,'checked': error.checked})
            
        else:
            data.append({"id": w.id, 'pos': w.position, 'word': w.word, 'time': w_time, 'row': w.row, 'isError': False, 'prb_wrds': [], 
                     'err_type': None, 'err_weight': None, 'autocorr': None, 'checked': None})
        
    text_info = [{"title": "Testo", "val": read_text.title},
                 {"title": "Parole testo", "val": len(text_words2)}, 
                 {"title": "Errori trovati", "val": err_count}]
    
    my_path = Path("static/audio_files/"+q.filename)
    if not my_path.is_file():
        download_blob(BUCKET_NAME, q.filename, "static/audio_files/"+q.filename)

    return render_template('workbench.html', patient=patient, infos=text_info, transcription=q, prova=data, audio="static/audio_files/"+q.filename, rows=list(range(data[-1]['row']+1)), )


#//////////pagina in costruzione
'''
@app.route('/settings', methods=['GET', 'POST'])
@is_logged_in
def settings():
    error = ''
    if request.method == 'POST':

        session['adjacents'] = request.form['adjacents']
        session['simple'] = request.form['simpleHidden']
        session['lev'] = request.form['levHidden']

        return redirect('analyzed_audios')

    return render_template('settings.html', adjacents=session['adjacents'])

'''
@app.route('/errors_submission', methods=["GET", "POST"])
def errors_submission():
    if request.method == "POST":
        err = Errors.query.filter_by(word=request.form['w_id'], transcription=request.form['trans']).first()

        err.type_e = request.form['err_type']
        err.weight = request.form['err_weight']
        err.checked = 1
        if request.form['err_a'] == "true":
            err.autocorrection = 1
        else:
            err.autocorrection = 0

        err_w = Words.query.filter_by(word=request.form["err_w"]).first()
        if err_w==None:
            err_w = Words(request.form["err_w"])
            db.session.add(err_w)
            db.session.flush()
            db.session.refresh(err_w)

        err.err_w = err_w.id

        db.session.commit()

        print(err.checked)
        return jsonify(result="Query OK")


@app.route('/remove_error', methods=["GET", "POST"])
def remove_error():
    if request.method == "POST":
        print(request.form['w_id'])
        Errors.query.filter_by(word=request.form['w_id'], transcription=request.form['trans']).delete()
        db.session.commit()
        return jsonify(result="Query OK")







#////////////WTF-forms classes (form di sottomissione, es. login)
def available_username(form, field):
    result = Supervisors.query.filter_by(username=field.data).first()
    if result:
        raise validators.ValidationError('Username already in use.\n Please choose another')


class RegisterForm(Form):
    id = StringField('id', [validators.Length(min=1, max=50)])
    username = StringField('Username', [
        validators.Length(min=4, max=25),
        available_username,
        validators.DataRequired()
    ])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')











#/////////////classe del mapper del database
class Supervisors(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    e_mail = db.Column('email', db.Unicode)
    username = db.Column('username', db.Unicode)
    password = db.Column('password', db.Unicode)

    def __init__(self, name, e_mail, username, password):
        self.name = name
        self.e_mail = e_mail
        self.username = username
        self.password = password


class Patients(db.Model):
    __tablename__ = 'patients'
    cf = db.Column('cf', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    surname = db.Column('surname', db.String)
    birthday = db.Column('birthday', db.Unicode)
    gender = db.Column('gender', db.String)

    def __init__(self, cf,  name, surname, birthday, gender):
        self.cf = cf
        self.name = name
        self.surname = surname
        self.birthday = birthday
        self.gender = gender


class Transcriptions(db.Model):
    __tablename__ = 'transcriptions'
    id = db.Column('id', db.Integer, primary_key=True)
    supervisor_id = db.Column('supervisor_id', db.Integer, db.ForeignKey('users.id'))
    patient_id = db.Column('patient_id', db.Integer, db.ForeignKey('patients.cf'))
    text_id = db.Column('text_id', db.Integer, db.ForeignKey('texts.id'))
    filename = db.Column('filename', db.String)
    transcription = db.Column('body', db.Text)
    update_date = db.Column('update_date', db.DateTime)

    def __init__(self, supervisor_id, patient_id, text_id, filename, transcription, update_date):
        self.supervisor_id = supervisor_id
        self.patient_id = patient_id
        self.text_id = text_id
        self.filename = filename
        self.transcription = transcription
        self.update_date = update_date


class Working_texts(db.Model):
    __tablename__ = 'texts'
    id = db.Column('id', db.Integer, primary_key=True)
    title = db.Column('title', db.String)
    body = db.Column('body', db.Text)
    font = db.Column('font', db.String)
    update_date = db.Column('update_date', db.DateTime)
    schoolyear = db.Column('class', db.Integer)
    period = db.Column('period', db.String)
    dictation = db.Column('dictation', db.Boolean, default=False)
    filename = db.Column('filename', db.String)
    outdated = db.Column('outdated', db.Boolean, default=False)

    def __init__(self, title, body, font, schoolyear, period, update_date, dictation, filename):
        self.title = title
        self.body = body
        self.font = font
        self.schoolyear = schoolyear
        self.period = period
        self.update_date = update_date
        self.dictation = dictation
        self.filename = filename


class Text_words(db.Model):
    __tablename__ = 'text_words'
    id = db.Column('id', db.Integer, primary_key=True)
    word = db.Column('word', db.Integer)
    position = db.Column('position', db.Integer)
    text = db.Column('text', db.Integer)
    row = db.Column('row', db.Integer)

    def __init__(self, word, position, text, row):
        self.word = word
        self.position = position
        self.text = text
        self.row = row


class Errors(db.Model):
    __tablename__ = 'errors'
    id = db.Column('id', db.Integer, primary_key=True)
    word = db.Column('text_word', db.Integer)
    type_e = db.Column('type', db.String)
    transcription = db.Column('transcription', db.Integer)
    err_w = db.Column('err_w', db.Integer, default=None)
    time = db.Column('time', db.Float)
    weight = db.Column('weight', db.Float)
    autocorrection = db.Column('autocorrection', db.Boolean)
    checked = db.Column('checked', db.Boolean)

    def __init__(self, word, transcription, time, checked=False, type_e=None, autocorrection=False):
        self.word = word
        self.transcription = transcription
        self.time = time
        self.checked = checked
        self.autocorrection=autocorrection
        self.type_e = type_e



class Words(db.Model):
    __tablename__ = 'words'
    id = db.Column('id', db.Integer, primary_key=True)
    word = db.Column('word', db.String)
    wtype = db.Column('type', db.String)

    def __init__(self, word, wtype=''):
        self.word = word
        self.wtype = wtype


class Similar_words(db.Model):
    __tablename__ = 'sim_words'
    id = db.Column('id', db.Integer, primary_key=True)
    word1 = db.Column('word1', db.Integer)
    word2 = db.Column('word2', db.Integer)
    sim_ratio = db.Column('ratio', db.Float)

    def __init__(self, word1, word2, sim_ratio):
        self.word1 = word1
        self.word2 = word2
        self.sim_ratio = sim_ratio


class Prob_words(db.Model):
    __tablename__ = 'prob_words'
    id = db.Column('id', db.Integer, primary_key=True)
    word = db.Column('word', db.Integer)
    error = db.Column('error', db.Integer)
    probability = db.Column('probability', db.Float)
    selected = db.Column('selected', db.Boolean)

    def __init__(self, word, error, probability, selected=False):
        self.word = word
        self.error = error
        self.probability = probability
        self.selected = selected

class Spoken_words(db.Model):
    __tablename__ = 'spoken_words'
    id = db.Column('id', db.Integer, primary_key=True)
    text_word = db.Column('text_word', db.Integer)
    transcription = db.Column('transcription', db.Integer)
    pos = db.Column('pos', db.Integer)
    time = db.Column('time', db.Float)

    def __init__(self, text_word, transcription, pos, time):
        self.text_word = text_word
        self.transcription = transcription
        self.pos = pos
        self.time = time

class Highlighted_words(db.Model):
    __tablename__ = 'highlighted_words'
    id = db.Column('id', db.Integer, primary_key=True)
    user = db.Column('user', db.Integer)
    user_time = db.Column('user_time', db.Integer)
    text = db.Column('text', db.Integer)
    text_word = db.Column('text_word', db.Integer)
    index = db.Column('index', db.Integer)
    time = db.Column('time', db.Float)
    
    def __init__(self, user, user_time, text, text_word, index, time):
        self.user = user
        self.user_time = user_time
        self.text = text
        self.text_word = text_word
        self.index = index
        self.time = time
        
class Written_words(db.Model):
    __tablename__ = 'written_words'
    id = db.Column('id', db.Integer, primary_key=True)
    user = db.Column('user', db.Integer)
    filename = db.Column('filename', db.String)
    text = db.Column('text', db.Integer)
    text_word = db.Column('text_word', db.Integer)
    time = db.Column('time', db.Float)
    
    def __init__(self, user, filename, text, text_word, time):
        self.user = user
        self.filename = filename
        self.text = text
        self.text_word = text_word
        self.time = time

class Audio_files(db.Model):
    __tablename__ = 'audio_files'
    id = db.Column('id', db.Integer, primary_key=True)
    filename = db.Column('filename', db.String)
    text = db.Column('text', db.Text)
    
    def __init__(self, filename, text):
        self.filename = filename
        self.text = text


          

if __name__== '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    #app.run(debug=True)
