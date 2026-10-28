from functools import wraps
from flask import session, redirect, url_for, flash, request
from repositories import user_repo

def get_current_user():
    """Retrieve currently authenticated user dict from session, or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    try:
        user = user_repo.get_by_id(user_id)
        if user:
            return user
    except Exception:
        pass

    # Safe fallback using session info if worker restart occurred
    if session.get('user_name') and session.get('user_role'):
        return {
            'id': user_id,
            'name': session.get('user_name'),
            'role': session.get('user_role'),
            'email': session.get('user_email', ''),
            'city': 'Mumbai'
        }
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Ensure user has a specific role ('patient' or 'doctor')."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('user_role')
            if user_role != required_role:
                flash(f'Access denied. This page is only accessible by {required_role}s.', 'danger')
                if user_role == 'doctor':
                    return redirect(url_for('doctor.dashboard'))
                elif user_role == 'patient':
                    return redirect(url_for('patient.dashboard'))
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
