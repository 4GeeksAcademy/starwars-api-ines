import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Vehicle, FavoriteCharacter, FavoritePlanet, FavoriteVehicle
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager 

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)

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
def get_all_users():
    all_users = User.query.all()
    all_users_list = list(map(lambda item:item.serialize(), all_users))
    if all_users_list == []:
        return jsonify({"msg":"Users not found"}), 404
    response_body = {
        "msg": "ok",
        "results": all_users_list
    }
    return jsonify(response_body), 200

@app.route('/users/<int:users_id>', methods=['GET'])
def get_one_user(users_id):
    user = User.query.get(users_id)
    if user is None:
        return jsonify({"msg":"User not exist"}), 404
    return jsonify(user.serialize()), 200

@app.route('/user', methods=['POST'])
def create_one_user():
    body = request.json
    user = User.query.filter_by(email=body["email"]).first()
    if not body:
            return jsonify({'msg': 'Bad Request'}), 400
    if user is None:
        new_user = User(email = body["email"], password = body["password"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User created successfully"}), 201
    else:
        return jsonify({"msg": "User has already exist"}), 400

@app.route('/users/favorites', methods=['GET'])
@jwt_required()
def get_all_favorites():
    email =  get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    all_favorite_character = FavoriteCharacter.query.filter_by(user_id=user_id).all()
    all_favorite_planet = FavoritePlanet.query.filter_by(user_id=user_id).all()
    all_favorite_vehicle = FavoriteVehicle.query.filter_by(user_id=user_id).all()
    all_favorite_character_list = list(map(lambda item: item.serialize(), all_favorite_character))
    all_favorite_planet_list = list(map(lambda item: item.serialize(), all_favorite_planet))
    all_favorite_vehicle_list = list(map(lambda item: item.serialize(), all_favorite_vehicle))

    if user_exist is None: 
        return jsonify({"msg": "This user does not exist"}), 401
    
    if all_favorite_character_list == [] and all_favorite_planet_list == [] and all_favorite_vehicle_list == []:
        return jsonify({"msg":"Favorites not found"}), 404
    response_body = {
        "msg": "ok",
        "results": [
            all_favorite_character_list,
            all_favorite_planet_list,
            all_favorite_vehicle_list
        ]
    }    
    return jsonify(response_body), 200
    
@app.route('/people', methods=['GET'])
def get_all_characters():
    all_characters = Character.query.all()
    all_characters_list = list(map(lambda item:item.serialize(), all_characters))
    if all_characters_list == []:
        return jsonify({"msg":"Characters not found"}), 404
    response_body = {
        "msg": "ok",
        "results": all_characters_list
    }
    return jsonify(response_body), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_character(people_id):
    character = Character.query.get(people_id)
    if character is None:
        return jsonify({"msg":"Character not exist"}), 404
    return jsonify(character.serialize()), 200

@app.route('/people', methods=['POST'])
def create_one_character():
    body = request.json
    character = Character.query.filter_by(name=body["name"]).first()
    if not body:
            return jsonify({'msg': 'Bad Request'}), 400
    if character is None:
        new_character = Character(name=body["name"],description=body["description"])
        db.session.add(new_character)
        db.session.commit()
        return jsonify({"msg": "Character created successfully"}), 201
    else:
        return jsonify({"msg": "Character has already exist"}), 400

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_character(people_id):
    character_to_delete = Character.query.filter_by(id=people_id).first()
    if character_to_delete:
        db.session.delete(character_to_delete)
        db.session.commit()
        return jsonify({"msg": "Character deleted"}), 200
    else:
        return jsonify({"msg": "Character not found"}), 404

@app.route("/favorite/people/<int:people_id>", methods=["POST"])
@jwt_required()
def add_favorite_character(people_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    character_exist = Character.query.filter_by(id=people_id).first()
    if user_exist is None and character_exist is None:
        return jsonify({'msg': 'There are not users or characters'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    elif character_exist is None:
        return ({"msg": "This character doesn't exist"}), 400
    else:
        exist_favorite_character = FavoriteCharacter.query.filter_by(character_id=people_id, user_id=user_id).first()
        if exist_favorite_character is None:
            new_favorite_character = FavoriteCharacter(character_id=people_id, user_id=user_id)
            db.session.add(new_favorite_character)
            db.session.commit()
            return jsonify({"msg": "Character added to favorites"}), 201
        else:  
            return jsonify({'msg': 'Character has already exist in favorites'}), 400
        
@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_character(people_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    character_exist = Character.query.filter_by(id=people_id).first()
    if user_exist is None and character_exist is None:
        return jsonify({'msg': 'There are not users or favorites characters'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    else:
        favorite_character_to_delete = FavoriteCharacter.query.filter_by(character_id=people_id, user_id=user_id).first()
        if favorite_character_to_delete:
            db.session.delete(favorite_character_to_delete)
            db.session.commit()
            return jsonify({"msg": "Character deleted to favorites"}), 200
        else:  
            return ({"msg": "This character doesn't exist in favorites"}), 400
      
@app.route('/planets', methods=['GET'])
def get_all_planets():
    all_planets = Planet.query.all()
    all_planets_list = list(map(lambda item:item.serialize(), all_planets))
    if all_planets_list == []:
        return jsonify({"msg":"Planets not found"}), 404
    response_body = {
        "msg": "ok",
        "results": all_planets_list
    }
    return jsonify(response_body), 200

@app.route('/planets/<int:planets_id>', methods=['GET'])
def get_one_planet(planets_id):
    planet = Planet.query.get(planets_id)
    if planet is None:
        return jsonify({"msg":"Planet not exist"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/planets', methods=['POST'])
def create_one_planet():
    body = request.json
    planet = Planet.query.filter_by(name=body["name"]).first()
    if not body:
            return jsonify({'msg': 'Bad Request'}), 400
    if planet is None:
        new_planet = Planet(name=body["name"], description=body["description"])
        db.session.add(new_planet)
        db.session.commit()
        return jsonify({"msg": "Planet created successfully"}), 201
    else:
        return jsonify({"msg": "Planet has already exist"}), 201

@app.route('/planets/<int:planets_id>', methods=['DELETE'])
def delete_planet(planets_id):
    planet_to_delete = Planet.query.filter_by(id=planets_id).first()
    if planet_to_delete:
        db.session.delete(planet_to_delete)
        db.session.commit()
        return jsonify({"msg": "Planet deleted"}), 200
    else:
        return jsonify({"msg": "Planet not found"}), 404 

@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
@jwt_required()
def add_favorite_planet(planet_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    planet_exist = Planet.query.filter_by(id=planet_id).first()
    if user_exist is None and planet_exist is None:
        return jsonify({'msg': 'There are not users or planets'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    elif planet_exist is None:
        return ({"msg": "This planet doesn't exist"}), 400
    else:
        exist_favorite_planet = FavoritePlanet.query.filter_by(planet_id=planet_id, user_id=user_id).first()
        if exist_favorite_planet is None:
            new_favorite_planet = FavoritePlanet(planet_id=planet_id, user_id=user_id)
            db.session.add(new_favorite_planet)
            db.session.commit()
            return jsonify({"msg": "Planet added to favorites"}), 201
        else:  
            return jsonify({'msg': 'Planet has already exist in favorites'}), 400

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_planet(planet_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    planet_exist = Planet.query.filter_by(id=planet_id).first()
    if user_exist is None and planet_exist is None:
        return jsonify({'msg': 'There are not users or favorites planets'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    else:
        favorite_planet_to_delete = FavoritePlanet.query.filter_by(planet_id=planet_id, user_id=user_id).first()
        if favorite_planet_to_delete:
            db.session.delete(favorite_planet_to_delete)
            db.session.commit()
            return jsonify({"msg": "Planet deleted to favorites"}), 200
        else:  
            return ({"msg": "This planet doesn't exist in favorites"}), 400
        
@app.route('/vehicles', methods=['GET'])
def get_all_vehicles():
    all_vehicles = Vehicle.query.all()
    all_vehicles_list = list(map(lambda item:item.serialize(), all_vehicles))
    if all_vehicles_list == []:
        return jsonify({"msg":"Vehicles not found"}), 404
    response_body = {
        "msg": "ok",
        "results": all_vehicles_list
    }
    return jsonify(response_body), 200

@app.route('/vehicles/<int:vehicles_id>', methods=['GET'])
def get_one_vehicle(vehicles_id):
    vehicle = Vehicle.query.get(vehicles_id)
    if vehicle is None:
        return jsonify({"msg":"Vehicle not exist"}), 404
    return jsonify(vehicle.serialize()), 200

@app.route('/vehicles', methods=['POST'])
def create_one_vehicle():
    body = request.json
    vehicle = Vehicle.query.filter_by(name=body["name"]).first()
    if not body:
            return jsonify({'msg': 'Bad Request'}), 400
    if vehicle is None:
        new_vehicle = Vehicle(name=body["name"],description=body["description"])
        db.session.add(new_vehicle)
        db.session.commit()
        return jsonify({"msg": "Vehicle created successfully"}), 201
    else:
        return jsonify({"msg": "Vehicle has already exist"}), 201

@app.route('/vehicles/<int:vehicles_id>', methods=['DELETE'])
def delete_vehicle(vehicles_id):
    vehicle_to_delete = Vehicle.query.filter_by(id=vehicles_id).first()
    if vehicle_to_delete:
        db.session.delete(vehicle_to_delete)
        db.session.commit()
        return jsonify({"msg": "Vehicle deleted"}), 200
    else:
        return jsonify({"msg": "Vehicle not found"}), 404 

@app.route("/favorite/vehicle/<int:vehicle_id>", methods=["POST"])
@jwt_required()
def add_favorite_vehicle(vehicle_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    vehicle_exist = Vehicle.query.filter_by(id=vehicle_id).first()
    if user_exist is None and vehicle_exist is None:
        return jsonify({'msg': 'There are not users or vehicles'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    elif vehicle_exist is None:
        return ({"msg": "This vehicle doesn't exist"}), 400
    else:
        exist_favorite_vehicle = FavoriteVehicle.query.filter_by(vehicle_id=vehicle_id, user_id=user_id).first()
        if exist_favorite_vehicle is None:
            new_favorite_vehicle = FavoriteVehicle(vehicle_id=vehicle_id, user_id=user_id)
            db.session.add(new_favorite_vehicle)
            db.session.commit()
            return jsonify({"msg": "Vehicle added to favorites"}), 201
        else:  
            return jsonify({'msg': 'Vechile has already exist in favorites'}), 400

@app.route('/favorite/vehicle/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_vehicle(vehicle_id): 
    email = get_jwt_identity()
    user_exist = User.query.filter_by(email=email).first()
    user_id = user_exist.id
    vehicle_exist = Vehicle.query.filter_by(id=vehicle_id).first()
    if user_exist is None and vehicle_exist is None:
        return jsonify({'msg': 'There are not users or favorites vehicles'}), 400
    elif user_exist is None:
        return ({"msg": "This user doesn't exist"}), 400
    else:
        favorite_vehicle_to_delete = FavoriteVehicle.query.filter_by(vehicle_id=vehicle_id, user_id=user_id).first()
        if favorite_vehicle_to_delete:
            db.session.delete(favorite_vehicle_to_delete)
            db.session.commit()
            return jsonify({"msg": "Vehicle deleted to favorites"}), 200
        else:  
            return ({"msg": "This vehicle doesn't exist in favorites"}), 400

@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"msg": "Email doesnt exist"}), 404
    if email != user.email or password != user.password:
        return jsonify({"msg": "Bad email or password"}), 401
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)

@app.route("/signup", methods=["POST"])
def signup():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user_exist = User.query.filter_by(email=email).first()
    
    if user_exist is None: 
            new_user = User(
                email=email, 
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "User already exist"}), 400

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
