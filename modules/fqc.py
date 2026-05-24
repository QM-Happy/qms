from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, FQCRecord
from auth import role_required, get_allowed_modules
from datetime import datetime

fqc_bp = Blueprint('fqc', __name__)

@fqc_bp.route('/')
@login_required
@role_required('fqc_staff')
def list_records():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = FQCRecord.query
    if search:
        query = query.filter(
            FQCRecord.product_name.contains(search) |
            FQCRecord.product_code.contains(search) |
            FQCRecord.batch_no.contains(search) |
            FQCRecord.record_no.contains(search)
        )
    records = query.order_by(FQCRecord.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('fqc/list.html', records=records, search=search,
                           modules=get_allowed_modules(current_user))

@fqc_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('fqc_staff')
def new_record():
    if request.method == 'POST':
        record = FQCRecord(
            record_no=request.form['record_no'],
            product_name=request.form['product_name'],
            product_code=request.form.get('product_code', ''),
            batch_no=request.form.get('batch_no', ''),
            quantity=float(request.form.get('quantity', 0) or 0),
            sample_qty=float(request.form.get('sample_qty', 0) or 0),
            inspection_result=request.form.get('inspection_result', ''),
            inspector=request.form.get('inspector', ''),
            inspection_date=datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date() if request.form.get('inspection_date') else None,
            remark=request.form.get('remark', ''),
            created_by=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('记录创建成功', 'success')
        return redirect(url_for('fqc.list_records'))
    return render_template('fqc/form.html', record=None, modules=get_allowed_modules(current_user))

@fqc_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('fqc_staff')
def edit_record(id):
    record = FQCRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.record_no = request.form['record_no']
        record.product_name = request.form['product_name']
        record.product_code = request.form.get('product_code', '')
        record.batch_no = request.form.get('batch_no', '')
        record.quantity = float(request.form.get('quantity', 0) or 0)
        record.sample_qty = float(request.form.get('sample_qty', 0) or 0)
        record.inspection_result = request.form.get('inspection_result', '')
        record.inspector = request.form.get('inspector', '')
        if request.form.get('inspection_date'):
            record.inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
        record.remark = request.form.get('remark', '')
        db.session.commit()
        flash('记录更新成功', 'success')
        return redirect(url_for('fqc.list_records'))
    return render_template('fqc/form.html', record=record, modules=get_allowed_modules(current_user))

@fqc_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('fqc_staff')
def delete_record(id):
    record = FQCRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('fqc.list_records'))