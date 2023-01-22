from wams import app
from flask import render_template, redirect, url_for, jsonify, flash, request, json
from wams.db import db
from wams.db import question, user_info
from wams.forms import Form, FormInscription, FormConnexion

from flask_login import login_user, logout_user

globalTags=[]

from sqlalchemy import Column, String, create_engine, MetaData, Table
globalTags=["Web", "Java", "Arithmétique", "Graphes"]
engine = create_engine('sqlite:///instance/wams.db?check_same_thread=False')
connection = engine.connect()
print(engine.table_names())
metadata = MetaData()
questionnaireTable = Table("questionnaire", metadata, autoload=True, autoload_with=engine)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/pagesQuestion', methods=['GET', 'POST'])
def pagesQuestion():
    return render_template('pagesQuestion.html')

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
            if not bool(Etiquettes.query.filter_by(id=listNewTags[i]).first()): #Ajout des étiquettes submit à la db sans doublon
                newTag = Etiquettes(id=listNewTags[i])
                db.session.add(newTag)
                db.session.commit()
                
        for tag in Etiquettes.query.all():
            if not bool(Etiquettes.query.filter_by(id=tag.id).first()): #Ajout des nouvelles étiquettes de la db dans une liste envoyée au html
                globalTags.append(tag.id)

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
    
    while len(listeQuestions) > nbcolonnes:
        x +=1
        Column_name = f'Q{x}'

        print(Column_name)
        query = f'ALTER TABLE questionnaire ADD {Column_name};'
        connection.execute(query)
        nbcolonnes +=1
    
    name_columns = [col.name for col in questionnaireTable.columns]
    for i, element in enumerate(listeQuestions, start=2):
        print(element)
        db.session.execute(questionnaireTable.update().values({name_columns[i]: element}))
    db.session.commit()
    return redirect(url_for('editeur'))


@app.route('/quest/<int:id>', methods=['POST', 'GET'])
def quest(id):
    Question = question.query.get(id)
    bonnesReps = question.query.with_entities(question.bonne_reponse)
    bonneRep = str(bonnesReps[id]).strip("()',")
    reponse = request.form.get('reponses')
    if reponse == bonneRep:
        flash("Bonne réponse !", category='success')
    else:
        flash("Mauvaise réponse !", category='danger')
    return render_template('question.html', Label=Question.Label, 
                   Etiquette=Question.Etiquette, 
                   Question=Question.Question, 
                   Réponse1=Question.Réponse1,
                   Réponse2=Question.Réponse2,
                   Réponse3=Question.Réponse3,
                   Réponse4=Question.Réponse4)

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if form.validate_on_submit():
        user_to_create = user_info(login_user=form.username.data,
                                    mail_user = form.mail.data,
                                    password = form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('connexion'))
    if form.errors != {}:
        for errors in form.errors.values():
            flash(f'Erreur : {errors}', category='danger')
    return render_template('inscription.html', form=form)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    form = FormConnexion()
    if form.validate_on_submit():
        passed_user = user_info.query.filter_by(login_user=form.username.data).first()
        if passed_user and passed_user.check_password_correction(passed_password = form.password.data):
            login_user(passed_user)
            flash(f"Connection réussie sous l'username {passed_user.login_user}", category='success')
            return redirect(url_for('editeur'))
        else:
            flash(f"Erreur, le nom d'utilisateur ne correspond pas au mot de passe !", category='danger')
    return render_template('connexion.html', form=form)

@app.route('/deconnexion', methods=['GET', 'POST'])
def deconnexion():
    logout_user()
    flash("Deconnexion réussie !", category='info')
    return redirect(url_for('editeur'))
