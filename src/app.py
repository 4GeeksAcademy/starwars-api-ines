import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Vehicle, FavoriteCharacter, FavoritePlanet, FavoriteVehicle
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_all_user():
    all = User.query.all()
    todos = list(map(lambda item:item.serialize(), all))
    if todos == []:
        return jsonify({"msg":"Users not found"}), 404
    response_body = {
        "msg": "ok",
        "results": todos
    }
    return jsonify(response_body), 200

@app.route('/users/<int:users_id>', methods=['GET'])
def get_one_user(users_id):
    character = Character.query.get(users_id)
    if character is None:
        return jsonify({"msg":"User not exist"}), 404
    return jsonify(character.serialize()), 200

@app.route('/user/favorites', methods=['GET'])
def get_favorites():
    favorite_character = FavoriteCharacter.query.all()
    favorite_planet = FavoritePlanet.query.all()
    favorite_vehicle = FavoriteVehicle.query.all()
    character_favorites = list(map(lambda item: item.serialize(), favorite_character))
    planet_favorites = list(map(lambda item: item.serialize(), favorite_planet))
    vehicle_favorites = list(map(lambda item: item.serialize(), favorite_vehicle))
    if character_favorites == [] and planet_favorites == [] and vehicle_favorites == []:
        return jsonify({"msg":"Favorites not found"}), 404
    response_body = {
        "msg": "ok",
        "results": [
            planet_favorites,
            character_favorites,
            vehicle_favorites
            ],
    }
    
    return jsonify(response_body), 200

@app.route('/people', methods=['GET'])
def get_all_people():
    all = Character.query.all()
    todos = list(map(lambda item:item.serialize(), all))
    if todos == []:
        return jsonify({"msg":"Characters not found"}), 404
    response_body = {
        "msg": "ok",
        "results": todos
    }
    return jsonify(response_body), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_character(people_id):
    character = Character.query.get(people_id)
    if character is None:
        return jsonify({"msg":"Character not exist"}), 404
    return jsonify(character.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_all_planet():
    all = Planet.query.all()
    todos = list(map(lambda item:item.serialize(), all))
    if todos == []:
        return jsonify({"msg":"Planets not found"}), 404
    response_body = {
        "msg": "ok",
        "results": todos
    }
    return jsonify(response_body), 200

@app.route('/planets/<int:planets_id>', methods=['GET'])
def get_one_planet(planets_id):
    character = Character.query.get(planets_id)
    if character is None:
        return jsonify({"msg":"Planet not exist"}), 404
    return jsonify(character.serialize()), 200

@app.route('/vehicles', methods=['GET'])
def get_all_vehicle():
    all = Vehicle.query.all()
    todos = list(map(lambda item:item.serialize(), all))
    if todos == []:
        return jsonify({"msg":"Vehicles not found"}), 404
    response_body = {
        "msg": "ok",
        "results": todos
    }
    return jsonify(response_body), 200

@app.route('/vehicles/<int:vehicles_id>', methods=['GET'])
def get_one_vehicle(vehicles_id):
    vehicle = Vehicle.query.get(vehicles_id)
    if vehicle is None:
        return jsonify({"msg":"Vehicle not exist"}), 404
    return jsonify(vehicle.serialize()), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
