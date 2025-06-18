from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, IntegerField, DateField, FieldList, BooleanField, validators,
                     PasswordField, FormField)
from wtforms.fields.datetime import DateTimeField
from wtforms.validators import DataRequired, InputRequired


class EditClass(FlaskForm):
    name = StringField('Класс', validators=[InputRequired()])
    submit = SubmitField('Добавить')

class AddStudent(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    fio = StringField('ФИО', validators=[DataRequired()])
    class_name = StringField('Класс', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class EditStudentForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    fio = StringField('ФИО ученика', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

class AddTeacher(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    fio = StringField('ФИО', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class EditSubject(FlaskForm):
    name = StringField('Предмет', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class EditOffice(FlaskForm):
    name = StringField('Кабинет', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class LessonForm(FlaskForm):
    student_id = IntegerField()
    value = IntegerField()

class AddLesson(FlaskForm):
    subject = StringField('Предмет', validators=[DataRequired()])
    office = StringField('Кабинет', validators=[DataRequired()])
    class_name = StringField('Класс', validators=[DataRequired()])
    day_of_week = StringField('День недели')
    class_id = IntegerField()
    submit = SubmitField('Провести занятие')
