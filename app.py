from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Connect to MongoDB
client = MongoClient('mongodb+srv://imaad:Ertdfgxc@cluster0.3fbel.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['car_inventory']
cars_collection = db['cars']
car_models_collection = db['car_models']
sold_cars_collection = db['sold_cars']

# Helper function to get current year
def get_current_year():
    return datetime.now().year

def validate_number_plate(plate):
    pattern = r'^[A-Z]{3}\d{3}[A-Z]$'
    return re.match(pattern, plate) is not None

@app.route('/')
def index():
    cars = cars_collection.find()
    sold_cars = db['sold_cars'].find().sort('sale_date', -1)  # Sort by sale date, most recent first
    return render_template('index.html', cars=cars, sold_cars=sold_cars)

@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = request.form['year']
        price = request.form['price']
        number_plate = request.form['number_plate'].upper()
        
        if not validate_number_plate(number_plate):
            flash('Invalid number plate format. Please use 3 uppercase letters, 3 numbers, and 1 uppercase letter.')
            return redirect(url_for('add_car'))
        
        # Check if the number plate already exists
        existing_car = cars_collection.find_one({'number_plate': number_plate})
        if existing_car:
            flash('A car with this number plate already exists.')
            return redirect(url_for('add_car'))
        
        cars_collection.insert_one({
            'make': make,
            'model': model,
            'year': year,
            'price': price,
            'number_plate': number_plate
        })
        flash('Car added successfully!')
        return redirect(url_for('index'))

    makes = car_models_collection.distinct('make')
    years = range(1990, get_current_year() + 1)
    return render_template('add_car.html', makes=makes, years=years)

@app.route('/get_models/<make>')
def get_models(make):
    models = car_models_collection.find_one({'make': make})['models']
    return {'models': models}

@app.route('/add_make_model', methods=['GET', 'POST'])
def add_make_model():
    if request.method == 'POST':
        make = request.form['make']
        models = request.form.getlist('models')
        existing_make = car_models_collection.find_one({'make': make})  
        if existing_make:
            car_models_collection.update_one(
                {'make': make},
                {'$addToSet': {'models': {'$each': models}}}  # Add new models without duplicates
            )
        else:
            car_models_collection.insert_one({
                'make': make,
                'models': models
            })
        return redirect(url_for('index'))
    return render_template('add_make_model.html')

@app.route('/edit_car/<car_id>', methods=['GET', 'POST'])
def edit_car(car_id):
    car = cars_collection.find_one({'_id': ObjectId(car_id)})
    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = request.form['year']
        price = request.form['price']
        number_plate = request.form['number_plate'].upper()
        if not validate_number_plate(number_plate):
            flash('Invalid number plate format. Please use 3 uppercase letters, 3 numbers, and 1 uppercase letter.')
            return redirect(url_for('edit_car', car_id=car_id))
        existing_car = cars_collection.find_one({'number_plate': number_plate, '_id': {'$ne': ObjectId(car_id)}})
        if existing_car:
            flash('A car with this number plate already exists.')
            return redirect(url_for('edit_car', car_id=car_id))
        
        cars_collection.update_one({'_id': ObjectId(car_id)}, {
            '$set': {
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'number_plate': number_plate
            }
        })
        flash('Car updated successfully!')
        return redirect(url_for('index'))
    makes = car_models_collection.distinct('make')
    years = range(1990, get_current_year() + 1)
    return render_template('edit_car.html', car=car, makes=makes, years=years)

@app.route('/delete_car/<car_id>')
def delete_car(car_id):
    cars_collection.delete_one({'_id': ObjectId(car_id)})
    return redirect(url_for('index'))


@app.route('/sell_car/<car_id>', methods=['GET', 'POST'])
def sell_car(car_id):
    car = cars_collection.find_one({'_id': ObjectId(car_id)})
    if not car:
        flash("Car not found.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        customer_phone = request.form['customer_phone']
        sale_price = float(request.form['sale_price'])

        # Move the car to a 'sold_cars' collection
        sold_car = car.copy()
        sold_car['sale_date'] = datetime.now()
        sold_car['customer'] = {
            'name': customer_name,
            'email': customer_email,
            'phone': customer_phone
        }
        sold_car['sale_price'] = sale_price
        sold_cars_collection = db['sold_cars']
        sold_cars_collection.insert_one(sold_car)
        
        # Remove the car from the active inventory
        cars_collection.delete_one({'_id': ObjectId(car_id)})
        
        flash(f"Car {car['make']} {car['model']} ({car['number_plate']}) has been sold to {customer_name}.")
        return redirect(url_for('index'))

    return render_template('sell_car.html', car=car)

if __name__ == '__main__':
    app.run(debug=True)

