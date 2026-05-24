from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, DataEntry
from auth import role_required, get_allowed_modules
from datetime import datetime

data_entry_bp = Blueprint('data_entry', __name__)

@data_entry_bp.route('/')
@login_required
@role_required('data_staff')
def list_entries():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    query = DataEntry.query
    if search:
        query = query.filter(
            DataEntry.title.contains(search) |
            DataEntry.entry_category.contains(search)
        )
    entries = query.order_by(DataEntry.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('data_entry/list.html', entries=entries, search=search,
                           modules=get_allowed_modules(current_user))

@data_entry_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('data_staff')
def new_entry():
    if request.method == 'POST':
        entry = DataEntry(
            entry_category=request.form['entry_category'],
            title=request.form['title'],
            content=request.form.get('content', ''),
            entry_date=datetime.strptime(request.form['entry_date'], '%Y-%m-%d').date() if request.form.get('entry_date') else None,
            created_by=current_user.id
        )
        db.session.add(entry)
        db.session.commit()
        flash('数据录入成功', 'success')
        return redirect(url_for('data_entry.list_entries'))
    return render_template('data_entry/form.html', entry=None, modules=get_allowed_modules(current_user))

@data_entry_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('data_staff')
def edit_entry(id):
    entry = DataEntry.query.get_or_404(id)
    if request.method == 'POST':
        entry.entry_category = request.form['entry_category']
        entry.title = request.form['title']
        entry.content = request.form.get('content', '')
        if request.form.get('entry_date'):
            entry.entry_date = datetime.strptime(request.form['entry_date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('数据更新成功', 'success')
        return redirect(url_for('data_entry.list_entries'))
    return render_template('data_entry/form.html', entry=entry, modules=get_allowed_modules(current_user))

@data_entry_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('data_staff')
def delete_entry(id):
    entry = DataEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('data_entry.list_entries'))