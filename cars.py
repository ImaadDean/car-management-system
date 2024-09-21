from pymongo import MongoClient

client = MongoClient('mongodb+srv://imaad:Ertdfgxc@cluster0.3fbel.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['car_inventory']
car_models_collection = db['car_models']

sample_data = [
    {
        "make": "Toyota",
        "models": ["Camry", "Corolla", "RAV4", "Highlander"]
    },
    {
        "make": "Honda",
        "models": ["Civic", "Accord", "CR-V", "Pilot"]
    },
    {
        "make": "Ford",
        "models": ["F-150", "Mustang", "Explorer", "Escape"]
    },
    {
        "make": "Chevrolet",
        "models": ["Silverado", "Equinox", "Malibu", "Camaro"]
    }
]

car_models_collection.insert_many(sample_data)
