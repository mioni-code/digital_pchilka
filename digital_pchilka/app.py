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

# Психологічний тест (Mindset Explorer)
@app.route('/mindset', methods=['GET', 'POST'])
def mindset():
    result = None
    if request.method == 'POST':
        q1 = request.form.get('q1')
        q2 = request.form.get('q2')
        if q1 == 'culture' and q2 == 'tradition':
            result = {'title': 'Етнограф-Просвітитель', 'desc': 'Як і Олена Пчілка, ви прагнете зберігати культурну спадщину та традиції.'}
        elif q1 == 'activism' or q2 == 'modern':
            result = {'title': 'Модерніст-Новатор', 'desc': 'Ви сміливо впроваджуєте нові ідеї та змінюєте суспільство.'}
        else:
            result = {'title': 'Гармонійний Хранитель', 'desc': 'Ви поєднуєте любов до рідної культури із прагненням до розвитку.'}
    return render_template('mindset.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)