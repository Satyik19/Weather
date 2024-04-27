import requests
from flask import Flask, render_template, request, redirect, session,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cities.db'
app.config['SECRET_KEY'] ='dcdbchfycnjdndjevmj'
db = SQLAlchemy(app)



class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    pressure = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User', backref='cities')

    def __init__(self, name, temperature=None, humidity=None, pressure=None, user_id=None):
        self.name = name
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.user_id = user_id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    if request.method == 'POST':
        city_name = request.form.get('city')
        try:
            r = requests.get('https://api.openweathermap.org/data/2.5/weather?q=' + city_name + '&appid=53705fdcadca2dde585078447590836f')
            json_object = r.json()
            temperature = float(json_object['main']['temp']-273.15)
            humidity = float(json_object['main']['humidity'])
            pressure = float(json_object['main']['pressure'])

            new_city = City(name=city_name,temperature=temperature,humidity=humidity,pressure=pressure,user_id=session['user_id'])
            db.session.add(new_city)
            db.session.commit()
            cities = City.query.filter_by(user_id=session['user_id']).all()

            return render_template('weather.html', temperature=temperature, humidity=humidity, pressure=pressure, city_name=city_name, new_city=new_city, cities=cities)
        except Exception as e:
            print(e)
            return render_template('weather.html')
    else:
        cities = City.query.filter_by(user_id=session['user_id']).all()
        return render_template('weather.html', cities=cities)
    
@app.route('/delete/<int:city_id>', methods=['POST'])
def delete_city(city_id):
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    if request.method == 'POST':
        city_to_delete = city = City.query.filter_by(user_id=session['user_id'], id=city_id).one()
        if city_to_delete:
            db.session.delete(city_to_delete)
            db.session.commit()
    return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

with app.app_context():
    db.create_all()
    db.session.commit()

if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.run(debug=True)
