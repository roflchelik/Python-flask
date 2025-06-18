# Импортируем необходимые библиотеки и модули
from flask import request, render_template, redirect, url_for, flash, session
from .db import get_db_connection, ShowDB

from app import app
from .forms import LoginForm, AddLesson
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, login_required, logout_user
from .user import User
from datetime import date, datetime

@app.errorhandler(404)
def page_not_found(error):
    file = 'index'
    return render_template('pageError.html', title="Страница не найдена. ", file=file)
@app.errorhandler(401)
def page_not_found(error):
    file = 'login'
    return render_template('pageError.html', title="Ошибка авторизации. ", file=file)

@app.route('/')
def index():
    try:
        if current_user.role[0] == 1:
            return redirect(url_for('student'))
        elif current_user.role[0] == 2:
            return redirect(url_for('teacher'))
        elif current_user.role[0] == 3:
            return redirect(url_for('admin'))
    except:
        return render_template('layout.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role[0] == 3:
        return render_template('admin.html', title='Главная')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_db_connection()
        with (db as con):
            cur = con.cursor()
            go = 'student'
            try: res = cur.execute('SELECT id, login, password, role '
                              'FROM "user"'
                              'WHERE login = %s', (form.login.data,)).fetchone(); print(res[1])
            except:
                if form.login.data == 'admin':
                    cur.execute('INSERT INTO "user" (login, password, role) VALUES (%s,%s,%s)',
                                (form.login.data, generate_password_hash(form.password.data), 3))
            if res is None or not check_password_hash(res[2], form.password.data):
                    flash('Неверный логин или пароль', 'danger')
                    return redirect(url_for('login'))
            id, login, password, role = res
            if role == 2: go = 'teacher'
            if role == 3: go = 'admin'
            user = User(id, login, password, role)
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for(go))
    return render_template('login.html', title='Вход', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student/', methods=['GET', 'POST'])
@login_required
def student():
    if current_user.is_authenticated and current_user.role[0] == 1:
        db = get_db_connection()
        cursor = db.cursor()
        fio = cursor.execute('SELECT fio '
                             'FROM student '
                             'WHERE user_id = %s', (current_user.id,)).fetchone()[0]
        return render_template('student.html', fio=fio)
    else:
        return render_template('public_home.html')

@app.route('/teacher', methods=['GET', 'POST'])
@login_required
def teacher():
    if current_user.role[0] == 2:
        if current_user.is_authenticated:
            db = get_db_connection()
            cursor = db.cursor()
            fio = cursor.execute('SELECT fio '
                                 'FROM teacher '
                                 'WHERE user_id = %s', (current_user.id,)).fetchone()[0]
            return render_template('teacher.html', fio=fio)
        else:
            return render_template('public_home.html')
    elif current_user.role[0] == 3:
        return redirect(url_for('admin'))

@app.route('/teacher/add_lesson', methods=['GET', 'POST'])
@login_required
def add_lesson():
    form = AddLesson()
    if current_user.role[0] == 2:
        if form.validate_on_submit():
            conn = get_db_connection()
            cursor = conn.cursor()
            try: subject_id = cursor.execute('SELECT id '
                                             'FROM subject '
                                             'WHERE name = %s', (form.subject.data, )).fetchone()[0]
            except:
                flash(f'Предмета {form.subject.data} не существует!', 'success')
                return render_template('add_lesson.html', form=form)
            try: office_id = cursor.execute('SELECT id '
                                            'FROM office '
                                            'WHERE name = %s', (form.office.data, )).fetchone()[0]
            except:
                flash(f'Кабинета {form.office.data} не существует!', 'success')
                return render_template('add_lesson.html', form=form)
            try: class_id = cursor.execute('SELECT id '
                                            'FROM class '
                                            'WHERE name = %s', (form.class_name.data, )).fetchone()[0]
            except:
                flash(f'Класса {form.class_name.data} не существует!', 'success')
                return render_template('add_lesson.html', form=form)
            teacher_id = cursor.execute('SELECT id '
                                        'FROM teacher '
                                        'WHERE user_id = %s', (current_user.id, )).fetchone()[0]
            current_date = date.today()
            chetvert = 1
            if (current_date.month > 8 or current_date.month < 6):
                if (current_date.month > 10):
                    chetvert = 2
                elif (current_date.month < 4):
                    chetvert = 3
                else:
                    chetvert = 4

            lesson_id = cursor.execute('INSERT INTO lesson_of_schedule'
                                       '(subject_id,office_id,teacher_id,class_id,day_of_week)'
                                       'VALUES (%s, %s, %s, %s, %s) RETURNING id',
                                       (subject_id, office_id, teacher_id, class_id,
                                        form.day_of_week.data)).fetchone()[0]
            conn.commit()
            cursor.execute('INSERT INTO lesson (lesson_id,date,quarter)'
                           'VALUES (%s, %s, %s)',
                           (lesson_id, current_date, chetvert))
            conn.commit()

            cursor.close()
            conn.close()

            AddLesson.class_id = class_id

            flash(f'Урок по предмету "{form.subject.data}" для {form.class_name.data} класса добавлен!',
                  'success')
            session['lesson_id'] = lesson_id
            return redirect(url_for('teacher_lesson'))
    return render_template('add_lesson.html', form=form)

@app.route('/teacher/lesson/NewLesson', methods=('GET', 'POST'))
@login_required
def teacher_lesson():
    db = get_db_connection()
    cursor = db.cursor()
    form = AddLesson()
    if request.method == 'GET':
        fio_id = cursor.execute('SELECT DISTINCT fio, id '
                                'FROM student '
                                'WHERE class_id = %s', (AddLesson.class_id,)).fetchall()
        cursor.close()
        db.close()
        return render_template('teacher_lesson.html', st=fio_id, form=form)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        value = request.form.getlist('value') #получаю оценки
        count_student = cursor.execute('SELECT COUNT(class_id) '
                                       'FROM student '
                                       'WHERE class_id = %s', (AddLesson.class_id, )).fetchone()[0]
        all_student = cursor.execute('SELECT id '
                                     'FROM student '
                                     'WHERE class_id = %s', (AddLesson.class_id, )).fetchall()
        for i in range(count_student):
            cursor.execute('INSERT INTO estimation (lesson_id, score, student_id) '
                           'VALUES (%s, %s, %s)',
                           (session['lesson_id'], value[i], all_student[i][0]))
            conn.commit()
        flash('Занятие завершено!', 'success')
        return redirect(url_for('teacher'))

@app.route('/teacher/class/<name>', methods=['GET', 'POST'])
@login_required
def show_students(name):
    db = get_db_connection()
    cursor = db.cursor()
    class_id = cursor.execute('SELECT id FROM class WHERE name = %s', (name,)).fetchone()[0]
    db.commit()

    students = cursor.execute('SELECT fio FROM student WHERE class_id = %s', (class_id,)).fetchall()
    db.commit()
    cursor.close()
    db.close()
    return render_template('show_students.html', st=students)

@app.route('/teacher/show_class', methods=['GET', 'POST'])
@login_required
def show_class():
    db = get_db_connection()
    cursor = db.cursor()
    send = cursor.execute('SELECT name '
                          'FROM class').fetchall()
    return render_template('teacher_show_class.html', tclass=send)

                                                                                            # УСПЕВАЕМОСТЬ УЧЕНИКА
@app.route('/student/show_success', methods=['GET', 'POST'])
@login_required
def show_success():
    db = get_db_connection()
    cursor = db.cursor()
    fio = cursor.execute('SELECT fio '
                         'FROM student '
                         'WHERE user_id = %s', (current_user.id,)).fetchone()
    if request.method == 'GET':
        rightNow = date.today().month
        quarter = 1
        months = ['Сентябрь', 'Октябрь']
        days = 30
        if rightNow > 8 or rightNow < 6:
            if rightNow > 8:
                if rightNow > 10:
                    quarter = 2
                months = ['Ноябрь', 'Декабрь']
                days = 30
            elif rightNow < 4:
                quarter = 3
                months = ['Январь', 'Февраль', 'Март']
                days = 30
            else:
                quarter = 4
                months = ['Апрель', 'Май']
                days = 30
        subjects = cursor.execute('SELECT DISTINCT subject.name '
                                  'FROM subject JOIN lesson_of_schedule ON subject.id = lesson_of_schedule.subject_id '
                                  'JOIN lesson ON lesson.lesson_id = lesson_of_schedule.id '
                                  'WHERE quarter = %s', (quarter,)).fetchall()

        month = 0
        first_date = date(date.today().year, 9, 1)
        second_date = date.today()
        start_input_day_of_week = 1
        if quarter == 1:
            if month == 1:
                days = 31
                first_date = date(date.today().year, 10, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 10, 31)
                try:
                    take = cursor.execute('SELECT date '
                                   'FROM lesson '
                                   'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    flash('Сейчас каникулы!')
                    return redirect(url_for('student'))
        elif quarter == 2:
            if month == 0:
                days = 30
                first_date = date(date.today().year, 11, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 11, 30)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    month+=1
            if month == 1:
                days = 31
                first_date = date(date.today().year, 12, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 12, 31)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    flash('Сейчас каникулы!')
                    return redirect(url_for('student'))
        elif quarter == 3:
            if month == 0:
                days = 31
                first_date = date(date.today().year, 1, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 1, 31)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    month+=1
            if month == 1:
                if date.today().year % 4 == 0:
                    days = 29
                    first_date = date(date.today().year, 2, 1)
                    start_input_day_of_week = first_date.weekday()
                    second_date = date(date.today().year, 2, 29)
                else:
                    days = 28
                    first_date = date(date.today().year, 2, 1)
                    start_input_day_of_week = first_date.weekday()
                    second_date = date(date.today().year, 2, 28)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    month+=1
            if month == 2:
                days = 31
                first_date = date(date.today().year, 3, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 3, 31)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    flash('Сейчас каникулы!')
                    return redirect(url_for('student'))
        else:
            if month == 0:
                days = 30
                first_date = date(date.today().year, 4, 1)
                start_input_day_of_week = first_date.weekday()-1
                second_date = date(date.today().year, 4, 30)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    month+=1
            if month == 1:
                days = 31
                first_date = date(date.today().year, 5, 1)
                start_input_day_of_week = first_date.weekday()
                second_date = date(date.today().year, 5, 31)
                try:
                    take = cursor.execute('SELECT date '
                                          'FROM lesson '
                                          'WHERE date >= %s AND date <= %s', (first_date, second_date)).fetchone()[0]
                except:
                    flash('Сейчас каникулы!')
                    return redirect(url_for('student'))

        current_student_id = cursor.execute('SELECT id '
                                            'FROM student '
                                            'WHERE user_id = %s', (current_user.id,)).fetchone()[0]

        info_check = cursor.execute('SELECT DISTINCT lesson.date, subject.name, ROUND(AVG(estimation.score),1) '
                                    'FROM estimation JOIN lesson ON estimation.lesson_id = lesson.lesson_id '
                                    'JOIN lesson_of_schedule ON lesson.lesson_id=lesson_of_schedule.id '
                                    'JOIN subject ON subject.id=lesson_of_schedule.subject_id '
                                    'WHERE estimation.student_id = %s '
                                    'AND lesson.date >= %s AND lesson.date <= %s '
                                    'GROUP BY lesson.date, subject.name ',
                                    (current_student_id, first_date, second_date)).fetchall()

        if len(info_check) == 1 and info_check[0][2] == 0:
            info = [(info_check[0][0], info_check[0][1], info_check[0][2])]
        else:
            info = cursor.execute('SELECT DISTINCT lesson.date, subject.name, ROUND(AVG(estimation.score),1) '
                                  'FROM estimation JOIN lesson ON estimation.lesson_id = lesson.lesson_id '
                                  'JOIN lesson_of_schedule ON lesson.lesson_id=lesson_of_schedule.id '
                                  'JOIN subject ON subject.id=lesson_of_schedule.subject_id '
                                  'WHERE estimation.score <> 0 AND estimation.student_id = %s '
                                  'AND lesson.date >= %s AND lesson.date <= %s '
                                  'GROUP BY lesson.date, subject.name ',
                                  (current_student_id, first_date, second_date)).fetchall()

        if len(info) == 1:
            value = str(info[0][2])
            if value == '0':
                value = '   '
            elif value == '6.0':
                value = ' н '
            new_info = [(info[0][0].day, info[0][1], value)]
            for a in range(len(subjects)):
                for day in range(days):
                    da = 0
                    take = subjects[a][0]
                    for i in range(len(new_info)):
                        if new_info[i][0] == day+1 and new_info[i][1] == take and da != 1:
                            da = 1
                    if da == 0:
                        new_info.append((day+1, take, "   "))
        else:
            new_info = [(info[0][0].day, info[0][1], info[0][0])]
            for i in range(len(info)):
                value = str(info[i][2])
                if value == '0':
                    value = '   '
                elif value == '6.0':
                    value = ' н '
                new_info.append((info[i][0].day, info[i][1], value))
            for a in range(len(subjects)):
                for day in range(days):
                    da = 0
                    take = subjects[a][0]
                    for i in range(len(new_info)):
                        if new_info[i][0] == day+1 and new_info[i][1] == take and da != 1:
                            da = 1
                    if da == 0:
                        new_info.append((day+1, take, "   "))

        day_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        head_success = [(1, day_of_week[start_input_day_of_week])]

        for i in range(days):
            if i > 0:
                start_input_day_of_week += 1
                if start_input_day_of_week > 6:
                    start_input_day_of_week = 0
                head_success.append((i+1, day_of_week[start_input_day_of_week]))
        return render_template('show_success.html', subjects=subjects, head=head_success, months=months,
                               days=days, form=new_info, fio=fio)
    else:
        rightNow = date.today().month
        quarter = 1
        months = ['Сентябрь', 'Октябрь']
        days = 30
        if rightNow > 8 or rightNow < 6:
            if rightNow > 8:
                if rightNow > 10:
                    quarter = 2
                months = ['Ноябрь', 'Декабрь']
                days = 30
            elif rightNow < 4:
                quarter = 3
                months = ['Январь', 'Февраль', 'Март']
                days = 30
            else:
                quarter = 4
                months = ['Апрель', 'Май']
                days = 30
        subjects = cursor.execute('SELECT DISTINCT subject.name '
                                  'FROM subject JOIN lesson_of_schedule ON subject.id = lesson_of_schedule.subject_id '
                                  'JOIN lesson ON lesson.lesson_id = lesson_of_schedule.id '
                                  'WHERE quarter = %s', (quarter,)).fetchall()
        take_month = request.form.getlist("value")
        month = int(take_month[0])
        first_date2 = date(date.today().year, 9, 1)
        second_date2 = date.today()
        start_input_day_of_week = 1
        if quarter == 1:
            if month == 1:
                days = 31
                first_date2 = date(date.today().year, 10, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 10, 31)
        elif quarter == 2:
            if month == 0:
                days = 30
                first_date2 = date(date.today().year, 11, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 11, 30)
            else:
                days = 31
                first_date2 = date(date.today().year, 12, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 12, 31)
        elif quarter == 3:
            if month == 0:
                days = 31
                first_date2 = date(date.today().year, 1, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 1, 31)
            elif month == 1:
                if date.today().year % 4 == 0:
                    days = 29
                    first_date2 = date(date.today().year, 2, 1)
                    start_input_day_of_week = first_date2.weekday()
                    second_date2 = date(date.today().year, 2, 29)
                else:
                    days = 28
                    first_date2 = date(date.today().year, 2, 1)
                    start_input_day_of_week = first_date2.weekday()
                    second_date2 = date(date.today().year, 2, 28)
            else:
                days = 31
                first_date2 = date(date.today().year, 3, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 3, 31)
        else:
            if month == 0:
                days = 30
                first_date2 = date(date.today().year, 4, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 4, 30)
            else:
                days = 31
                first_date2 = date(date.today().year, 5, 1)
                start_input_day_of_week = first_date2.weekday()
                second_date2 = date(date.today().year, 5, 31)

        current_student_id = cursor.execute('SELECT id '
                                            'FROM student '
                                            'WHERE user_id = %s', (current_user.id,)).fetchone()[0]

        info_check = cursor.execute('SELECT DISTINCT lesson.date, subject.name, ROUND(AVG(estimation.score),1) '
                                    'FROM estimation JOIN lesson ON estimation.lesson_id = lesson.lesson_id '
                                    'JOIN lesson_of_schedule ON lesson.lesson_id=lesson_of_schedule.id '
                                    'JOIN subject ON subject.id=lesson_of_schedule.subject_id '
                                    'WHERE estimation.student_id = %s '
                                    'AND lesson.date >= %s AND lesson.date <= %s '
                                    'GROUP BY lesson.date, subject.name ',
                                    (current_student_id, first_date2, second_date2)).fetchall()
        if len(info_check) == 0:
            choosed_month = months[month]
            flash('Уроков не было в выбранном месяце')
            return redirect(url_for('show_success'))
        if len(info_check) == 1 and info_check[0][2] == 0:
            info = [(info_check[0][0], info_check[0][1], info_check[0][2])]
        else:
            info = cursor.execute('SELECT DISTINCT lesson.date, subject.name, ROUND(AVG(estimation.score),1) '
                                  'FROM estimation JOIN lesson ON estimation.lesson_id = lesson.lesson_id '
                                  'JOIN lesson_of_schedule ON lesson.lesson_id=lesson_of_schedule.id '
                                  'JOIN subject ON subject.id=lesson_of_schedule.subject_id '
                                  'WHERE estimation.score <> 0 AND estimation.student_id = %s '
                                  'AND lesson.date >= %s AND lesson.date <= %s '
                                  'GROUP BY lesson.date, subject.name ',
                                  (current_student_id, first_date2, second_date2)).fetchall()
        if len(info) == 1:
            value = str(info[0][2])
            if value == '0':
                value = '   '
            elif value == '6.0':
                value = ' н '
            new_info = [(info[0][0].day, info[0][1], value)]
            for a in range(len(subjects)):
                for day in range(days):
                    da = 0
                    take = subjects[a][0]
                    for i in range(len(new_info)):
                        if new_info[i][0] == day+1 and new_info[i][1] == take and da != 1:
                            da = 1
                    if da == 0:
                        new_info.append((day+1, take, "   "))
        else:
            new_info = [(info[0][0].day, info[0][1], info[0][0])]
            for i in range(len(info)):
                value = str(info[i][2])
                if value == '0':
                    value = '   '
                elif value == '6.0':
                    value = ' н '
                new_info.append((info[i][0].day, info[i][1], value))
            for a in range(len(subjects)):
                for day in range(days):
                    da = 0
                    take = subjects[a][0]
                    for i in range(len(new_info)):
                        if new_info[i][0] == day+1 and new_info[i][1] == take and da != 1:
                            da = 1
                    if da == 0:
                        new_info.append((day+1, take, "   "))

        day_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        head_success = [(1, day_of_week[start_input_day_of_week])]

        for i in range(days):
            if i > 0:
                start_input_day_of_week += 1
                if start_input_day_of_week > 6:
                    start_input_day_of_week = 0
                head_success.append((i+1, day_of_week[start_input_day_of_week]))
        return render_template('show_success.html', subjects=subjects, head=head_success,
                               months=months, days=days, form=new_info, fio=fio)


@app.route('/student/show_teachers', methods=['GET', 'POST'])
@login_required
def show_teachers():
    db = get_db_connection()
    dbase = ShowDB(db)
    return render_template('show_teachers.html', teach=dbase.showTeachers())

#                                                                                                           ПРЕДМЕТЫ
@app.route('/admin/show_subjects', methods=['GET', 'POST'])
@login_required
def show_subjects():
    db = get_db_connection()
    dbase = ShowDB(db)
    subjects = dbase.showSubjects()
    db.close()
    return render_template('show_subjects.html', list_subjects=subjects)

@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        if name != '':
            try:
                cursor.execute('INSERT INTO subject (name) VALUES (%s)', (name,))
                db.commit()
                flash('Предмет добавлен')
            except:
                flash('Предмет уже был добавлен!')
                return redirect(url_for('show_subjects'))
        else: flash('Заполните поле!')
        return redirect(url_for('show_subjects'))


@app.route('/admin/show_subjects/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    subject = cursor.execute('SELECT * '
                             'FROM subject '
                             'WHERE id = %s ', (id,)).fetchall()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('edit_subject.html', subject=subject)

@app.route('/admin/show_subjects/update/<id>', methods=['GET', 'POST'])
@login_required
def update_subject(id):
    if request.method == 'POST':
        name_change = request.form['name']
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE subject SET name = %s "
                           "WHERE id = %s", (name_change,id))
            db.commit()
            cursor.close()
            db.close()
            flash('Название предмета изменено')
            return redirect(url_for('show_subjects'))
        except:
            flash('Неподходящее имя предмета!')
            cursor.close()
            db.close()
            return redirect(url_for('edit_subject', id=id))

    return render_template('show_subjects.html', subject=id)

@app.route('/admin/show_subjects/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_subject(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM subject WHERE id = %s', (id,))
    db.commit()
    cursor.close()
    flash('Предмет успешно удалён')
    return redirect(url_for('show_subjects'))

#                                                                                                           КАБИНЕТЫ
@app.route('/admin/show_offices', methods=['GET', 'POST'])
@login_required
def show_offices():
    db = get_db_connection()
    dbase = ShowDB(db)
    offices = dbase.showOffices()
    db.close()
    return render_template('show_offices.html', list_offices=offices)

@app.route('/admin/add_office', methods=['GET', 'POST'])
def add_office():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        if name != '':
            try:
                cursor.execute('INSERT INTO office (name) VALUES (%s)', (name,))
                db.commit()
                flash('Кабинет добавлен')
            except:
                flash('Кабинет уже был добавлен!')
                return redirect(url_for('show_offices'))
        else: flash('Заполните поле!')
        return redirect(url_for('show_offices'))

@app.route('/admin/show_offices/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_office(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    office = cursor.execute('SELECT * '
                             'FROM office '
                             'WHERE id = %s ', (id,)).fetchall()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('edit_office.html', office=office)

@app.route('/admin/show_offices/update/<id>', methods=['GET', 'POST'])
@login_required
def update_office(id):
    if request.method == 'POST':
        name_change = request.form['name']
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE office SET name = %s "
                           "WHERE id = %s", (name_change, id))
            db.commit()
            cursor.close()
            db.close()
            flash('Название кабинета изменено')
            return redirect(url_for('show_offices'))
        except:
            flash('Неподходящее имя кабинета!')
            cursor.close()
            db.close()
            return redirect(url_for('edit_office', id=id))

    return render_template('show_offices.html', office=id)

@app.route('/admin/show_offices/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_office(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM office WHERE id = %s', (id,))
    db.commit()
    cursor.close()
    flash('Кабинет успешно удалён')
    return redirect(url_for('show_offices'))

#                                                                                                               КЛАССЫ
@app.route('/admin/show_classes', methods=['GET', 'POST'])
@login_required
def show_classes():
    db = get_db_connection()
    dbase = ShowDB(db)
    classes = dbase.showClasses()
    db.close()
    return render_template('show_classes.html', list_classes=classes)

@app.route('/admin/add_classes', methods=['GET', 'POST'])
def add_classes():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        if name != '':
            try:
                cursor.execute('INSERT INTO class (name) VALUES (%s)', (name,))
                db.commit()
                flash('Класс добавлен')
            except:
                flash('Класс уже был добавлен!')
                return redirect(url_for('show_classes'))
        else: flash('Заполните поле!')
        return redirect(url_for('show_classes'))

@app.route('/admin/show_classes/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_classes(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    classes = cursor.execute('SELECT * '
                             'FROM class '
                             'WHERE id = %s ', (id,)).fetchall()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('edit_classes.html', classes=classes)

@app.route('/admin/show_classes/update/<id>', methods=['GET', 'POST'])
@login_required
def update_classes(id):
    if request.method == 'POST':
        name_change = request.form['name']
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE class SET name = %s "
                           "WHERE id = %s", (name_change, id))
            db.commit()
            cursor.close()
            db.close()
            flash('Название класса изменено')
            return redirect(url_for('show_classes'))
        except:
            flash('Неподходящее имя класса!')
            cursor.close()
            db.close()
            return redirect(url_for('edit_classes', id=id))

    return render_template('show_offices.html', classes=id)

@app.route('/admin/show_classes/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_classes(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM class WHERE id = %s', (id,))
    db.commit()
    cursor.close()
    flash('Класс успешно удалён')
    return redirect(url_for('show_classes'))

#                                                                                                             УЧИТЕЛЯ
@app.route('/admin/show_teachers', methods=['GET', 'POST'])
@login_required
def show_teachers_admin():
    db = get_db_connection()
    dbase = ShowDB(db)
    teachers = dbase.showTeachersAdmin()
    db.close()
    return render_template('show_teachers_admin.html', list_teachers=teachers)

@app.route('/admin/add_teachers', methods=['GET', 'POST'])
def add_teachers():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        log = request.form['login']
        pwd = request.form['pass']
        hash_pwd = generate_password_hash(pwd)
        if name != '':
            try:
                user_id = cursor.execute('INSERT INTO "user" (login,password,role) '
                                         'VALUES (%s,%s, 2) RETURNING id', (log, hash_pwd)).fetchone()[0]
                db.commit()
                try:
                    cursor.execute('INSERT INTO teacher (fio,user_id) VALUES (%s,%s)', (name, user_id))
                    db.commit()
                    cursor.close()
                    db.close()
                    flash('Учитель успешно добавлен')
                    return redirect(url_for('show_teachers_admin'))
                except:
                    cursor.close()
                    db.close()
                    flash('Учитель уже был добавлен!')
                    return redirect(url_for('show_teachers_admin'))
            except:
                flash('Введены неверные данные!')
                redirect(url_for('show_teachers_admin'))
        else:
            flash('Заполните все поля!')
            return redirect(url_for('add_teachers'))
    return redirect(url_for('show_teachers_admin'))

@app.route('/admin/show_teachers/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_teachers(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    teachers = cursor.execute('SELECT teacher.id, teacher.fio, "user".login, "user".password, "user".role '
                              'FROM teacher JOIN "user" ON teacher.user_id="user".id '
                              'WHERE teacher.id = %s', (id,)).fetchall()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('edit_teacher.html', teachers=teachers)

@app.route('/admin/show_teachers/update/<id>', methods=['GET', 'POST'])
@login_required
def update_teachers(id):
    if request.method == 'POST':
        name_change = request.form['name']
        log = request.form['login']
        pwd = request.form['pwd']
        hash_pwd = generate_password_hash(pwd)
        role = request.form['role']
        db = get_db_connection()
        cursor = db.cursor()
        try:
            user_id = cursor.execute('UPDATE teacher SET fio = %s '
                                     'WHERE id = %s RETURNING user_id', (name_change, id)).fetchone()[0]
            db.commit()
            cursor.execute('UPDATE "user" SET (login, password, role) = (%s,%s,%s) '
                           'WHERE id = %s', (log, hash_pwd, role, user_id))
            db.commit()
            cursor.close()
            db.close()
            flash('Данные учителя изменены')
            return redirect(url_for('show_teachers_admin'))
        except:
            flash('Некорректные данные учителя!')
            cursor.close()
            db.close()
            return redirect(url_for('edit_teachers', id=id))

    return render_template('show_teachers_admin.html', teachers=id)

@app.route('/admin/show_teachers/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_teachers(id):
    db = get_db_connection()
    cursor = db.cursor()
    user_id = cursor.execute('SELECT user_id FROM teacher '
                             'WHERE id = %s ', (id,)).fetchone()[0]
    cursor.execute('DELETE FROM teacher WHERE id = %s', (id,))
    db.commit()
    cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
    db.commit()
    cursor.close()
    flash('Учитель успешно удалён')
    return redirect(url_for('show_teachers_admin'))

#                                                                                                             УЧЕНИКИ
@app.route('/admin/show_students', methods=['GET', 'POST'])
@login_required
def show_students_admin():
    db = get_db_connection()
    dbase = ShowDB(db)
    students = dbase.showStudentsAdmin()
    db.close()
    return render_template('show_students_admin.html', list_students=students)

@app.route('/admin/add_students', methods=['GET', 'POST'])
@login_required
def add_students():
    db = get_db_connection()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        class_name = request.form['class']
        log = request.form['login']
        pwd = request.form['pwd']
        pass_hash = generate_password_hash(pwd)
        try:
            cursor.execute('INSERT INTO "user" (login, password, role) VALUES (%s, %s, 1) RETURNING id',
                           (log, pass_hash))
            db.commit()
            user_id = cursor.fetchone()[0]
        except:
            flash(f'Ученик {log} уже добавлен!', 'success')
            return redirect(url_for('show_students_admin'))
        try:
            class_id = cursor.execute('SELECT id '
                                      'FROM class '
                                      'WHERE name = %s', (class_name, )).fetchone()[0]
            db.commit()
        except:
            flash(f'Класса {class_name} не существует!', 'success')
            return redirect(url_for('show_students_admin'))

        cursor.execute("INSERT INTO student (fio, user_id, class_id) VALUES (%s, %s, %s)",
                       (name, user_id, class_id))
        db.commit()

        cursor.close()
        db.close()

        flash(f'Ученик {name} добавлен', 'success')
        return redirect(url_for('show_students_admin'))
    return render_template('show_students_admin.html')

@app.route('/admin/show_students/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_students(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    students = cursor.execute('SELECT student.id, student.fio, class.name, "user".login, "user".password '
                              'FROM student JOIN "user" ON student.user_id="user".id '
                              'JOIN class ON student.class_id=class.id '
                              'WHERE student.id = %s', (id,)).fetchall()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('edit_student.html', students=students)

@app.route('/admin/show_students/update/<id>', methods=['GET', 'POST'])
@login_required
def update_students(id):
    if request.method == 'POST':
        name_change = request.form['name']
        class_name = request.form['class']
        log = request.form['login']
        pwd = request.form['pwd']
        hash_pwd = generate_password_hash(pwd)
        db = get_db_connection()
        cursor = db.cursor()
        try:
            class_id = cursor.execute('SELECT id '
                                      'FROM class '
                                      'WHERE name = %s', (class_name,)).fetchone()[0]

            user_id = cursor.execute('UPDATE student SET fio = %s, class_id = %s '
                                     'WHERE id = %s RETURNING user_id', (name_change, class_id, id)).fetchone()[0]
            db.commit()
            cursor.execute('UPDATE "user" SET (login, password) = (%s,%s) '
                           'WHERE id = %s', (log, hash_pwd, user_id))
            db.commit()
            cursor.close()
            db.close()
            flash('Данные ученика изменены')
            return redirect(url_for('show_students_admin'))
        except:
            flash('Некорректные данные ученика!')
            cursor.close()
            db.close()
            return redirect(url_for('edit_students', id=id))

    return render_template('show_students_admin.html', students=id)

@app.route('/admin/show_students/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete_students(id):
    db = get_db_connection()
    cursor = db.cursor()
    user_id = cursor.execute('SELECT user_id FROM student '
                             'WHERE id = %s ', (id,)).fetchone()[0]
    cursor.execute('DELETE FROM student WHERE id = %s', (id,))
    db.commit()
    cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
    db.commit()
    cursor.close()
    flash('Ученик успешно удалён')
    return redirect(url_for('show_students_admin'))