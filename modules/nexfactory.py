from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, NexfactoryData
from auth import role_required, get_allowed_modules
from datetime import datetime

nexfactory_bp = Blueprint('nexfactory', __name__)

@nexfactory_bp.route('/')
@login_required
@role_required('nexfactory')
def index():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = NexfactoryData.query
    if search:
        query = query.filter(
            NexfactoryData.title.contains(search) |
            NexfactoryData.record_type.contains(search)
        )
    records = query.order_by(NexfactoryData.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('nexfactory/list.html', records=records, search=search,
                           modules=get_allowed_modules(current_user))

@nexfactory_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('nexfactory')
def new_record():
    if request.method == 'POST':
        record = NexfactoryData(
            record_type=request.form.get('record_type', ''),
            title=request.form['title'],
            content=request.form.get('content', ''),
            record_date=datetime.strptime(request.form['record_date'], '%Y-%m-%d').date() if request.form.get('record_date') else None,
            created_by=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('记录创建成功', 'success')
        return redirect(url_for('nexfactory.index'))
    return render_template('nexfactory/form.html', record=None, modules=get_allowed_modules(current_user))

@nexfactory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('nexfactory')
def edit_record(id):
    record = NexfactoryData.query.get_or_404(id)
    if request.method == 'POST':
        record.record_type = request.form.get('record_type', '')
        record.title = request.form['title']
        record.content = request.form.get('content', '')
        if request.form.get('record_date'):
            record.record_date = datetime.strptime(request.form['record_date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('记录更新成功', 'success')
        return redirect(url_for('nexfactory.index'))
    return render_template('nexfactory/form.html', record=record, modules=get_allowed_modules(current_user))

@nexfactory_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('nexfactory')
def delete_record(id):
    record = NexfactoryData.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('nexfactory.index'))