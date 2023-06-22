import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Consultant, Manager, ManagerType, Client, Project, Task, Assignment, ProjectStage
from sqlalchemy import cast, Date
from werkzeug.security import check_password_hash
from datetime import *
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import json
import plotly
import plotly.express as px




basedir = os.path.abspath(os.path.dirname(__file__)) # tell me the directory of my current directory

app = Flask(__name__)
app.secret_key = 'para session key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'para.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key'

UPLOAD_FOLDER = 'static/images/employees/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login' # default login route
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    if session['perm'] == 'consultant':
        return Consultant.query.get(int(user_id))
    elif session['perm'] in ['manager', 'project manager']:
        return Manager.query.get(int(user_id))
    else:
        return None

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    session['perm'] = ''

    # Determine the user type for the session
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Consultant.query.filter_by(email=email).first()
        session['perm'] = 'consultant'
        if not user:
            user = Manager.query.filter_by(email=email).first()
            if user:
                if user.manager_type_id == 1:
                    session['perm'] = 'manager'
                elif user.manager_type_id == 2:
                    session['perm'] = 'project manager'
            else:
                flash(f'Your login information was not correct. Please try again.', 'error') #need to edit login page
        if user:
            if check_password_hash(user.password, password):
                login_user(user) #this sets the current_user variable
                return redirect(url_for('dashboard'))
            else:
                flash(f'Incorrect password. Please try again.')
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(f'You\'ve been successfully logged out!')
    return redirect(url_for('login'))


@app.route('/dashboard2')
@login_required
def dashboard2():
    if session['perm'] == 'consultant':
        assignments = Assignment.query.filter_by(consultant_id=current_user.consultant_id).all()
        tasks = Task.query.outerjoin(Project, Project.project_id == Task.project_id).outerjoin(Assignment, Assignment.project_id == Project.project_id).add_entity(Project).filter_by(consultant_id=current_user.consultant_id).all()
        return render_template('dashboard2.html', assignments=assignments, tasks=tasks)
    if session['perm'] == 'manager':
        projects = Project.query.filter_by(manager_id=current_user.manager_id).all()
        tasks = Task.query.outerjoin(Project, Project.project_id == Task.project_id).add_entity(Project).filter_by(manager_id=current_user.manager_id).all()
        assignments = Assignment.query.outerjoin(Project, Project.project_id == Assignment.project_id).filter_by(manager_id=current_user.manager_id).all()
        return render_template('dashboard2.html', assignments=assignments, tasks=tasks, projects=projects)
    if session['perm'] == 'project manager':
        projects = Project.query.all()
        tasks = Task.query.outerjoin(Project, Project.project_id == Task.project_id).add_entity(Project).all()
        assignments = Assignment.query.outerjoin(Project, Project.project_id == Assignment.project_id).all()
        return render_template('dashboard2.html', assignments=assignments, tasks=tasks, projects=projects)


@app.route('/dashboard')
@login_required
def dashboard():
    if session['perm'] == 'consultant':
        tasks = Task.query.outerjoin(Project, Project.project_id == Task.project_id).outerjoin(Assignment, Assignment.project_id == Project.project_id)\
            .filter_by(consultant_id=current_user.consultant_id).all()
        assignments = Assignment.query.filter_by(consultant_id=current_user.consultant_id).all()

        projects_for_dict = Project.query.outerjoin(Assignment, Assignment.project_id == Project.project_id).filter_by(consultant_id=current_user.consultant_id).outerjoin(ProjectStage, ProjectStage.stage_id == Project.stage_id).add_entity(ProjectStage).all()

        project_stage_dict = {i.project_stage:0 for i in ProjectStage.query.all()}

        for project, stage in projects_for_dict:
            project_stage_dict[stage.project_stage] = project_stage_dict.get(stage.project_stage,0) + 1

        mydf = pd.DataFrame(project_stage_dict.items(), columns=['stage', 'count'])

        project_stage_chart = px.pie(data_frame=mydf, names='stage', values='count', title='Projects by Project Stage')

        project_stage_chart.update_traces(textposition='inside', textinfo='percent', textfont_size=16, sort=False)
        project_stage_chart.update_layout(title={'x': 0.5})

        graphJSON = json.dumps(project_stage_chart, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('dashboard.html', tasks=tasks, assignments=assignments, graphJSON=graphJSON)

    elif session['perm'] == 'manager':
        assignments = Assignment.query.outerjoin(Project, Project.project_id == Assignment.project_id).filter_by(manager_id=current_user.manager_id).all()
        projects = Project.query.filter_by(manager_id=current_user.manager_id).all()
        working_employees = Consultant.query.all()
        assignment_hours = {i.consultant_id: 0 for i in working_employees}
        tasks = Task.query.outerjoin(Project, Project.project_id == Task.project_id).filter_by(manager_id=current_user.manager_id).all()

        for i in assignments:
            assignment_hours[i.consultant_id] = assignment_hours.get(i.consultant_id, 0) + i.hours_worked
        working_employees = Consultant.query.all()
        assignments = Assignment.query.all()

        projects_for_dict = Project.query.filter_by(manager_id=current_user.manager_id).outerjoin(ProjectStage, ProjectStage.stage_id == Project.stage_id).add_entity(ProjectStage).all()

        project_stage_dict = {i.project_stage: 0 for i in ProjectStage.query.all()}

        for project, stage in projects_for_dict:
            project_stage_dict[stage.project_stage] = project_stage_dict.get(stage.project_stage, 0) + 1

        mydf = pd.DataFrame(project_stage_dict.items(), columns=['stage', 'count'])

        project_stage_chart = px.pie(data_frame=mydf, names='stage', values='count', title='Projects by Project Stage')

        project_stage_chart.update_traces(textposition='inside', textinfo='percent', textfont_size=16, sort=False)
        project_stage_chart.update_layout(title={'x': 0.5})

        graphJSON = json.dumps(project_stage_chart, cls=plotly.utils.PlotlyJSONEncoder)


        return render_template('dashboard.html', tasks=tasks, employees=working_employees, assignment_hours=assignment_hours, assignments=assignments, projects=projects, graphJSON=graphJSON)

    else:
        assignments = Assignment.query.all()
        project_for_budget = Project.query.all()
        tasks = Task.query.all()

        working_employees = Manager.query.filter_by(manager_type_id=1).all()
        projects_working = {i.manager_id: 0 for i in working_employees}

        for i in project_for_budget:
            projects_working[i.manager_id] = projects_working.get(i.manager_id, 0) + 1
        working_employees = Manager.query.filter_by(manager_type_id=1).all()

        budget = 0

        for i in project_for_budget:
            budget += i.budget

        projects_for_dict = Project.query.outerjoin(Assignment, Assignment.project_id == Project.project_id).outerjoin(ProjectStage, ProjectStage.stage_id == Project.stage_id).add_entity(ProjectStage).all()

        project_stage_dict = {i.project_stage: 0 for i in ProjectStage.query.all()}

        for project, stage in projects_for_dict:
            project_stage_dict[stage.project_stage] = project_stage_dict.get(stage.project_stage, 0) + 1

        mydf = pd.DataFrame(project_stage_dict.items(), columns=['stage', 'count'])

        project_stage_chart = px.pie(data_frame=mydf, names='stage', values='count', title='Projects by Project Stage')

        project_stage_chart.update_traces(textposition='inside', textinfo='percent', textfont_size=16, sort=False)
        project_stage_chart.update_layout(title={'x': 0.5})

        graphJSON = json.dumps(project_stage_chart, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('dashboard.html', tasks=tasks, employees=working_employees, assignment_hours=projects_working, assignments=assignments, budget=budget, graphJSON=graphJSON)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Set user types for the signup form
    user_types = ['Consultant', 'Manager', 'Project Manager']
    # Validation of PARA user
    if request.method == 'POST':
        user_type = request.form['usertype']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        area_code = request.form['phone'][:3]
        phone = request.form['phone'][3:]
        password = request.form['password']

        consultant_emails = Consultant.query.all()
        manager_emails = Manager.query.all()
        all_emails = []
        for i in consultant_emails:
            all_emails.append(i.email)
        for i in manager_emails:
            all_emails.append(i.email)

        if email[-9:] != '@para.com':
            flash(f'Must signup with a @para.com email address.', category = 'error')
            return redirect(url_for('signup'))
        elif email in all_emails:
            flash(f'Email address already in use. Please use a different email address.', category = 'error')
            return redirect(url_for('signup'))
        if user_type not in ['Manager', 'Project Manager']:
            user = Consultant(first_name=first_name, last_name=last_name, email=email, password=password)
            user.image = 'profile-icon.png'
            user.phone = phone
            user.area_code = area_code
        else:
            if user_type == 'Manager':
                manager_type_id = 1
            else:
                manager_type_id = 2
            user = Manager(first_name=first_name, last_name=last_name, email=email, password=password, manager_type_id=manager_type_id)
            user.image = 'profile-icon.png'
            user.phone = phone
            user.area_code = area_code
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', user_types=user_types)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Information retreival of PARA users

    if request.method == 'POST':
        current_user.first_name = request.form['first_name']
        current_user.last_name = request.form['last_name']

        if request.form['phone']:
            current_user.area_code = request.form['phone'][:3]
            current_user.phone = request.form['phone'][3:]

        if request.files['profile_pic']:
            current_user.image = request.files['profile_pic']
            pic_name = current_user.image.filename
            current_user.image.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            current_user.image = pic_name


            # Update to a new photo or delete the current one on file
        if 'delete_profile_pic' in request.form:
            try:
                os.remove(os.path.join(basedir, app.config['UPLOAD_FOLDER'], current_user.image))
                current_user.image = 'profile-icon.png'
            except:
                pass  # Nothing to do as file is no longer being stored


        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html')


@app.route('/projects', methods=['GET', 'POST'])
@login_required
# Assigning projects to each user type
def projects():
    project_stages = ProjectStage.query.all()
    stages = {}

    for stage in project_stages:
        stages[stage.stage_id] = stage.project_stage

        # retreiving information for client projects
    if request.method == 'POST':
        description = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        budget = request.form['budget']
        poc_first_name = request.form['contact_first_name']
        poc_last_name = request.form['contact_last_name']
        email = request.form['contact_email']
        poc_area_code = request.form['contact_phone'][:3]
        poc_phone = request.form['contact_phone'][3:]
        first_contact_date = datetime.strptime(request.form['first_contact_date'], '%Y-%m-%d')
        # Retreiving new client information
        new_client = Client(poc_first_name=poc_first_name, poc_last_name=poc_last_name, email=email,
                            poc_area_code=poc_area_code, poc_phone=poc_phone, first_contact_date=first_contact_date)
        db.session.add(new_client)
        db.session.commit()

        client = Client.query.filter_by(poc_last_name=poc_last_name, poc_first_name=poc_first_name, email=email).first()

        new_project = Project(manager_id=current_user.manager_id, client_id=client.client_id, description=description,
                              start_date=start_date, end_date=end_date, budget=budget)
        db.session.add(new_project)

        db.session.commit()

        return redirect(url_for('project_information', project_id=new_project.project_id))

    if session['perm'] == 'manager':
        all_projects = Project.query.filter_by(manager_id=current_user.manager_id).all()
        project_assignments = {}

        for project in all_projects:
            project_assignments[project.project_id] = Assignment.query.filter_by(project_id=project.project_id).count()

        return render_template('projects.html', projects=all_projects, project_assignments = project_assignments, stages=stages)


    elif session['perm'] == 'project manager':
        all_projects = Project.query.all()
        return render_template('projects.html', projects=all_projects, stages=stages)
    else:
        all_projects = Project.query.outerjoin(Assignment, Assignment.project_id == Project.project_id)\
            .filter_by(consultant_id=current_user.consultant_id).all()
        all_assignments = Assignment.query.filter_by(consultant_id=current_user.consultant_id).all()
        project_assignments = {}

        for assignment in all_assignments:
            project_assignments[assignment.project_id] = assignment.hours_worked
        return render_template('projects.html', projects=all_projects, project_assignments = project_assignments, stages=stages)


@app.route('/projects/project-information/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project_information(project_id):
    if session['perm'] != 'project manager':
        if session['perm'] == 'consultant':
            c_assignments = [assignment.project_id for assignment in Assignment.query.filter_by(consultant_id=current_user.consultant_id).all()]
        else:
            c_assignments = [project.project_id for project in Project.query.filter_by(manager_id=current_user.manager_id).all()]
        if project_id not in c_assignments:
            return redirect(url_for('error'))

    # Pass all project stages to the info page
    project_stages = ProjectStage.query.order_by(ProjectStage.stage_id).all()

    project = Project.query.filter_by(project_id=project_id).first()
    tasks = Task.query.filter_by(project_id=project_id).all()
    client = Client.query.outerjoin(Project, Project.client_id == Client.client_id)\
        .add_entity(Project).filter_by(project_id=project_id).first()[0]
    consultants = Consultant.query.outerjoin(Assignment, Assignment.consultant_id == Consultant.consultant_id)\
        .filter_by(project_id=project_id).all()
    all_consultants = Consultant.query.all()
    unassigned_consultants = [i for i in all_consultants if i not in consultants]

    if session['perm'] == 'consultant':
        assignments = Assignment.query.filter_by(project_id=project_id, consultant_id=current_user.consultant_id).first()  # hardcoded but needs to be current_user
    else:
        assignments = Assignment.query.filter_by(project_id=project_id).all()


    if request.method == 'POST':
        if 'hours' in request.form:
            assignments.hours_worked = request.form['hours']
        if 'task_text' in request.form:
            task = Task(project_id=project_id, task_content=request.form['task_text'], task_date=datetime.now())
            db.session.add(task)
        if 'name' in request.form and request.form['name']:
            project.description = request.form['name']
        if 'start_date' in request.form and request.form['start_date']:
            project.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        if 'end_date' in request.form and request.form['end_date']:
            project.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        if 'budget' in request.form and request.form['budget']:
            project.budget = request.form['budget']
        if 'contact_first_name' in request.form and request.form['contact_first_name']:
            client.poc_first_name = request.form['contact_first_name']
        if 'contact_last_name' in request.form and request.form['contact_last_name']:
            client.poc_last_name = request.form['contact_last_name']
        if 'contact_email' in request.form and request.form['contact_email']:
            client.email = request.form['contact_email']
        if 'contact_phone' in request.form and request.form['contact_phone']:
            client.poc_area_code = request.form['contact_phone'][:3]
            client.poc_phone = request.form['contact_phone'][3:]
        if 'first_contact_date' in request.form and request.form['first_contact_date']:
            client.first_contact_date = datetime.strptime(request.form['first_contact_date'], '%Y-%m-%d')
        if 'myRadio' in request.form and request.form['myRadio']:
            project.stage_id = request.form['myRadio']



        db.session.commit()

        return redirect(url_for('project_information', project_id=project_id))

    return render_template('project-information.html', stages=project_stages, project=project,
                           assignments=assignments, tasks=tasks, client=client, consultants=consultants,
                           unassigned_consultants=unassigned_consultants)


@app.route('/add-assignee/<int:project_id>-<int:consultant_id>')
@login_required
# Enabling project assignment to different user types
def add_assignee(project_id, consultant_id):
    if session['perm'] != 'manager':
        return redirect(url_for('error'))

    consultants = [i.consultant_id for i in Consultant.query.all()]
    project_ids = [i.project_id for i in Project.query.filter_by(manager_id=current_user.manager_id).all()]

    if project_id not in project_ids or consultant_id not in consultants:
        return redirect(url_for('error'))

    new_assign = Assignment(project_id=project_id, consultant_id=consultant_id, date=datetime.now())
    db.session.add(new_assign)
    db.session.commit()
    return redirect(url_for('project_information', project_id=project_id))



@app.route('/delete-task/<int:project_id>-<int:task_id>-<int:page>')
@login_required
# Enabling task deletion to different user types
def delete_task(project_id, task_id, page):
    if session['perm'] == 'project manager':
        return redirect(url_for('error'))

    tasks = [i.task_id for i in Task.query.all()]
    if session['perm'] == 'manager':
        project_ids = [i.project_id for i in Project.query.filter_by(manager_id=current_user.manager_id).all()]

    else:
        project_ids = [i.project_id for i in Project.query.outerjoin(Assignment,Assignment.project_id == Project.project_id).filter_by(consultant_id=current_user.consultant_id).all()]
    pages = [1,2]


    if project_id not in project_ids or task_id not in tasks or page not in pages:
        return redirect(url_for('error'))
    task = Task.query.filter_by(task_id=task_id).first()
    db.session.delete(task)
    db.session.commit()
    if page == 2:
        return redirect(url_for('project_information', project_id=project_id))
    elif page == 1:
        return redirect(url_for('dashboard', project_id=project_id))





@app.route('/delete-assignment/<int:project_id>-<int:consultant_id>')
@login_required
# Enabling assignment deletion to different user types
def delete_assignment(project_id, consultant_id):
    if session['perm'] != 'manager':
        return redirect(url_for('error'))
    consultants = [i.consultant_id for i in Assignment.query.all()]
    project_ids = [i.project_id for i in Assignment.query.all()]

    if project_id not in project_ids or consultant_id not in consultants:
        return redirect(url_for('error'))
    assignment = Assignment.query.filter_by(project_id=project_id, consultant_id=consultant_id).first()
    db.session.delete(assignment)
    db.session.commit()

    return redirect(url_for('project_information', project_id=project_id))


@app.route('/delete-project/<int:project_id>')
@login_required
# Enabling project deletion to different user types
def delete_project(project_id):
    if session['perm'] != 'manager':
        return redirect(url_for('error'))
    project_ids = [i.project_id for i in Project.query.filter_by(manager_id=current_user.manager_id).all()]
    if project_id not in project_ids:
        return redirect(url_for('error'))

    project = Project.query.filter_by(project_id=project_id).first()
    assignments = Assignment.query.filter_by(project_id=project_id).all()
    tasks = Task.query.filter_by(project_id=project_id).all()




    for task in tasks:
        db.session.delete(task)
    for assignment in assignments:
        db.session.delete(assignment)
    db.session.delete(project)
    db.session.commit()

    return redirect(url_for('projects'))


@app.route('/error')
@login_required
def error():
    # Generic error handler to handle various site errors
    # Before routing to this route, ensure flash function is used
    return render_template('error.html')

@app.route('/employees')
@login_required
def employees():
    if session['perm'] != 'manager':
        return redirect(url_for('error'))
    all_employees = Consultant.query.all()
    grouped_employees = []
    for i in range(0,len(all_employees),3):
        group = all_employees[i:i+3]
        grouped_employees.append(group)

    project_assignments = {}

    for consultant in all_employees:
        project_assignments[consultant.consultant_id] = Assignment.query.filter_by(consultant_id=consultant.consultant_id).count()

    return render_template('employees.html',employees=grouped_employees, assignments= project_assignments)

@app.route('/employee-metrics')
@login_required
def employee_metrics():
    if session['perm'] == 'project manager':
        all_projects = Project.query.order_by(Project.end_date).all()
        assignments = [assignment.consultant_id for assignment in Assignment.query.all()]
        all_consultants = Consultant.query.all()
        assigned = [consultant for consultant in all_consultants if consultant.consultant_id in assignments]
        unassigned = [consultant for consultant in all_consultants if consultant.consultant_id not in assignments]
        utilization = len(assigned)/len(all_consultants)*100
        assignment_hours = {i.consultant_id: 0 for i in all_consultants}
        for i in Assignment.query.all():
            assignment_hours[i.consultant_id] = assignment_hours.get(i.consultant_id, 0) + i.hours_worked
        working_employees = Consultant.query.all()
        assignments = Assignment.query.all()





        assignments_for_dict = Assignment.query.all()
        assignment_dict = {i.consultant_id: 0 for i in Consultant.query.all()}

        for assignment in assignments_for_dict:
            assignment_dict[assignment.consultant_id] = assignment_dict.get(assignment.consultant_id, 0) + 1

        dictionary_for_use = {'0 Projects':0,'1 Project':0,'2 Projects':0,'3+ Projects':0}
        for consultant in assignment_dict.values():
            if consultant == 0:
                dictionary_for_use['0 Projects'] +=1

            elif consultant ==1:
                dictionary_for_use['1 Project'] +=1

            elif consultant == 2:
                dictionary_for_use['2 Projects'] +=1

            else:
                dictionary_for_use['3+ Projects'] +=1

        mydf = pd.DataFrame(dictionary_for_use.items(), columns=['Total Assignments Per Consultant', 'count'])

        project_stage_chart = px.pie(data_frame=mydf, names='Total Assignments Per Consultant', values='count', title='Total Assignments Per Consultant')

        project_stage_chart.update_traces(textposition='inside', textinfo='percent', textfont_size=16, sort=False)
        project_stage_chart.update_layout(title={'x': 0.5})

        graphJSON = json.dumps(project_stage_chart, cls=plotly.utils.PlotlyJSONEncoder)





        return render_template('employee-metrics.html', all_projects=all_projects, all_consultants=all_consultants, assignments=assignments, assigned=assigned, unassigned=unassigned, utilization=utilization, assignment_hours=assignment_hours, graphJSON=graphJSON)
    else:
        return redirect(url_for('error'))

@app.errorhandler(404)
def page_not_found(e):
    if session['perm'] == '':
        return render_template('404.html'), 404
    else:
        flash(f'The page you are requesting does not exist. Please contact Para support.')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Execute only once! Initial loading of project stages (will not run in PythonAnywhere)
        '''
        stages = ['Contracting', 'Client Research', 'System Design', 'Implementation', 'Completed']
        for each_stage in stages:
            a_stage = ProjectStage(project_stage=each_stage)
            db.session.add(a_stage)
            db.session.commit()
        '''

        # Execute only once! Initial loading of manager types (will not run in PythonAnywhere)
        '''
        manager_types = ['Manager', 'Project Manager']
        for type in manager_types:
            a_type = ManagerType(manager_type=type)
            db.session.add(a_type)
            db.session.commit()
        '''

    app.run()
