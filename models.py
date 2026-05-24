from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime, date

db = SQLAlchemy()

# ── User & Supplier ──
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False, default='viewer')
    # 供应商用户绑定的供应商 ID（仅 role=supplier 时有值）
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='users', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def has_role(self, *roles):
        return self.role in roles

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(256), nullable=False)
    contact_person = db.Column(db.String(128))
    contact_phone = db.Column(db.String(32))
    contact_email = db.Column(db.String(128))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── IQC 来料检验 ──
class IQCRecord(db.Model):
    __tablename__ = 'iqc_records'
    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    material_name = db.Column(db.String(256), nullable=False)
    material_code = db.Column(db.String(128))
    batch_no = db.Column(db.String(128))
    quantity = db.Column(db.Float)
    sample_qty = db.Column(db.Float)
    inspection_result = db.Column(db.String(32))  # pass / fail / conditional
    inspector = db.Column(db.String(128))
    inspection_date = db.Column(db.Date, default=date.today)
    remark = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='iqc_records', lazy=True)

# ── FQC 最终检验 ──
class FQCRecord(db.Model):
    __tablename__ = 'fqc_records'
    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    product_name = db.Column(db.String(256), nullable=False)
    product_code = db.Column(db.String(128))
    batch_no = db.Column(db.String(128))
    quantity = db.Column(db.Float)
    sample_qty = db.Column(db.Float)
    inspection_result = db.Column(db.String(32))
    inspector = db.Column(db.String(128))
    inspection_date = db.Column(db.Date, default=date.today)
    remark = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── 内外部质量问题 ──
class QualityIssue(db.Model):
    __tablename__ = 'quality_issues'
    id = db.Column(db.Integer, primary_key=True)
    issue_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    issue_type = db.Column(db.String(32))  # internal / external / customer_complaint
    source = db.Column(db.String(256))
    product_name = db.Column(db.String(256))
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(32))  # critical / major / minor
    root_cause = db.Column(db.Text)
    corrective_action = db.Column(db.Text)
    status = db.Column(db.String(32), default='open')  # open / investigating / closed
    reported_date = db.Column(db.Date, default=date.today)
    closed_date = db.Column(db.Date, nullable=True)
    responsible_person = db.Column(db.String(128))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── 认证与测试 ──
class CertificationRecord(db.Model):
    __tablename__ = 'certifications'
    id = db.Column(db.Integer, primary_key=True)
    cert_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    cert_type = db.Column(db.String(64))  # UL / CE / FCC / RoHS / ...
    product_name = db.Column(db.String(256))
    cert_body = db.Column(db.String(256))  # 认证机构
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(32), default='valid')  # valid / expiring / expired
    remark = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── 封样管理 ──
class SealedSample(db.Model):
    __tablename__ = 'sealed_samples'
    id = db.Column(db.Integer, primary_key=True)
    sample_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    sample_name = db.Column(db.String(256), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    product_code = db.Column(db.String(128))
    seal_date = db.Column(db.Date)
    storage_location = db.Column(db.String(256))
    sample_qty = db.Column(db.Integer)
    status = db.Column(db.String(32), default='active')  # active / returned / scrapped
    remark = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='sealed_samples', lazy=True)

# ── 通用数据录入 ──
class DataEntry(db.Model):
    __tablename__ = 'data_entries'
    id = db.Column(db.Integer, primary_key=True)
    entry_category = db.Column(db.String(64), nullable=False)  # 自定义分类
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text)
    entry_date = db.Column(db.Date, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ── 供应商门户数据 ──
class SupplierSubmission(db.Model):
    __tablename__ = 'supplier_submissions'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False, index=True)
    submission_type = db.Column(db.String(64))  # 8D_report / inspection_report / corrective_action / other
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text)
    attachment_path = db.Column(db.String(512))
    status = db.Column(db.String(32), default='submitted')  # submitted / reviewed / approved / rejected
    review_comment = db.Column(db.Text)
    submitted_date = db.Column(db.Date, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='submissions', lazy=True)

# ── Nexfactory ──
class NexfactoryData(db.Model):
    __tablename__ = 'nexfactory_data'
    id = db.Column(db.Integer, primary_key=True)
    record_type = db.Column(db.String(64))
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text)
    record_date = db.Column(db.Date, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)