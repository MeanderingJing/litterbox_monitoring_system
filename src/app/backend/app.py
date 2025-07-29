import os
from datetime import timedelta
from flask import g, Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from database.postgresql_gateway import PostgreSQLGateway
from models.models import UserInfo, CatInfo, LitterboxInfo, LitterboxEdgeDeviceInfo

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://example_user:example_password@localhost:5435/example_db",
)
db_gateway = PostgreSQLGateway(DATABASE_URL)

app = Flask(__name__)
# Configuration
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "your_jwt_secret_key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


@app.before_request
def create_db_session():
    g.db_session = db_gateway.SessionLocal()


@app.teardown_request
# The function accepts an optional exception object passed in by Flask
def shutdown_session(exeption=None):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        if exeption:
            db_session.rollback()
        else:
            db_session.commit()
        db_session.close()


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    session = g.db_session
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    # Validate input
    if not username or not password or not email:
        return jsonify({"msg": "Username, password, and email are required"}), 400

    # Check if username or email already exists
    # if UserInfo.query.filter_by(username=username).first():
    #     return jsonify({"error": "Username already exists"}), 400
    if (
        session.query(UserInfo)
        .filter((UserInfo.username == username) | (UserInfo.email == email))
        .first()
    ):
        return jsonify({"error": "User already exists."}), 400

    # Hash the password and save the user
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = UserInfo(username=username, email=email, password_hash=hashed_password)
    session.add(new_user)
    session.commit()
    return jsonify({"msg": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    session = g.db_session
    username = data.get("username")
    password = data.get("password")

    # Validate input
    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    # Check if user exists and password is correct
    user = session.query(UserInfo).filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Create JWT token
    access_token = create_access_token(identity=str(user.id))
    return (
        jsonify(
            {
                "access_token": access_token,
                "username": user.username,
                "token_type": "bearer",
            }
        ),
        200,
    )

@app.route("/cats", methods=["POST"])
@jwt_required()
def create_cat():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = g.db_session

    cat = CatInfo(
        owner_id=current_user_id,
        name=data["name"],
        breed=data.get("breed"),
        age=data.get("age"),
    )
    session.add(cat)
    session.commit()

    return (
        jsonify(
            {
                "msg": "Added a cat!",
                "id": str(cat.id),
                "name": cat.name,
                "breed": cat.breed,
                "age": cat.age,
            }
        ),
        201,
    )


@app.route("/litterboxes", methods=["post"])
@jwt_required()
def create_litterbox():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = g.dbsession()

    cat = session.query(CatInfo).get(data["cat_id"])
    if not cat or str(cat.owner_id) != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403

    litterbox = LitterboxInfo(cat_id=data["cat_id"], name=data["name"])
    session.add(litterbox)
    session.commit()

    return jsonify(
        {
            "msg": "Added a litterbox!",
            "id": str(litterbox.id),
            "cat_id": str(litterbox.cat_id),
            "name": litterbox.name,
        }
    )

@app.route('/edge_devices', methods=['POST'])
@jwt_required()
def register_edge_devices():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = g.dbsession()

    litterbox = session.query(LitterboxInfo).get(data['litterbox_id'])
    if not litterbox:
        return jsonify({'error': 'Litterbox not found.'}), 404
    
    cat = session.query(CatInfo).get(litterbox.cat_id)
    if not cat or str(cat.owner_id) != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    edge_device = LitterboxEdgeDeviceInfo(
        id = data['id'],
        litterbox_id = data['litterbox_id'],
        device_name = data['device_name'],
        device_type = data['device_type']
        )
    session.add(edge_device)
    session.commit()

    return jsonify({
        'msg': 'Added an edge device!',
        'id': str(edge_device.id),
        'litterbox_id': data['litterbox_id'],
        'device_name': data['device_name'],
        'device_type': data['device_type']
    })

# @app.route('/profile', methods=['GET'])
# @jwt_required()
# def profile():
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     return jsonify({
#         "username": user.username,
#         "email": user.email
#     }), 200

# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
app.run(debug=True)
