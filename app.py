import os
from datetime import datetime
from flask import Flask, render_template, session
from flask_wtf.csrf import CSRFProtect

from config import config_by_name
from repositories import user_repo, get_datastore, use_mongo
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.patient import patient_bp
from blueprints.doctor import doctor_bp
from blueprints.appointments import appointments_bp

csrf = CSRFProtect()

def create_app(config_name=None):
    """Application factory for MediConnect."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions
    csrf.init_app(app)

    # Ensure uploads folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize data store from seed data
    get_datastore(app.config['SEED_DATA_PATH'])

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(appointments_bp)

    # Context processors for all Jinja2 templates
    @app.context_processor
    def inject_global_data():
        current_user = None
        user_id = session.get('user_id')
        if user_id:
            current_user = user_repo.get_by_id(user_id)
        
        return {
            'current_user': current_user,
            'current_year': datetime.utcnow().year,
            'user_role': session.get('user_role'),
            'user_name': session.get('user_name'),
            'use_mongo': use_mongo,
            'has_mongo_uri': bool(os.environ.get('MONGO_URI'))
        }

    # Custom template filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"\u20b9{float(val):,.0f}"
        except (ValueError, TypeError):
            return f"\u20b9{val}"

    # Error handlers
    from flask_wtf.csrf import CSRFError
    from werkzeug.exceptions import HTTPException
    from flask import request, flash, redirect, url_for

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('Your session expired. Please submit the form again.', 'warning')
        ref = request.referrer
        if ref and ref != request.url:
            return redirect(ref)
        return redirect(request.url)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/404.html', message="403 Forbidden: You don't have permission to access this resource."), 403

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/500.html', message="Uploaded image is too large. Max file size is 5MB."), 413

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        if e.code == 404:
            return render_template('errors/404.html'), 404
        if e.code == 403:
            return render_template('errors/404.html', message=e.description), 403
        return render_template('errors/500.html', message=e.description), e.code

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        import traceback
        err_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Unhandled App Exception] {err_msg}\n{traceback.format_exc()}")
        return render_template('errors/500.html', message=err_msg), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
