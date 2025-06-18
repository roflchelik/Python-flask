import psycopg

def get_db_connection():
    conn = psycopg.connect(
        host="localhost",
        port="5432",
        user="postgres",
        password="1111",
        dbname="School")
    return conn

class ShowDB():
        def __init__(self, db):
            self.__db = db
            self.__cur = db.cursor()
        def showTeachers(self):
            sql = "SELECT * FROM teacher"
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []
        def showTeachersAdmin(self):
            sql = ('SELECT teacher.id, teacher.fio, "user".login '
                  'FROM teacher JOIN "user" ON teacher.user_id="user".id')
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []
        def showStudentsAdmin(self):
            sql = ('SELECT student.id, student.fio, class.name, "user".login '
                   'FROM student JOIN "user" ON student.user_id="user".id '
                   'JOIN class ON student.class_id=class.id')
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []
        def showSubjects(self):
            sql = "SELECT * FROM subject"
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []
        def showOffices(self):
            sql = "SELECT * FROM office"
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []
        def showClasses(self):
            sql = "SELECT * FROM class"
            try:
                self.__cur.execute(sql)
                res = self.__cur.fetchall()
                if res: return res
            except:
                print("Ошибка чтения из БД")
            return []


