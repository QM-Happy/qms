import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User
from auth import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)

    # 主页
    from modules.main import main_bp
    app.register_blueprint(main_bp)

    # 各功能模块
    from modules.iqc import iqc_bp
    app.register_blueprint(iqc_bp, url_prefix='/iqc')

    from modules.fqc import fqc_bp
    app.register_blueprint(fqc_bp, url_prefix='/fqc')

    from modules.quality_issues import issues_bp
    app.register_blueprint(issues_bp, url_prefix='/quality-issues')

    from modules.certification import cert_bp
    app.register_blueprint(cert_bp, url_prefix='/certification')

    from modules.sealed_samples import sealed_bp
    app.register_blueprint(sealed_bp, url_prefix='/sealed-samples')

    from modules.data_entry import data_entry_bp
    app.register_blueprint(data_entry_bp, url_prefix='/data-entry')

    from modules.supplier import supplier_bp
    app.register_blueprint(supplier_bp, url_prefix='/supplier')

    from modules.nexfactory import nexfactory_bp
    app.register_blueprint(nexfactory_bp, url_prefix='/nexfactory')

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app

def _seed_admin(app):
    """初始化管理员账户"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            display_name='系统管理员',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5050)