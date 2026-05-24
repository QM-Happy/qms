from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SealedSample, Supplier
from auth import role_required, get_allowed_modules
from datetime import datetime

sealed_bp = Blueprint('sealed_samples', __name__)

@sealed_bp.route('/')
@login_required
@role_required('sealed_admin')
def list_samples():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = SealedSample.query
    if search:
        query = query.filter(
            SealedSample.sample_no.contains(search) |
            SealedSample.sample_name.contains(search) |
            SealedSample.product_code.contains(search)
        )
    samples = query.order_by(SealedSample.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('sealed_samples/list.html', samples=samples, search=search,
                           modules=get_allowed_modules(current_user))

@sealed_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('sealed_admin')
def new_sample():
    if request.method == 'POST':
        sample = SealedSample(
            sample_no=request.form['sample_no'],
            sample_name=request.form['sample_name'],
            supplier_id=request.form.get('supplier_id') or None,
            product_code=request.form.get('product_code', ''),
            seal_date=datetime.strptime(request.form['seal_date'], '%Y-%m-%d').date() if request.form.get('seal_date') else None,
            storage_location=request.form.get('storage_location', ''),
            sample_qty=int(request.form.get('sample_qty', 0) or 0),
            status=request.form.get('status', 'active'),
            remark=request.form.get('remark', ''),
            created_by=current_user.id
        )
        db.session.add(sample)
        db.session.commit()
        flash('封样记录创建成功', 'success')
        return redirect(url_for('sealed_samples.list_samples'))
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('sealed_samples/form.html', sample=None, suppliers=suppliers,
                           modules=get_allowed_modules(current_user))

@sealed_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('sealed_admin')
def edit_sample(id):
    sample = SealedSample.query.get_or_404(id)
    if request.method == 'POST':
        sample.sample_no = request.form['sample_no']
        sample.sample_name = request.form['sample_name']
        sample.supplier_id = request.form.get('supplier_id') or None
        sample.product_code = request.form.get('product_code', '')
        if request.form.get('seal_date'):
            sample.seal_date = datetime.strptime(request.form['seal_date'], '%Y-%m-%d').date()
        sample.storage_location = request.form.get('storage_location', '')
        sample.sample_qty = int(request.form.get('sample_qty', 0) or 0)
        sample.status = request.form.get('status', 'active')
        sample.remark = request.form.get('remark', '')
        db.session.commit()
        flash('封样记录更新成功', 'success')
        return redirect(url_for('sealed_samples.list_samples'))
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('sealed_samples/form.html', sample=sample, suppliers=suppliers,
                           modules=get_allowed_modules(current_user))

@sealed_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('sealed_admin')
def delete_sample(id):
    sample = SealedSample.query.get_or_404(id)
    db.session.delete(sample)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('sealed_samples.list_samples'))