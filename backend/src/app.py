import os
from datetime import timedelta, datetime
import uuid
from flask import g, Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from database.postgresql_gateway import PostgreSQLGateway
from models.models import (
    LitterboxUsageData,
    UserInfo,
    CatInfo,
    LitterboxInfo,
    LitterboxEdgeDeviceInfo,
)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://example_user:example_password@192.168.40.159:5435/example_db",
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
    session = g.db_session

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


@app.route("/edge_devices", methods=["POST"])
@jwt_required()
def register_edge_devices():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    session = g.db_session

    litterbox = session.query(LitterboxInfo).get(data["litterbox_id"])
    if not litterbox:
        return jsonify({"error": "Litterbox not found."}), 404

    cat = session.query(CatInfo).get(litterbox.cat_id)
    if not cat or str(cat.owner_id) != current_user_id:
        return jsonify({"error": "Unauthorized"}), 403

    edge_device = LitterboxEdgeDeviceInfo(
        id=data["id"],
        litterbox_id=data["litterbox_id"],
        device_name=data["device_name"],
        device_type=data["device_type"],
    )
    session.add(edge_device)
    session.commit()

    return jsonify(
        {
            "msg": "Added an edge device!",
            "id": str(edge_device.id),
            "litterbox_id": data["litterbox_id"],
            "device_name": data["device_name"],
            "device_type": data["device_type"],
        }
    )


@app.route("/cats", methods=["GET"])
@jwt_required()
def get_cats():
    current_user_id = get_jwt_identity()
    session = g.db_session

    cats = session.query(CatInfo).filter_by(owner_id=current_user_id).all()

    cats_data = []
    for cat in cats:
        cats_data.append(
            {"id": str(cat.id), "name": cat.name, "breed": cat.breed, "age": cat.age}
        )

    return jsonify(cats_data), 200


@app.route("/litterboxes", methods=["GET"])
@jwt_required()
def get_litterboxes():
    current_user_id = get_jwt_identity()
    session = g.db_session

    # Get litterboxes for cats owned by the current user
    litterboxes = (
        session.query(LitterboxInfo)
        .join(CatInfo)
        .filter(CatInfo.owner_id == current_user_id)
        .all()
    )

    litterboxes_data = []
    for litterbox in litterboxes:
        litterboxes_data.append(
            {
                "id": str(litterbox.id),
                "cat_id": str(litterbox.cat_id),
                "name": litterbox.name,
            }
        )

    return jsonify(litterboxes_data), 200


@app.route("/edge_devices", methods=["GET"])
@jwt_required()
def get_edge_devices():
    current_user_id = get_jwt_identity()
    session = g.db_session

    # Get edge devices for litterboxes owned by the current user
    edge_devices = (
        session.query(LitterboxEdgeDeviceInfo)
        .join(LitterboxInfo)
        .join(CatInfo)
        .filter(CatInfo.owner_id == current_user_id)
        .all()
    )

    devices_data = []
    for device in edge_devices:
        devices_data.append(
            {
                "id": str(device.id),
                "litterbox_id": str(device.litterbox_id),
                "device_name": device.device_name,
                "device_type": device.device_type,
            }
        )

    return jsonify(devices_data), 200


@app.route("/cats/<cat_id>/litterbox-usage", methods=["GET"])
@jwt_required()
def get_cat_litterbox_usage(cat_id):
    """
    Retrieve litterbox usage data for a specific cat.
    Only returns data for cats owned by the authenticated user.

    Query parameters:
    - start_date: ISO format datetime string (optional)
    - end_date: ISO format datetime string (optional)
    - limit: number of records to return (default: 100, max: 1000)
    - offset: offset for pagination (default: 0)
    """
    current_user_id = get_jwt_identity()
    session = g.db_session

    # Get query parameters
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = max(int(request.args.get("offset", 0)), 0)

    # Parse dates if provided
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
    except ValueError:
        return (
            jsonify(
                {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}
            ),
            400,
        )

    try:
        cat_uuid = uuid.UUID(cat_id)
    except ValueError:
        return jsonify({"error": "Invalid cat ID format"}), 400

    # First, verify the cat belongs to the current user
    cat = (
        session.query(CatInfo)
        .filter(
            and_(CatInfo.id == cat_uuid, CatInfo.owner_id == uuid.UUID(current_user_id))
        )
        .first()
    )

    if not cat:
        return (
            jsonify(
                {
                    "error": "Cat not found or you don't have permission to access this cat's data"
                }
            ),
            404,
        )

    # Build the query to get usage data
    # .options(joinedload(...)):
    # “When you query LitterboxUsageData, go ahead and eagerly load the related LitterboxEdgeDeviceInfo
    # and its LitterboxInfo in the same SQL query (using JOIN).”
    query = (
        session.query(LitterboxUsageData)
        .join(
            LitterboxEdgeDeviceInfo,
            LitterboxUsageData.litterbox_edge_device_id == LitterboxEdgeDeviceInfo.id,
        )
        .join(LitterboxInfo, LitterboxEdgeDeviceInfo.litterbox_id == LitterboxInfo.id)
        .join(CatInfo, LitterboxInfo.cat_id == CatInfo.id)
        .filter(CatInfo.id == cat_uuid)
        .options(
            joinedload(LitterboxUsageData.litterbox_edge_device).joinedload(
                LitterboxEdgeDeviceInfo.litterbox
            )
        )
    )

    # Apply date filters if provided
    if start_date:
        query = query.filter(LitterboxUsageData.enter_time >= start_date)
    if end_date:
        query = query.filter(LitterboxUsageData.enter_time <= end_date)

    # Order by most recent first
    query = query.order_by(LitterboxUsageData.enter_time.desc())

    # Get total count for pagination info
    total_count = query.count()

    # Apply pagination
    usage_data = query.offset(offset).limit(limit).all()

    # Transform the data
    usage_responses = []
    for usage in usage_data:
        duration = (
            usage.exit_time - usage.enter_time
        ).total_seconds() / 60  # in minutes
        weight_diff = usage.weight_enter - usage.weight_exit

        usage_responses.append(
            {
                "id": str(usage.id),
                "enter_time": usage.enter_time.isoformat(),
                "exit_time": usage.exit_time.isoformat(),
                "weight_enter": usage.weight_enter,
                "weight_exit": usage.weight_exit,
                "duration_minutes": round(duration, 2),
                "cat_weight": round(weight_diff, 2),
                "created_at": usage.created_at.isoformat(),
                "device_name": usage.litterbox_edge_device.device_name,
                "litterbox_name": usage.litterbox_edge_device.litterbox.name,
            }
        )

    return (
        jsonify(
            {
                "cat_id": str(cat.id),
                "cat_name": cat.name,
                "total_usage_count": total_count,
                "returned_count": len(usage_responses),
                "offset": offset,
                "limit": limit,
                "usage_data": usage_responses,
            }
        ),
        200,
    )


@app.route("/my-cats/litterbox-usage", methods=["GET"])
@jwt_required()
def get_all_my_cats_litterbox_usage():
    """
    Retrieve litterbox usage data for all cats owned by the authenticated user.

    Query parameters:
    - start_date: ISO format datetime string (optional)
    - end_date: ISO format datetime string (optional)
    - limit_per_cat: number of records per cat (default: 50, max: 500)
    """
    current_user_id = get_jwt_identity()
    session = g.db_session

    # Get query parameters
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    limit_per_cat = min(int(request.args.get("limit_per_cat", 50)), 500)

    # Parse dates if provided
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
    except ValueError:
        return (
            jsonify(
                {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}
            ),
            400,
        )

    # Get all cats owned by the user
    cats = (
        session.query(CatInfo)
        .filter(CatInfo.owner_id == uuid.UUID(current_user_id))
        .all()
    )

    if not cats:
        return jsonify({"error": "No cats found for this user"}), 404

    result = []

    for cat in cats:
        # Get usage data for each cat
        query = (
            session.query(LitterboxUsageData)
            .join(
                LitterboxEdgeDeviceInfo,
                LitterboxUsageData.litterbox_edge_device_id
                == LitterboxEdgeDeviceInfo.id,
            )
            .join(
                LitterboxInfo, LitterboxEdgeDeviceInfo.litterbox_id == LitterboxInfo.id
            )
            .filter(LitterboxInfo.cat_id == cat.id)
            .options(
                joinedload(LitterboxUsageData.litterbox_edge_device).joinedload(
                    LitterboxEdgeDeviceInfo.litterbox
                )
            )
        )

        if start_date:
            query = query.filter(LitterboxUsageData.enter_time >= start_date)
        if end_date:
            query = query.filter(LitterboxUsageData.enter_time <= end_date)

        total_count = query.count()
        usage_data = (
            query.order_by(LitterboxUsageData.enter_time.desc())
            .limit(limit_per_cat)
            .all()
        )

        usage_responses = []
        for usage in usage_data:
            duration = (usage.exit_time - usage.enter_time).total_seconds() / 60
            weight_diff = usage.weight_exit - usage.weight_enter

            usage_responses.append(
                {
                    "id": str(usage.id),
                    "enter_time": usage.enter_time.isoformat(),
                    "exit_time": usage.exit_time.isoformat(),
                    "weight_enter": usage.weight_enter,
                    "weight_exit": usage.weight_exit,
                    "duration_minutes": round(duration, 2),
                    "weight_difference": round(weight_diff, 2),
                    "created_at": usage.created_at.isoformat(),
                    "device_name": usage.litterbox_edge_device.device_name,
                    "litterbox_name": usage.litterbox_edge_device.litterbox.name,
                }
            )

        result.append(
            {
                "cat_id": str(cat.id),
                "cat_name": cat.name,
                "total_usage_count": total_count,
                "returned_count": len(usage_responses),
                "usage_data": usage_responses,
            }
        )

    return jsonify({"cats": result, "total_cats": len(cats)}), 200


# @app.route("/cats/<cat_id>/litterbox-usage/stats", methods=["GET"])
# @jwt_required()
# def get_cat_litterbox_usage_stats(cat_id):
#     """
#     Get usage statistics for a cat over a specified period.

#     Query parameters:
#     - days: number of days to calculate stats for (default: 7, max: 365)
#     """
#     current_user_id = get_jwt_identity()
#     session = g.db_session

#     # Get query parameters
#     days = min(int(request.args.get('days', 7)), 365)

#     try:
#         cat_uuid = uuid.UUID(cat_id)
#     except ValueError:
#         return jsonify({"error": "Invalid cat ID format"}), 400

#     # Verify cat ownership
#     cat = session.query(CatInfo).filter(
#         and_(
#             CatInfo.id == cat_uuid,
#             CatInfo.owner_id == uuid.UUID(current_user_id)
#         )
#     ).first()

#     if not cat:
#         return jsonify({"error": "Cat not found or you don't have permission to access this cat's data"}), 404

#     start_date = datetime.now(timezone.utc) - timedelta(days=days)

#     # Get usage statistics
#     stats = (
#         session.query(
#             func.count(LitterboxUsageData.id).label('total_visits'),
#             func.avg(
#                 func.extract('epoch', LitterboxUsageData.exit_time - LitterboxUsageData.enter_time) / 60
#             ).label('avg_duration_minutes'),
#             func.avg(LitterboxUsageData.weight_exit - LitterboxUsageData.weight_enter).label('avg_weight_change'),
#             func.min(LitterboxUsageData.enter_time).label('first_visit'),
#             func.max(LitterboxUsageData.enter_time).label('last_visit')
#         )
#         .join(LitterboxEdgeDeviceInfo, LitterboxUsageData.litterbox_edge_device_id == LitterboxEdgeDeviceInfo.id)
#         .join(LitterboxInfo, LitterboxEdgeDeviceInfo.litterbox_id == LitterboxInfo.id)
#         .filter(
#             and_(
#                 LitterboxInfo.cat_id == cat_uuid,
#                 LitterboxUsageData.enter_time >= start_date
#             )
#         )
#         .first()
#     )

#     # Calculate daily usage pattern (visits per hour of day)
#     hourly_pattern = (
#         session.query(
#             func.extract('hour', LitterboxUsageData.enter_time).label('hour'),
#             func.count(LitterboxUsageData.id).label('visits')
#         )
#         .join(LitterboxEdgeDeviceInfo, LitterboxUsageData.litterbox_edge_device_id == LitterboxEdgeDeviceInfo.id)
#         .join(LitterboxInfo, LitterboxEdgeDeviceInfo.litterbox_id == LitterboxInfo.id)
#         .filter(
#             and_(
#                 LitterboxInfo.cat_id == cat_uuid,
#                 LitterboxUsageData.enter_time >= start_date
#             )
#         )
#         .group_by(func.extract('hour', LitterboxUsageData.enter_time))
#         .all()
#     )

#     return jsonify({
#         "cat_id": str(cat_uuid),
#         "cat_name": cat.name,
#         "period_days": days,
#         "stats": {
#             "total_visits": stats.total_visits or 0,
#             "average_duration_minutes": round(float(stats.avg_duration_minutes or 0), 2),
#             "average_weight_change_grams": round(float(stats.avg_weight_change or 0), 2),
#             "visits_per_day": round((stats.total_visits or 0) / days, 2),
#             "first_visit_in_period": stats.first_visit.isoformat() if stats.first_visit else None,
#             "last_visit_in_period": stats.last_visit.isoformat() if stats.last_visit else None
#         },
#         "hourly_pattern": [{"hour": int(h.hour), "visits": h.visits} for h in hourly_pattern]
#     }), 200


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
app.run(debug=True, host="0.0.0.0", port=8000)
