import csv
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Налаштування бази даних SQLite (шлях абсолютний)
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'digital_pchilka.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Таблиця "Work" для зберігання творів у базі даних
class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.String(500), nullable=True)
    text = db.Column(db.Text, nullable=False)

# Перенесення даних із файлу works.csv у базу даних SQLite
def load_works_from_csv():
    csv_file_path = os.path.join(BASE_DIR, 'works.csv')
    if os.path.exists(csv_file_path):
        Work.query.delete()  # Очищення старих записів перед оновленням
        # utf-8-sig прибирає невидимий BOM, якщо CSV збережено з Excel
        with open(csv_file_path, mode='r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file, delimiter=';')
            for number, row in enumerate(reader, start=1):
                work = Work(
                    id=number,  # id = номер рядка в CSV, тож посилання /work/<id> стабільні
                    title=row['title'],
                    genre=row['genre'],
                    year=int(row['year']) if row['year'].isdigit() else None,
                    summary=row['summary'],
                    text=row['text']
                )
                db.session.add(work)
        db.session.commit()

# Ініціалізація бази даних при запуску
with app.app_context():
    db.create_all()
    load_works_from_csv()

# 1. Головна сторінка
@app.route('/')
def home():
    return render_template('index.html')

# 2. Сторінка "Архів творів"
@app.route('/archive')
def archive():
    search_query = request.args.get('search', '').strip()
    genre = request.args.get('genre', '').strip()
    year = request.args.get('year', '').strip()

    query = Work.query
    if genre:
        query = query.filter(Work.genre == genre)
    if year.isdigit():
        query = query.filter(Work.year == int(year))
    works = query.order_by(Work.year, Work.title).all()

    # Пошук робимо в Pytho
    if search_query:
        needle = search_query.casefold()
        works = [
            w for w in works
            if needle in w.title.casefold()
            or needle in w.text.casefold()
            or needle in (w.summary or '').casefold()
        ]

    genres = [g for (g,) in db.session.query(Work.genre).distinct().order_by(Work.genre)]
    years = [y for (y,) in db.session.query(Work.year).filter(Work.year.isnot(None)).distinct().order_by(Work.year)]
    return render_template('archive.html', works=works, search_query=search_query,
                           genre=genre, year=year, genres=genres, years=years)

# 3. Детальна сторінка окремого твору
@app.route('/work/<int:work_id>')
def work_detail(work_id):
    work = db.get_or_404(Work, work_id)
    prev_work = Work.query.filter(Work.id < work_id).order_by(Work.id.desc()).first()
    next_work = Work.query.filter(Work.id > work_id).order_by(Work.id).first()
    return render_template('work_detail.html', work=work, prev_work=prev_work, next_work=next_work)

# 4. Світоглядний квіз
@app.route('/mindset', methods=['GET', 'POST'])
def mindset():
    result = None
    if request.method == 'POST':
        # Збираємо відповіді користувача з форми
        answers = [
            request.form.get('q1'),
            request.form.get('q2'),
            request.form.get('q3'),
            request.form.get('q4'),
            request.form.get('q5')
        ]

        # Якщо відповіли не на всі питання
        if any(a not in ('ethno', 'publisher', 'activist') for a in answers):
            return render_template('mindset.html', result=None,
                                   error='Дайте відповідь на всі 5 запитань.')

        # Підраховуємо бали для трьох типів діяльності
        scores = {'ethno': 0, 'publisher': 0, 'activist': 0}
        for ans in answers:
            if ans in scores:
                scores[ans] += 1

        # Визначаємо максимальну кількість балів
        max_score = max(scores.values())
        winners = [key for key, value in scores.items() if value == max_score]

        # Перевірка на однакову кількість балів
        if len(winners) > 1:
            result = {
                'title': 'Синтез кількох напрямів',
                'desc': 'Ваші відповіді показують зацікавленість одразу кількома сферами діяльності Олени Пчілки.',
                'connection': 'Олена Пчілка поєднувала у своїй праці безліч ролей: вона була одночасно етнографом, видавчинею та громадською діячкою.'
            }
        else:
            main_type = winners[0]
            if main_type == 'ethno':
                result = {
                    'title': 'Етнографічний напрям',
                    'desc': 'Вам найближче збереження народної культури, звичаїв та традицій.',
                    'connection': 'У 1876 році Олена Пчілка видала фундаментальну працю «Український народний орнамент», де зібрала й систематизувала сотні зразків української вишивки та ткацтва.'
                }
            elif main_type == 'publisher':
                result = {
                    'title': 'Видавничий та освітній напрям',
                    'desc': 'Вам найближча турбота про освіту молоді та створення якісних книжок.',
                    'connection': 'Олена Пчілка видавала дитячий журнал «Молода Україна» та упорядкувала збірку дитячих віршів і казок «Зелений гай» (1914 рік).'
                }
            else:
                result = {
                    'title': 'Громадсько-публіцистичний напрям',
                    'desc': 'Вам найближче відстоювання громадянської позиції та права на рідне слово.',
                    'connection': 'Олена Пчілка видавала часопис «Рідний Край», виступала на захист української мови та брала участь у жіночому русі (зокрема друкувалася в альманасі «Перший вінок», 1887 рік).'
                }

    return render_template('mindset.html', result=result, error=None)

if __name__ == '__main__':
    app.run(debug=True)
