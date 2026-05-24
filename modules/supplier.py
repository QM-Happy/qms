from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Supplier, SupplierSubmission
from auth import role_required, get_allowed_modules
from datetime import datetime

supplier_bp = Blueprint('supplier', __name__)

# ── 供应商列表（管理员可见） ──
@supplier_bp.route('/')
@login_required
def portal():
    modules = get_allowed_modules(current_user)
    if current_user.role == 'supplier':
        # 供应商只看自己的提交
        submissions = SupplierSubmission.query.filter_by(supplier_id=current_user.supplier_id)\
            .order_by(SupplierSubmission.created_at.desc()).all()
        supplier_info = Supplier.query.get(current_user.supplier_id)
        return render_template('supplier/portal.html', submissions=submissions,
                               supplier=supplier_info, modules=modules)
    # 管理员/内部人员看全部，支持按供应商和状态筛选
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    filter_supplier = request.args.get('supplier_id', '').strip()
    filter_status = request.args.get('status', '').strip()
    query = SupplierSubmission.query
    if search:
        query = query.filter(
            SupplierSubmission.title.contains(search) |
            SupplierSubmission.submission_type.contains(search)
        )
    if filter_supplier:
        query = query.filter(SupplierSubmission.supplier_id == int(filter_supplier))
    if filter_status:
        query = query.filter(SupplierSubmission.status == filter_status)
    submissions = query.order_by(SupplierSubmission.created_at.desc()).paginate(page=page, per_page=20)
    all_suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('supplier/admin_list.html', submissions=submissions,
                           search=search, suppliers=all_suppliers,
                           filter_supplier=filter_supplier, filter_status=filter_status,
                           modules=modules)

# ── 供应商提交新数据 ──
@supplier_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        submission = SupplierSubmission(
            supplier_id=current_user.supplier_id,
            submission_type=request.form.get('submission_type', 'other'),
            title=request.form['title'],
            content=request.form.get('content', ''),
            status='submitted',
            submitted_date=datetime.strptime(request.form['submitted_date'], '%Y-%m-%d').date() if request.form.get('submitted_date') else None,
            created_by=current_user.id
        )
        db.session.add(submission)
        db.session.commit()
        flash('数据提交成功，等待审核', 'success')
        return redirect(url_for('supplier.portal'))
    return render_template('supplier/submit.html', modules=get_allowed_modules(current_user))

# ── 审核供应商提交（管理员） ──
@supplier_bp.route('/review/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def review(id):
    submission = SupplierSubmission.query.get_or_404(id)
    if request.method == 'POST':
        submission.status = request.form['status']
        submission.review_comment = request.form.get('review_comment', '')
        db.session.commit()
        flash('审核完成', 'success')
        return redirect(url_for('supplier.portal'))
    return render_template('supplier/review.html', submission=submission,
                           modules=get_allowed_modules(current_user))

# ── 供应商管理（管理员） ──
@supplier_bp.route('/manage-suppliers')
@login_required
@role_required('admin')
def manage_suppliers():
    from models import User
    all_suppliers = Supplier.query.order_by(Supplier.name).all()
    # 获取每个供应商的用户账户
    supplier_users = {}
    for s in all_suppliers:
        users = User.query.filter_by(supplier_id=s.id).all()
        supplier_users[s.id] = users
    return render_template('supplier/manage.html', suppliers=all_suppliers,
                           supplier_users=supplier_users,
                           modules=get_allowed_modules(current_user))

@supplier_bp.route('/manage-suppliers/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_supplier():
    if request.method == 'POST':
        supplier = Supplier(
            code=request.form['code'],
            name=request.form['name'],
            contact_person=request.form.get('contact_person', ''),
            contact_phone=request.form.get('contact_phone', ''),
            contact_email=request.form.get('contact_email', ''),
            address=request.form.get('address', '')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('供应商创建成功', 'success')
        return redirect(url_for('supplier.manage_suppliers'))
    return render_template('supplier/supplier_form.html', supplier=None,
                           modules=get_allowed_modules(current_user))

@supplier_bp.route('/manage-suppliers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier.code = request.form['code']
        supplier.name = request.form['name']
        supplier.contact_person = request.form.get('contact_person', '')
        supplier.contact_phone = request.form.get('contact_phone', '')
        supplier.contact_email = request.form.get('contact_email', '')
        supplier.address = request.form.get('address', '')
        supplier.is_active = 'is_active' in request.form
        db.session.commit()
        flash('供应商更新成功', 'success')
        return redirect(url_for('supplier.manage_suppliers'))
    return render_template('supplier/supplier_form.html', supplier=supplier,
                           modules=get_allowed_modules(current_user))

# ── 用户管理（管理员） ──
@supplier_bp.route('/manage-users')
@login_required
@role_required('admin')
def manage_users():
    from models import User
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('supplier/users.html', users=all_users, suppliers=all_suppliers,
                           modules=get_allowed_modules(current_user))

@supplier_bp.route('/manage-users/new', methods=['POST'])
@login_required
@role_required('admin')
def new_user():
    from models import User
    user = User(
        username=request.form['username'],
        display_name=request.form['display_name'],
        role=request.form['role']
    )
    user.set_password(request.form['password'])
    if request.form.get('supplier_id'):
        user.supplier_id = int(request.form['supplier_id'])
    db.session.add(user)
    db.session.commit()
    flash('用户创建成功', 'success')
    return redirect(url_for('supplier.manage_users'))

@supplier_bp.route('/manage-users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(id):
    from models import User
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.display_name = request.form['display_name']
        user.role = request.form['role']
        user.supplier_id = int(request.form['supplier_id']) if request.form.get('supplier_id') else None
        if request.form.get('password'):
            user.set_password(request.form['password'])
        user.is_active = 'is_active' in request.form
        db.session.commit()
        flash('用户更新成功', 'success')
        return redirect(url_for('supplier.manage_users'))
    all_suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('supplier/user_edit.html', u=user, suppliers=all_suppliers,
                           modules=get_allowed_modules(current_user))

@supplier_bp.route('/manage-users/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(id):
    from models import User
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能停用自己', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash('用户状态已更新', 'success')
    return redirect(url_for('supplier.manage_users'))

# ── 一键创建供应商 + 登录账户 ──
@supplier_bp.route('/create-supplier-account', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_supplier_account():
    if request.method == 'POST':
        # 1. 创建供应商
        supplier = Supplier(
            code=request.form['code'],
            name=request.form['name'],
            contact_person=request.form.get('contact_person', ''),
            contact_phone=request.form.get('contact_phone', ''),
            contact_email=request.form.get('contact_email', ''),
            address=request.form.get('address', '')
        )
        db.session.add(supplier)
        db.session.flush()  # 获取 supplier.id

        # 2. 创建登录账户
        from models import User
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username and password:
            user = User(
                username=username,
                display_name=request.form.get('display_name', supplier.name),
                role='supplier',
                supplier_id=supplier.id
            )
            user.set_password(password)
            db.session.add(user)

        db.session.commit()
        flash(f'供应商「{supplier.name}」及登录账户创建成功', 'success')
        return redirect(url_for('supplier.manage_suppliers'))
    return render_template('supplier/create_account.html', modules=get_allowed_modules(current_user))