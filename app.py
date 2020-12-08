from flask import Flask, render_template, request, g
from datetime import datetime
from database import connect_db, get_db
import sqlite3

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        new_date = datetime.strptime(str(request.form['new_date']), '%Y-%m-%d')
        new_date_for_db = datetime.strftime(new_date, '%Y%m%d')
        db.execute('insert into log_date (entry_date) values (?)', [new_date_for_db])
        db.commit()
    cur = db.execute('''select log_date.entry_date as entry_date, sum(food.protein) as protein, sum(food.carbo) as carbo, sum(food.fat) as fat, sum(food.calories) as calories 
                        from log_date 
                        left join food_date on food_date.log_date_id = log_date.id 
                        left join food on food.id = food_date.food_id 
                        group by log_date.id 
                        order by log_date.entry_date desc''')
    totals_raw = cur.fetchall()
    totals = []
    for i in totals_raw:
        single_date = {}
        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['pretty_date'] = datetime.strftime(d, '%B %d, %Y')
        single_date['entry_date'] = str(i['entry_date'])
        single_date['protein'] = str(i['protein'])
        single_date['carbo'] = str(i['carbo'])
        single_date['fat'] = str(i['fat'])
        single_date['calories'] = str(i['calories'])
        totals.append(single_date)
    return render_template('home.html', totals=totals)

@app.route('/view/<date>', methods=['POST', 'GET']) # date es. 20201207
def view(date):
    db = get_db()
    cur_id = db.execute('select id from log_date where entry_date = (?)', [date])
    date_id = cur_id.fetchone()
    if request.method == 'POST':
        db.execute('insert into food_date (food_id, log_date_id) values (?, ?)', [request.form['food-select'], date_id['id']])
        db.commit()
    d = datetime.strptime(str(date), '%Y%m%d')
    date_pretty = datetime.strftime(d, '%B %d, %Y')
    cur = db.execute('''select name, protein, carbo, fat, calories 
                        from food join food_date on food.id = food_date.food_id 
                        where log_date_id = (?)''', [date_id['id']])
    foods_on_date = cur.fetchall()
    cur_all = db.execute('select id, name from food')
    all_foods = cur_all.fetchall()
    totals_perday = {'protein':0, 'carbo':0, 'fat':0, 'calories':0}
    for food in foods_on_date:
        totals_perday['protein'] += int(food['protein'])
        totals_perday['carbo'] += int(food['carbo'])
        totals_perday['fat'] += int(food['fat'])
        totals_perday['calories'] += int(food['calories'])
    return render_template('day.html', date_id=date, date=date_pretty, foods=foods_on_date, all_foods=all_foods, total=totals_perday)

@app.route('/add', methods=['POST', 'GET'])
def add():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        protein = int(request.form['protein'])
        carbo = int(request.form['carbo'])
        fat = int(request.form['fat'])
        calories = protein + carbo + fat
        db.execute('insert into food (name, protein, carbo, fat, calories) values (?, ?, ?, ?, ?)',
                   [name, protein, carbo, fat, calories])
        db.commit()
    cur = db.execute('select id, name, protein, carbo, fat, calories from food')
    foods = cur.fetchall()
    return render_template('add_food.html', foods=foods)

if __name__ == '__main__':
    app.run(debug=True)
