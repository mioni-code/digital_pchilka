import csv
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Налаштування бази даних SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_pchilka.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель даних для творів
class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.String(500), nullable=True)
    text = db.Column(db.Text, nullable=False)

# Автоматичне завантаження творів з CSV-файлу (Excel)
def load_works_from_csv():
    csv_file_path = 'works.csv'
    if os.path.exists(csv_file_path):
        Work.query.delete() # Очищаємо застарілі дані
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                work = Work(
                    title=row['title'],
                    genre=row['genre'],
                    year=int(row['year']) if row['year'].isdigit() else None,
                    summary=row['summary'],
                    text=row['text']
                )
                db.session.add(work)
        db.session.commit()

with app.app_context():
    db.create_all()
    load_works_from_csv()

# Головна сторінка
@app.route('/')
def home():
    return render_template('index.html')

# Архів творів
@app.route('/archive')
def archive():
    search_query = request.args.get('search', '')
    genre_filter = request.args.get('genre', '')
    
    query = Work.query
    if search_query:
        query = query.filter(Work.title.contains(search_query) | Work.text.contains(search_query) | Work.summary.contains(search_query))
    if genre_filter:
        query = query.filter(Work.genre == genre_filter)
        
    works = query.all()
    genres = [g[0] for g in db.session.query(Work.genre).distinct().all()]
    
    return render_template('archive.html', works=works, search_query=search_query, genres=genres, selected_genre=genre_filter)

# Детальна сторінка твору
@app.route('/work/<int:work_id>')
def work_detail(work_id):
    work = Work.query.get_or_404(work_id)
    return render_template('work_detail.html', work=work)

# Інтерактивний світоглядний квіз (Mindset Explorer)
@app.route('/mindset', methods=['GET', 'POST'])
def mindset():
    result = None
    if request.method == 'POST':
        # Отримуємо відповіді з 5 питань
        answers = [
            request.form.get('q1'),
            request.form.get('q2'),
            request.form.get('q3'),
            request.form.get('q4'),
            request.form.get('q5')
        ]

        # Підраховуємо бали
        scores = {'ethno': 0, 'publisher': 0, 'activist': 0}
        for ans in answers:
            if ans in scores:
                scores[ans] += 1

        # Визначаємо максимальний бал і переможців (з урахуванням нічиєї)
        max_score = max(scores.values())
        winners = [key for key, value in scores.items() if value == max_score]

        if len(winners) > 1 or max_score == 0:
            result = {
                'title': 'Гармонійний синтез культурних типів ✨',
                'desc': 'Ваші світоглядні орієнтири поєднують кілька напрямів діяльності Олени Пчілки. Ви бачите важливість як збереження народних витоків, так і просвітництва молоді та активної громадянської позиції.',
                'connection': 'Олена Пчілка поєднувала у своїй праці безліч ролей: вона була одночасно етнографом-дослідницею, редакторкою-видавчинею та громадською діячкою.'
            }
        else:
            main_type = winners[0]
            if main_type == 'ethno':
                result = {
                    'title': 'Етнограф-Зберігач спадщини 🧵',
                    'desc': 'Ваш світогляд відображає глибоку повагу до коріння, традицій та матеріальної культури народів.',
                    'connection': 'Історичний паралелізм: Олена Пчілка здійснила фундаментальне дослідження народної творчості. У 1876 році вийшла її праця «Український народний орнамент: вишивки, ткани, писанки», де було систематизовано сотні зразків українського орнаменту.'
                }
            elif main_type == 'publisher':
                result = {
                    'title': 'Новатор-Просвітитель 📚',
                    'desc': 'Ваш фокус спрямований на розвиток молоді, освіту та якісний культурний продукт для нових поколінь.',
                    'connection': 'Історичний паралелізм: Олена Пчілка опікувалася дитячою літературою та освітою. Вона видавала дитячий часопис «Молода Україна» (перше періодичне видання для дітей у Наддніпрянщині), а також видала ілюстровану збірку віршів і казок «Зелений гай» (1914 р.).'
                }
            else:
                result = {
                    'title': 'Культурний Активіст ⚡',
                    'desc': 'Ваш вибір свідчить про принциповість, відстоювання культурних цінностей та активну громадянську позицію.',
                    'connection': 'Історичний паралелізм: Олена Пчілка була редакторкою та видавчинею українських часописів (зокрема «Рідний Край»), послідовно виступала на захист української мови та брала активну участь у жіночому русі (зокрема видала разом із Н. Кобринською альманах «Перший вінок», 1887 р.).'
                }

    return render_template('mindset.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)