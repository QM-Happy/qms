from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, QualityIssue
from auth import role_required, get_allowed_modules
from datetime import datetime

issues_bp = Blueprint('quality_issues', __name__)

@issues_bp.route('/')
@login_required
@role_required('qa_staff')
def list_issues():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    query = QualityIssue.query
    if search:
        query = query.filter(
            QualityIssue.issue_no.contains(search) |
            QualityIssue.product_name.contains(search) |
            QualityIssue.description.contains(search)
        )
    if status_filter:
        query = query.filter(QualityIssue.status == status_filter)
    issues = query.order_by(QualityIssue.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('quality_issues/list.html', issues=issues, search=search, status_filter=status_filter,
                           modules=get_allowed_modules(current_user))

@issues_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('qa_staff')
def new_issue():
    if request.method == 'POST':
        issue = QualityIssue(
            issue_no=request.form['issue_no'],
            issue_type=request.form.get('issue_type', ''),
            source=request.form.get('source', ''),
            product_name=request.form.get('product_name', ''),
            description=request.form['description'],
            severity=request.form.get('severity', ''),
            root_cause=request.form.get('root_cause', ''),
            corrective_action=request.form.get('corrective_action', ''),
            status=request.form.get('status', 'open'),
            reported_date=datetime.strptime(request.form['reported_date'], '%Y-%m-%d').date() if request.form.get('reported_date') else None,
            responsible_person=request.form.get('responsible_person', ''),
            created_by=current_user.id
        )
        db.session.add(issue)
        db.session.commit()
        flash('问题记录创建成功', 'success')
        return redirect(url_for('quality_issues.list_issues'))
    return render_template('quality_issues/form.html', issue=None, modules=get_allowed_modules(current_user))

@issues_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('qa_staff')
def edit_issue(id):
    issue = QualityIssue.query.get_or_404(id)
    if request.method == 'POST':
        issue.issue_no = request.form['issue_no']
        issue.issue_type = request.form.get('issue_type', '')
        issue.source = request.form.get('source', '')
        issue.product_name = request.form.get('product_name', '')
        issue.description = request.form['description']
        issue.severity = request.form.get('severity', '')
        issue.root_cause = request.form.get('root_cause', '')
        issue.corrective_action = request.form.get('corrective_action', '')
        issue.status = request.form.get('status', 'open')
        if request.form.get('reported_date'):
            issue.reported_date = datetime.strptime(request.form['reported_date'], '%Y-%m-%d').date()
        if request.form.get('closed_date'):
            issue.closed_date = datetime.strptime(request.form['closed_date'], '%Y-%m-%d').date()
        issue.responsible_person = request.form.get('responsible_person', '')
        db.session.commit()
        flash('问题记录更新成功', 'success')
        return redirect(url_for('quality_issues.list_issues'))
    return render_template('quality_issues/form.html', issue=issue, modules=get_allowed_modules(current_user))

@issues_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('qa_staff')
def delete_issue(id):
    issue = QualityIssue.query.get_or_404(id)
    db.session.delete(issue)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('quality_issues.list_issues'))