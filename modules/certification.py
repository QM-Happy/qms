from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, CertificationRecord
from auth import role_required, get_allowed_modules
from datetime import datetime

cert_bp = Blueprint('certification', __name__)

@cert_bp.route('/')
@login_required
@role_required('qa_staff')
def list_records():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = CertificationRecord.query
    if search:
        query = query.filter(
            CertificationRecord.cert_no.contains(search) |
            CertificationRecord.product_name.contains(search) |
            CertificationRecord.cert_type.contains(search)
        )
    records = query.order_by(CertificationRecord.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('certification/list.html', records=records, search=search,
                           modules=get_allowed_modules(current_user))

@cert_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('qa_staff')
def new_record():
    if request.method == 'POST':
        record = CertificationRecord(
            cert_no=request.form['cert_no'],
            cert_type=request.form.get('cert_type', ''),
            product_name=request.form.get('product_name', ''),
            cert_body=request.form.get('cert_body', ''),
            issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date() if request.form.get('issue_date') else None,
            expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form.get('expiry_date') else None,
            status=request.form.get('status', 'valid'),
            remark=request.form.get('remark', ''),
            created_by=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('认证记录创建成功', 'success')
        return redirect(url_for('certification.list_records'))
    return render_template('certification/form.html', record=None, modules=get_allowed_modules(current_user))

@cert_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('qa_staff')
def edit_record(id):
    record = CertificationRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.cert_no = request.form['cert_no']
        record.cert_type = request.form.get('cert_type', '')
        record.product_name = request.form.get('product_name', '')
        record.cert_body = request.form.get('cert_body', '')
        if request.form.get('issue_date'):
            record.issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date()
        if request.form.get('expiry_date'):
            record.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        record.status = request.form.get('status', 'valid')
        record.remark = request.form.get('remark', '')
        db.session.commit()
        flash('认证记录更新成功', 'success')
        return redirect(url_for('certification.list_records'))
    return render_template('certification/form.html', record=record, modules=get_allowed_modules(current_user))

@cert_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('qa_staff')
def delete_record(id):
    record = CertificationRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('certification.list_records'))