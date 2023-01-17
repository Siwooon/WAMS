from wams import app
from flask import render_template, redirect, url_for, request, jsonify
from wams.db import question
from wams.forms import Form
from wams.db import db



@app.route('/', methods=['GET', 'POST'])
def home():
    Question = question.query.all()
    form = Form()
    if form.validate_on_submit():
        
        questionToAdd = question(Label=form.Label.data,
                                Etiquette=form.Etiquette.data,
                                Question=form.Question.data,
                                Réponse1=form.Réponse1.data,
                                Réponse2=form.Réponse2.data,
                                Réponse3=form.Réponse3.data,
                                Réponse4=form.Réponse4.data)
        db.session.add(questionToAdd)
        db.session.commit()
        return redirect(url_for('test'))
    return render_template('home.html', form = form, question = Question)


@app.route('/update/<int:id>', methods=['GET'])
def update(id):
    Question = question.query.get(id)
    return jsonify(Label=Question.Label, 
                   Etiquette=Question.Etiquette, 
                   Question=Question.Question, 
                   Réponse1=Question.Réponse1,
                   Réponse2=Question.Réponse2,
                   Réponse3=Question.Réponse3,
                   Réponse4=Question.Réponse4)


@app.route('/update2', methods=['POST'])
def update2():
    Label = request.form['Label']
    Etiquette = request.form['Etiquette']
    Question = request.form['Question']
    Réponse1 = request.form['Réponse1']
    Réponse2 = request.form['Réponse2']
    Réponse3 = request.form['Réponse3']
    Réponse4 = request.form['Réponse4']

    question = Question.query.filter_by(Label=Label).first()

    if question:
        question.Etiquette = Etiquette
        question.Question = Question
        question.Réponse1 = Réponse1
        question.Réponse2 = Réponse2
        question.Réponse3 = Réponse3
        question.Réponse4 = Réponse4
    else:
        question = Question(Label=Label, Etiquette=Etiquette, Question=Question, Réponse1=Réponse1, Réponse2=Réponse2, Réponse3=Réponse3, Réponse4=Réponse4)
        db.session.add(question)

    db.session.commit()









# @app.route('/update/<int:id>', methods=['POST'])
# def update_user(id):
#     Question = question.query.get(id)
#     Question.Label = request.form['Label']
#     Question.Etiquette = request.form['Etiquette']
#     Question.Question = request.form['Question']
#     Question.Réponse1= request.form['Réponse1']
#     Question.Réponse2= request.form['Réponse2']
#     Question.Réponse3= request.form['Réponse3']
#     Question.Réponse4= request.form['Réponse4']
#     db.session.commit()
#     return redirect('/')















@app.route('/test')
def test():
    return 'Hello World'

