import difflib
import pdfkit
from wams import app, socketio
from flask import render_template, redirect, url_for, jsonify, flash, request, json, make_response
from wams.db import db
from wams.db import question, user_info, Etiquettes, questionnaire, archive
from wams.forms import Form, FormInscription, FormConnexion, FormChangerPassword, FormPoserQuestionOuverte, FormRepondreQuestionOuverte
import os
import csv
import random, string
from datetime import date
from flask_login import login_user, logout_user, current_user, login_required
from flask_socketio import emit, send
import markdown
import math
from itertools import combinations, product, islice
from wordcloud import WordCloud
import re
from collections import Counter


globalTags=[] #étiquettes par défaut
roomOuvertes={} #dictionnaire contenant toutes les diffusions de question avec la question associée
questionnairesOuverts={} #dictionnaire contenant toutes les diffusions de séquences avec a liste des questions associée
indiceQuestion={} #pour savoir à quelle question en est chaque diffusion de séquence
testDeLaComOMG=[]
dicoHosts={} #répertorie les hosts pour chaque diffusion de question
dicoHostsS={} #répertorie les hosts pour chaque diffusion de séquence
dicoReponsesQuestions={} #répertorie toutes les réponses envoyées par les participants dans une diffusion de question
dicoReponsesSequences={} #répertorie toutes les réponses envoyées par les participants dans une diffusion de séquence
participantsQuestions={} #répertorie tous les participants de chaque diffusion de question
participantsSequences={} #répertorie tous les participants de chaque diffusion de séquence
estStoppeeQuestion={} #pour savoir si une question est arrêtée quand un participant arrive
estCorrigeeQuestion={} #pour savoir si une question est corrigee
estStoppeeSequence={} #pour séquence
estCorrigeeSequence={}
controles={}

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

globalTags=["Web", "Java", "Arithmétique", "Graphes"]
engine = create_engine('sqlite:///instance/wams.db?check_same_thread=False')
connection = engine.connect()
print(engine.table_names())
metadata = MetaData()
Session = sessionmaker(bind=engine)
session = Session()
questionnaireTable = Table("questionnaire", metadata, autoload=True, autoload_with=engine)


@socketio.on('typing')
def typing(data):
    emit("formatted", data)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/pagesQuestion', methods=['GET', 'POST'])
def pagesQuestion():
    return render_template('pagesQuestion.html', questions=question.query.all(), globalTags=globalTags, len=len(globalTags), len9 = len(globalTags) if len(globalTags)<9 else 9)# listeTags = listeTags, lenTags = len(listeTags))

@app.route('/pagesQuestionWaitingRoom', methods=['GET', 'POST'])
def pagesQuestionWaitingRoom():
    listeTags = json.loads(request.data)["listeTags"]
    print(listeTags)
    strTags = json.loads(request.data)["strTags"]
    print(strTags)
    return render_template("pagesQuestion.html", questions=question.query.all(), globalTags=globalTags, len=len(globalTags), len9=len(globalTags) if len(globalTags)<9 else 9, listeTags=listeTags, strTags=strTags)

@app.route('/pageQuestionnaires', methods=['GET', 'POST'])
def pageQuestionnaires():
    print(questionnaire.query.all())
    return render_template("pageQuestionnaires.html", questionnaires=questionnaire.query.all())

isChecked = False

@app.route('/oneAnswer', methods=['GET', 'POST'])
def oneAnswer():
    global isChecked
    isChecked = not(isChecked)
    return redirect(url_for('editeur'))

@app.route('/editeur', methods=['GET', 'POST'])
def editeur():
    for tag in Etiquettes.query.all():
        if not(tag.id in globalTags): #Initialise les étiquettes de base
            globalTags.append(tag.id)
    AllQuestion = question.query.all()
    form = Form()
    if form.validate_on_submit():
        Label = form.Label.data
        Etiquette = form.Etiquette.data
        Questiondata = form.Question.data
        Réponse1 = form.Réponse1.data
        Réponse2 = form.Réponse2.data
        Réponse3 =form.Réponse3.data
        Réponse4 = form.Réponse4.data
        bonne_reponse = form.bonne_reponse.data

        listNewTags = Etiquette.split(",")
        for i in range(len(listNewTags)) :
            if not bool(Etiquettes.query.filter_by(id=listNewTags[i]).first()):
                if not (listNewTags[i] == ""): #Ajout des étiquettes submit à la db sans doublon
                    newTag = Etiquettes(id=listNewTags[i])
                    db.session.add(newTag)
                    db.session.commit()
                
        for tag in Etiquettes.query.all():
            if not bool(Etiquettes.query.filter_by(id=tag.id).first()):
                if not (tag.id == ""): #Ajout des nouvelles étiquettes de la db dans une liste envoyée au html
                    globalTags.append(tag.id)
        
        if not(isChecked):
            print("erreur", isChecked)
            if not Label.strip() or not Etiquette.strip() or not Questiondata.strip() or not Réponse1.strip() or not Réponse2.strip() or not Réponse3.strip() or not Réponse4.strip():
                raise ValueError("Les champs ne peuvent pas être vides ou remplis d'espaces uniquement.")

        Questionfilter = question.query.filter_by(Label=Label).first()

        if Questionfilter:
            Questionfilter.Etiquette = Etiquette
            Questionfilter.Question = Questiondata
            Questionfilter.Réponse1 = Réponse1
            Questionfilter.Réponse2 = Réponse2
            Questionfilter.Réponse3 = Réponse3
            Questionfilter.Réponse4 = Réponse4
            Questionfilter.bonne_reponse = bonne_reponse
        else:
            QuestionToAdd = question(Label=Label, Etiquette=Etiquette, Question=Questiondata, Réponse1=Réponse1, Réponse2=Réponse2, Réponse3=Réponse3, Réponse4=Réponse4, bonne_reponse=bonne_reponse)
            db.session.add(QuestionToAdd)
            db.session.commit()
            return redirect(url_for('editeur'))
        db.session.commit()
    
    
    return render_template('editeur.html', form = form, question = AllQuestion, globalTags=globalTags, len=len(globalTags), len9 = len(globalTags) if len(globalTags)<9 else 9)

@app.route('/waitingRoom', methods=['GET', 'POST'])
def waitingRoom():
    return render_template('waitingRoom.html')

@app.route('/joinRoomQ', methods=['GET', 'POST'])
def joinRoomQ():
    codeRoom = request.json
    infosQuestion = roomOuvertes[codeRoom] if codeRoom in roomOuvertes.keys() else ""
    return {"codeRoom" : codeRoom, "infosQuestion" : infosQuestion}

@app.route('/diffusionQ/<codeRoom>', methods=['GET', 'POST'])
def diffusionQ(codeRoom):
    infosQuestion = request.args.get('infosQuestion')
    if infosQuestion is not None:
        infosQuestion = json.loads(request.args.get('infosQuestion'))
    if codeRoom in participantsQuestions.keys():
        if current_user.id not in participantsQuestions[codeRoom]:
            participantsQuestions[codeRoom].append(current_user.id)
            socketio.emit("nouveauParticipantQ", participantsQuestions)
    if codeRoom in roomOuvertes:
        return render_template('diffusionQuestion.html', existsRoom = codeRoom in roomOuvertes, codeRoom=codeRoom, roomOuvertes=roomOuvertes, infosQuestion=infosQuestion, Label=roomOuvertes[codeRoom]['Label'], 
                   Etiquette=roomOuvertes[codeRoom]['Etiquette'], 
                   Question=roomOuvertes[codeRoom]['Question'], 
                   Réponse1=roomOuvertes[codeRoom]['Reponse1'],
                   Réponse2=roomOuvertes[codeRoom]['Reponse2'],
                   Réponse3=roomOuvertes[codeRoom]['Reponse3'],
                   Réponse4=roomOuvertes[codeRoom]['Reponse4'],
                   Bonne_Réponse=roomOuvertes[codeRoom]['Bonne_Reponse'], isHost=isHost(codeRoom), userID=current_user.id, estStoppee=estStoppeeQuestion[codeRoom], estCorrigee=estCorrigeeQuestion[codeRoom])
    else:
        return render_template('diffusionQuestion.html', existsRoom = codeRoom in roomOuvertes)


@app.route('/updateDiffusionQuestion', methods=['POST'])
def updateDiffusionQuestion():
    codeRoomA = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    codeRoom = codeRoomA if codeRoomA not in roomOuvertes.keys() else updateDiffusionQuestion()
    infosQuestion = request.json
    roomOuvertes[codeRoom] = infosQuestion
    dicoHosts[codeRoom]=current_user.id
    dicoReponsesQuestions[codeRoom]=[]
    estStoppeeQuestion[codeRoom]=False
    estCorrigeeQuestion[codeRoom]=False
    participantsQuestions[codeRoom]=[]

    return codeRoom

@app.route('/deleteDiffusion', methods=['GET', 'POST'])
def deleteDiffusion():
    codeRoom = request.get_json()['codeRoom']
    roomOuvertes.pop(codeRoom, None)
    dicoHosts.pop(codeRoom, None)
    dicoReponsesQuestions.pop(codeRoom, None)
    estStoppeeQuestion.pop(codeRoom, None)
    estCorrigeeQuestion.pop(codeRoom, None)
    participantsQuestions.pop(codeRoom, None)
    return redirect(url_for("pagesQuestion"))

@app.route('/diffusionQuestionnaire/<codeRoomS>', methods=['GET', 'POST'])
def diffusionQuestionnaire(codeRoomS):
    q=json.loads(request.args.get("q"))
    if codeRoomS in participantsSequences.keys():
        if current_user.id not in participantsSequences[codeRoomS]:
            participantsSequences[codeRoomS].append(current_user.id)
            socketio.emit("nouveauParticipantS", participantsSequences)
    listeQ=[]
    for i in range(len(q)):
        listeQ.append(db.session.query(question).filter_by(Label=q[i]).first())
    return render_template("diffusionQuestionnaire.html", questionnairesOuverts=questionnairesOuverts, codeRoomS=codeRoomS, listeQ=listeQ, indiceQuestion=indiceQuestion[codeRoomS], isHostS=isHostS(codeRoomS), userIDS=current_user.id)

@app.route('/updateDiffusionQuestionnaire', methods=['POST'])
def updateDiffusionQuestionnaire():
    codeRoomSA = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    codeRoomS = codeRoomSA if codeRoomSA not in questionnairesOuverts.keys() else updateDiffusionQuestionnaire()
    temp=request.json
    tableQ=db.session.query(questionnaire).filter_by(id=temp).first()
    listeQ=[]
    for i in range(1, len(tableQ.__table__.columns)-1):
        column = f"Q{i}"
        listeQ.append(getattr(tableQ, column))
    questionnairesOuverts[codeRoomS] = listeQ
    indiceQuestion[codeRoomS] = 0
    dicoHostsS[codeRoomS] = current_user.id
    dicoReponsesSequences[codeRoomS]=[]
    participantsSequences[codeRoomS]=[]
    estStoppeeSequence[codeRoomS]=False
    estCorrigeeSequence[codeRoomS]=False
    print(questionnairesOuverts)
    return {"codeRoom" : codeRoomS, "listeQ" : listeQ}

@app.route('/joinRoomS', methods=['GET', 'POST'])
def joinRoomS():
    codeRoom = request.json
    infosQuestion = questionnairesOuverts[codeRoom] if codeRoom in questionnairesOuverts.keys() else ""
    return {"codeRoom" : codeRoom, "infosQuestion" : infosQuestion}

@app.route('/deleteDiffusionS', methods=['GET', 'POST'])
def deleteDiffusionS():
    codeRoomS = request.get_json()["codeRoomS"]
    questionnairesOuverts.pop(codeRoomS, None)
    dicoHostsS.pop(codeRoomS, None)
    dicoReponsesSequences.pop(codeRoomS, None)
    estStoppeeSequence.pop(codeRoomS, None)
    estCorrigeeSequence.pop(codeRoomS, None)
    return redirect(url_for("pageQuestionnaires"))

@app.route('/nextQ', methods=['GET', 'POST'])
def nextQ():
    codeRoomS = request.json
    indiceQuestion[codeRoomS]+=1
    estStoppeeSequence[codeRoomS]=False
    estCorrigeeSequence[codeRoomS]=False
    print(questionnairesOuverts[codeRoomS])
    return questionnairesOuverts[codeRoomS]

@app.route('/update/<int:id>', methods=['GET'])
def update(id):
    Question = question.query.get(id)
    return jsonify(Label=Question.Label, 
                   Etiquette=Question.Etiquette, 
                   Question=Question.Question, 
                   Réponse1=Question.Réponse1,
                   Réponse2=Question.Réponse2,
                   Réponse3=Question.Réponse3,
                   Réponse4=Question.Réponse4,
                   bonne_reponse=Question.bonne_reponse)

@app.route('/add', methods=['POST'])
def addQuestion():
    listeQuestions = request.get_json()['listeQuestions']
    x = len(questionnaireTable.columns)-2
    print(listeQuestions)
    print(len(listeQuestions))
    nbcolonnes = len(questionnaireTable.columns) - 2
    print(nbcolonnes)
    
    while len(listeQuestions) >= nbcolonnes:
        x +=1
        Column_name = f'Q{x}'

        print(Column_name)
        query = f'ALTER TABLE questionnaire ADD {Column_name};'
        connection.execute(query)
        nbcolonnes +=1
    
    new_questionnaire = questionnaire(Label=listeQuestions[0])
    listeQuestions.pop(0)
    for i in range(len(listeQuestions)):
        setattr(new_questionnaire, f"Q{str(i+1)}", listeQuestions[i])
    db.session.add(new_questionnaire)
    db.session.commit()
    return redirect(url_for('editeur'))

@app.route('/q/<id>', methods=['POST', 'GET'])
def q(id):
    allQuestionnaire = questionnaire.query.all()
    
    ligne_selectionnée = db.session.query(questionnaire).filter_by(id=id).first()
    print(ligne_selectionnée)
    labels = []
    sto = len(ligne_selectionnée.__table__.columns)
    print(sto)
    for i in range(1, len(ligne_selectionnée.__table__.columns)-1):
        column = f"Q{i}"
        value = getattr(ligne_selectionnée, column)
        if value:
            labels.append(value)
    questionsRows = db.session.query(question).filter(question.Label.in_(labels)).all()

    idQuestions = []
    labelQuestions = []
    for questionRow in questionsRows:
        idQuestions.append(questionRow.id)
        labelQuestions.append(questionRow.Label)
    print(idQuestions)
    


    return render_template('questionnaire.html', idQuestions = idQuestions, labelQuestions= labelQuestions)

@app.route('/quest/<int:id>', methods=['POST', 'GET'])
def quest(id):
    Question = question.query.get(id)
    bonnesReps = question.query.with_entities(question.bonne_reponse)
    bonneRep = str(bonnesReps[id-1]).strip("()',").replace("\\n", "\n").replace("\\r", "")
    print(bonneRep)

    reponse = request.form.get('reponses')
    print(reponse)
    
    if reponse == bonneRep:
        login_user = current_user.login_user
        flash("Bonne réponse !", category='success')
    elif (request.form.get('reponses') == None) :
        flash("Veuillez répondre à la question", category='danger')
    else:
        login_user = current_user.login_user
        flash("Mauvaise réponse !", category='danger')
    return render_template('question.html', Label=Question.Label, 
                   Etiquette=Question.Etiquette, 
                   Question=Question.Question, 
                   Réponse1=Question.Réponse1,
                   Réponse2=Question.Réponse2,
                   Réponse3=Question.Réponse3,
                   Réponse4=Question.Réponse4,
                   Bonne_Réponse=Question.bonne_reponse)
@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if form.validate_on_submit():
        user_to_create = user_info(login_user=form.username.data,
                                    mail_user = form.mail.data,
                                    password = form.password1.data,
                                    prof_user = 1)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('connexion'))
    if form.errors != {}:
        for errors in form.errors.values():
            flash(f'Erreur : {errors}', category='danger')
    return render_template('inscription.html', form=form)

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    archivesto = archive(user = "Simon", réponse = "Test", date = date.today(), typeQuestion = "typeQuestion")
    db.session.add(archivesto)
    db.session.commit()
    print("HEOHHHHHHHHHHHHHHHHHHHHHO")
    return render_template('stats.html', stats = archive.query.all())

@app.route('/changerPassword', methods=['GET', 'POST'])
def changerPassword():
    form = FormChangerPassword()
    print("mdp user :", current_user.password_user)
    if form.validate_on_submit():
        user_to_create = user_info(password = form.password1.data)
        user = user_info.query.filter_by(login_user=current_user.login_user).first()
        user.password_user = user_to_create.password_user
        db.session.add(user)
        db.session.commit()
    if form.errors != {}:
        for errors in form.errors.values():
            flash(f'Erreur : {errors}', category='danger')
    return render_template('changePassword.html', form=form)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if not current_user.is_authenticated:
        form = FormConnexion()
        if form.validate_on_submit():
            passed_user = user_info.query.filter_by(login_user=form.username.data).first()
            if passed_user and passed_user.check_password_correction(passed_password = form.password.data):
                login_user(passed_user)
                # flash(f"Connection réussie sous l'username {passed_user.login_user}", category='success')
                return redirect(url_for('editeur'))
            else:
                flash(f"Erreur, le nom d'utilisateur ne correspond pas au mot de passe !", category='danger')
        return render_template('connexion.html', form=form)
    else: return "Vous êtes déjà connecté !"

@app.route('/deconnexion', methods=['GET', 'POST'])
def deconnexion():
    logout_user()
    flash("Deconnexion réussie !", category='info')
    return redirect(url_for('editeur'))

@app.route('/creerAllComptes', methods=["GET", "POST"])
def creerAllComptes():
    if (current_user.prof_user == 1):
        form = FormInscription()
        if request.method == 'POST':
            if request.files:
                uploaded_file = request.files['filename']
                filepath = os.path.join(app.config['FILE_UPLOADS'], uploaded_file.filename)
                uploaded_file.save(filepath)
                with open(filepath) as file:
                    csv_file = csv.reader(file)
                    for data in csv_file:
                        user_to_create = user_info(login_user=f"{data[0]}{data[1]}",
                                                    mail_user = "",
                                                    password = data[2],
                                                    prof_user = 0)
                        db.session.add(user_to_create)
                        db.session.commit()
        return render_template('creerAllComptes.html')
    else:
        return "Vous n'êtes pas prof"

degres_similitude = 0.5
reponses_salles = {}


@socketio.on('send_rep')
@app.route('/repondreQuestionOuv', methods=["GET", "POST"])
def repondreQuestionOuv():
    form = FormRepondreQuestionOuverte()
    if form.validate_on_submit():
        reponse = form.reponse.data
        room = form.code_room.data
        if not room in reponses_salles:
            reponses_salles[str(room)] = []
        else:
            reponse_clean = reponse.strip().lower()

            prefixes = ["in", "a", "de"]  # Liste des prefixes à vérifier
            best_match = difflib.get_close_matches(reponse_clean, reponses_salles[str(room)], 1, degres_similitude)
            if len(best_match) > 0:
                for prefixe in prefixes:
                    if reponse_clean.startswith(prefixe) and not best_match[0].startswith(prefixe):
                        # Si les deux n'ont pas le même préfixes
                        reponses_salles[str(room)].append(reponse_clean)
                        break
                    else:
                        reponses_salles[str(room)].append(best_match[0])
                        break
            else:
                reponses_salles[str(room)].append(reponse_clean)

        print(f"Reponse de la salle {room} : {reponses_salles[str(room)]}")
    return render_template("repondreQuestionOuv.html", form=form)


@app.route('/poserQuestionOuv', methods=["GET", "POST"])
def poserQuestionOuv():
    form = FormPoserQuestionOuverte()
    if form.validate_on_submit():
        if request.method == 'POST' and request.form.get('submit'):
            print("ok")
            question_ouverte = form.question_ouverte.data
            room = form.code_room.data
            socketio.emit('send_question2', {
                          "question_ouverte": question_ouverte, "room": room})
            print("Question envoyée: ", question_ouverte, room)
        elif request.method == 'POST' and request.form.get('nuage'):
            room = form.code_room.data
            nb_rep = Counter(reponses_salles[str(room)])
            wc = WordCloud(width=800, height=400, background_color="rgba(255, 255, 255, 0)",
                           mode="RGBA").generate_from_frequencies(nb_rep)
            wc.to_file('./wams/static/nuagemot-'+room+'.png')
            socketio.emit('update_nuagemot', {"room": room})

    return render_template("poserQuestionOuv.html", form=form)


@app.route('/controle', methods=["GET", "POST"])
def controle():
    listeEtiquettes=[]
    dicoQuestionsParTag1={}
    for etiquette in Etiquettes.query.all():
        listeEtiquettes.append(etiquette.id)
        dicoQuestionsParTag1[etiquette.id]=[]
        for quest in question.query.all():
            if etiquette.id == quest.Etiquette.split(",")[0]:
                dicoQuestionsParTag1[etiquette.id].append(quest)
    print(dicoQuestionsParTag1)
    return render_template('controle.html', listeEtiquettes=listeEtiquettes, dicoQuestionsParTag1=dicoQuestionsParTag1)


def archivage(user, réponse, typeQuestion):
    archivesto = archive(user = user, réponse = réponse, date = date.today(), typeQuestion = typeQuestion)
    db.session.add(archivesto)
    db.session.commit()


def isHost(code):
    return current_user.id == dicoHosts[code]

def isHostS(code):
    return current_user.id == dicoHostsS[code]

@socketio.on('EnvoieReponse')
def archivageReponseQuestion(reponse):
    archivage(current_user.login_user, reponse["bouton"], "question")
    dicoReponsesQuestions[reponse["room"]].append(reponse["bouton"])
    emit('envoieDico', {"dicoReponsesQuestion": dicoReponsesQuestions, "dicoHost" : dicoHosts, "rep" : reponse["bouton"]}, broadcast=True)

@socketio.on('CorrectionQuestion')
def CorrectionQuestion(reponse):
    estStoppeeQuestion[reponse["code"]]=True
    if reponse["estCorrec"]:
        estCorrigeeQuestion[reponse["code"]]=True
    emit('envoieCorrectionQuestion', {"correction" : reponse["estCorrec"], "code" : reponse["code"]}, broadcast=True)


@socketio.on('EnvoieReponseS')
def envoieReponseS(reponse):
    archivage(current_user.login_user, reponse["bouton"], "sequence")
    print("comm réussie", reponse["room"])
    dicoReponsesSequences[reponse["room"]].append(reponse["bouton"])
    emit('envoieDicoS', {"dicoReponsesSequences": dicoReponsesSequences, "dicoHostS" : dicoHostsS, "rep" : reponse["bouton"]}, broadcast=True)

@socketio.on('nextQuestion')
def nextQuestion(reponse):
    dicoReponsesSequences[reponse["room"]]=[]
    emit('nextQ', reponse["lien"], broadcast=True)

@socketio.on('CorrectionSequence')
def CorrectionSequence(reponse):
    estStoppeeSequence[reponse["code"]]=True
    if reponse["estCorrec"]:
        estCorrigeeSequence[reponse["code"]]=True
    emit('envoieCorrectionSequence', {"correction" : reponse["estCorrec"], "code" : reponse["code"]}, broadcast=True)

@socketio.on('fourchetteQuestionsParTag')
def fourchetteQuestionsParTag(dico):
    global newResult
    totalPossibilités=1
    dicoQuestionsParTag1={}
    for etiquette in Etiquettes.query.all():
        dicoQuestionsParTag1[etiquette.id]=[]
        for quest in question.query.all():
            if etiquette.id == quest.Etiquette.split(",")[0]:
                dicoQuestionsParTag1[etiquette.id].append(quest)
    dicoComb={}
    nbTotal=0
    while nbTotal != int(dico["nbQuestions"]):
        nbTotal=0
        totalPossibilités=1
        for tag in dico["dictionnaireMinMax"]:
            dicoComb[tag]=[]
            nbQuest=random.randint(int(dico["dictionnaireMinMax"][tag][0]),int(dico["dictionnaireMinMax"][tag][1]))
            nbTotal+=nbQuest
            totalPossibilités=totalPossibilités*math.comb(int(dico["dictionnaireMinMax"][tag][2]), nbQuest)
            for comb in combinations(dicoQuestionsParTag1[tag], nbQuest):
                if list(comb)!=[]:
                    dicoComb[tag].append(list(comb))
    print("possibilités max : ", totalPossibilités)
    print(dicoComb)
    newDicoComb={}
    if not(dico["shuffleQuestions"]) :
        for i in dicoComb:
            random.shuffle(dicoComb[i])
            newDicoComb[i] = dicoComb[i]
        dicoComb=newDicoComb
    listes = [v for v in dicoComb.values() if isinstance(v, list) and len(v) > 0]
    produit = list(product(*listes))
    print(produit)

    resultat = []
    cptNbQuestions=0
    for tuple in produit:
        fusion = []
        if cptNbQuestions<int(dico["nbSujets"]):
            for liste in tuple:
                fusion.extend(liste)
            resultat.append(fusion)
            cptNbQuestions+=1
    print(int(dico["nbSujets"]))
    print(cptNbQuestions)
    print(resultat)
    newResult = []
    if dico["shuffleQuestions"] :
        for i in resultat:
            random.shuffle(i)
            newResult.append(i)

    else : newResult = resultat
    print(newResult)
    controles[current_user.id]=newResult
    emit('resultatcontroles', dico["estAnonyme"])


@app.route('/pdfcontrole/<estAnonyme>')
def pdfcontrole(estAnonyme):
    # anonyme=(estAnonyme=="true")
    # print(controles[current_user.id])
    # html = render_template('pdfcontrole.html', resultat=controles[current_user.id], anonyme=anonyme)
    # pdf = generate_pdf(html)
    # response = make_response(pdf)
    # response.headers['Content-Type'] = 'application/pdf'
    # response.headers['Content-Disposition'] = 'inline; filename=questionnaire.pdf'
    # return response



    anonyme=(estAnonyme=="true")
    print(controles[current_user.id])
    return render_template('pdfcontrole.html', resultat=controles[current_user.id], anonyme=anonyme)
    

from weasyprint import HTML
@app.route('/pdf')
def generate_pdf(html):
    pdf = HTML(string=html).write_pdf()
    return pdf


@socketio.on("convert")
def conversion(data):
    print("CONVERSIOOOOOOOOON")
    pdf = HTML(string=data).write_pdf()
    emit('pdf', pdf)
