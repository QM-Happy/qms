from flask import Blueprint, render_template
from flask_login import login_required, current_user
from auth import get_allowed_modules

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    modules = get_allowed_modules(current_user)
    return render_template('dashboard.html', modules=modules)