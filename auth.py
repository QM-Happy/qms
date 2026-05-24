from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# ── 角色权限映射：每个角色可访问的模块 ──
ROLE_MODULES = {
    'admin': ['dashboard', 'iqc', 'fqc', 'quality_issues', 'certification', 'sealed_samples', 'data_entry', 'supplier', 'nexfactory', 'admin_users'],
    'iqc_staff': ['dashboard', 'iqc'],
    'fqc_staff': ['dashboard', 'fqc'],
    'qa_staff': ['dashboard', 'quality_issues', 'certification'],
    'data_staff': ['dashboard', 'data_entry'],
    'sealed_admin': ['dashboard', 'sealed_samples'],
    'supplier': ['dashboard', 'supplier'],
    'nexfactory': ['dashboard', 'nexfactory'],
    'viewer': ['dashboard'],
}

def role_required(*roles):
    """装饰器：限制只有特定角色可访问"""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles and current_user.role != 'admin':
                flash('你没有权限访问此页面', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def get_allowed_modules(user):
    """返回用户可访问的模块列表"""
    return ROLE_MODULES.get(user.role, ['dashboard'])

# ── 路由 ──
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('用户名或密码错误', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))