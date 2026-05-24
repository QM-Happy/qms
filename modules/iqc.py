from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, IQCRecord, Supplier
from auth import role_required, get_allowed_modules
from datetime import datetime

iqc_bp = Blueprint('iqc', __name__)

@iqc_bp.route('/')
@login_required
@role_required('iqc_staff')
def list_records():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = IQCRecord.query
    if search:
        query = query.filter(
            IQCRecord.material_name.contains(search) |
            IQCRecord.material_code.contains(search) |
            IQCRecord.batch_no.contains(search) |
            IQCRecord.record_no.contains(search)
        )
    records = query.order_by(IQCRecord.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('iqc/list.html', records=records, search=search,
                           modules=get_allowed_modules(current_user))

@iqc_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('iqc_staff')
def new_record():
    if request.method == 'POST':
        record = IQCRecord(
            record_no=request.form['record_no'],
            supplier_id=request.form.get('supplier_id') or None,
            material_name=request.form['material_name'],
            material_code=request.form.get('material_code', ''),
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
        return redirect(url_for('iqc.list_records'))
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('iqc/form.html', record=None, suppliers=suppliers,
                           modules=get_allowed_modules(current_user))

@iqc_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('iqc_staff')
def edit_record(id):
    record = IQCRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.record_no = request.form['record_no']
        record.supplier_id = request.form.get('supplier_id') or None
        record.material_name = request.form['material_name']
        record.material_code = request.form.get('material_code', '')
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
        return redirect(url_for('iqc.list_records'))
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('iqc/form.html', record=record, suppliers=suppliers,
                           modules=get_allowed_modules(current_user))

@iqc_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('iqc_staff')
def delete_record(id):
    record = IQCRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('iqc.list_records'))