from flask import Blueprint, render_template, request, jsonify
from repositories import doctor_repo

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    cities = doctor_repo.get_all_cities()
    specializations = doctor_repo.get_all_specializations()
    # Featured top rated doctors for landing showcase
    featured_doctors = doctor_repo.search(sort_by='rating')[:6]
    return render_template(
        'index.html',
        cities=cities,
        specializations=specializations,
        featured_doctors=featured_doctors
    )

@main_bp.route('/search')
def search():
    city = request.args.get('city', '').strip()
    specialization = request.args.get('specialization', '').strip()
    doctor_type = request.args.get('doctor_type', '').strip()
    sort_by = request.args.get('sort_by', 'rating').strip()
    query = request.args.get('q', '').strip()

    min_fee_arg = request.args.get('min_fee')
    max_fee_arg = request.args.get('max_fee')

    min_fee = float(min_fee_arg) if min_fee_arg and min_fee_arg.isnumeric() else None
    max_fee = float(max_fee_arg) if max_fee_arg and max_fee_arg.isnumeric() else None

    doctors = doctor_repo.search(
        city=city if city else None,
        specialization=specialization if specialization else None,
        doctor_type=doctor_type if doctor_type else None,
        min_fee=min_fee,
        max_fee=max_fee,
        sort_by=sort_by,
        search_term=query if query else None
    )

    all_cities = doctor_repo.get_all_cities()
    all_specs = doctor_repo.get_all_specializations()

    return render_template(
        'search.html',
        doctors=doctors,
        selected_city=city,
        selected_spec=specialization,
        selected_type=doctor_type,
        selected_sort=sort_by,
        selected_min_fee=min_fee_arg or '',
        selected_max_fee=max_fee_arg or '',
        query=query,
        cities=all_cities,
        specializations=all_specs,
        total_results=len(doctors)
    )

@main_bp.route('/doctor/<doctor_id>')
def doctor_detail(doctor_id):
    doctor = doctor_repo.get_by_id(doctor_id)
    if not doctor:
        return render_template('errors/404.html', message="Doctor profile not found"), 404
    
    # Get similar doctors in same city or specialty
    similar_doctors = [
        d for d in doctor_repo.search(city=doctor.get('city'))
        if d['id'] != doctor_id
    ][:3]

    return render_template(
        'doctor_detail.html',
        doctor=doctor,
        similar_doctors=similar_doctors
    )

@main_bp.route('/api/cities')
def api_cities():
    """Autocomplete JSON API for city search input."""
    q = request.args.get('q', '').strip().lower()
    cities = doctor_repo.get_all_cities()
    if q:
        matched = [c for c in cities if q in c.lower()]
    else:
        matched = cities
    resp = jsonify({"cities": matched})
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@main_bp.route('/api/health')
def api_health():
    """Diagnostic health-check endpoint for database and backend configuration."""
    import os, re
    from repositories import user_repo, use_mongo, mongo_connection_error
    
    raw_uri = os.environ.get("MONGO_URI", "")
    sanitized_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', raw_uri) if raw_uri else None

    info = {
        "status": "online",
        "backend_env": os.environ.get("DATA_BACKEND", "not_set"),
        "use_mongo": use_mongo,
        "repo_type": type(user_repo).__name__,
        "has_mongo_uri": bool(raw_uri),
        "mongo_target": sanitized_uri,
        "database_name": os.environ.get("DATABASE_NAME", "findmydoc"),
        "mongo_connection_error": mongo_connection_error
    }
    if use_mongo:
        try:
            from repositories.mongo_repository import MongoDatabaseClient
            client = MongoDatabaseClient.get_instance()
            client.db.command('ping')
            info["mongodb_ping"] = "ok"
        except Exception as e:
            info["mongodb_ping"] = f"error: {str(e)}"
    return jsonify(info)
