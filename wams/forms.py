from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from wams.db import user_info

class Form(FlaskForm):
    Label = StringField(label='Label')
    Etiquette = StringField(label='Etiquette', render_kw={'readonly': True, 'placeholder' : 'Sélectionnez des étiquettes'})
    Question = TextAreaField(label='Question')
    Réponse1 = TextAreaField(label='Réponse 1')
    Réponse2 = TextAreaField(label='Réponse 2')
    Réponse3 = TextAreaField(label='Réponse 3')
    Réponse4 = TextAreaField(label='Réponse 4')
    bonne_reponse = TextAreaField(label='bonne_reponse')
    submit = SubmitField(label='Envoyer')

class FormInscription(FlaskForm):

    def validate_username(self, username_to_check):
        user = user_info.query.filter_by(login_user=username_to_check.data).first()
        if user:
            raise ValidationError("Le nom d'utilisateur est déjà utilisé !")
    def validate_mail(self, mail_to_check):
        mail = user_info.query.filter_by(mail_user=mail_to_check.data).first()
        if mail:
            raise ValidationError("Le mail est déjà utilisé !")
        

    username = StringField(label="Username:", validators=[DataRequired()])
    mail = StringField(label="Adresse mail:", validators=[Email(), DataRequired()])
    password1 = PasswordField(label="Mot de passe:", validators=[Length(min=8), DataRequired()])
    password2 = PasswordField(label="Confirmer mot de passe:", validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label="Confirmer")
  
class FormChangerPassword(FlaskForm):   
    password1 = PasswordField(label="Mot de passe:", validators=[Length(min=8), DataRequired()])
    password2 = PasswordField(label="Confirmer mot de passe:", validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label="Confirmer")

class FormConnexion(FlaskForm):
    username = StringField(label="Username:", validators=[DataRequired()])
    password = PasswordField(label="Mot de passe:", validators=[Length(min=8), DataRequired()])
    submit = SubmitField(label="Confirmer")


class FormPoserQuestionOuverte(FlaskForm):
    question_ouverte = StringField(label='Question ouverte')
    code_room = StringField(label="Code room")
    submit = SubmitField(name="submit", label='Envoyer')
    nuage = SubmitField(name="nuage")


class FormRepondreQuestionOuverte(FlaskForm):
    reponse = StringField(label='Réponse')
    code_room = StringField(label="Code room")
    submit = SubmitField(name="submit", label='Envoyer')
