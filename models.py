from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class Consultant(UserMixin,db.Model):
    __tablename__ = "consultant"
# Consultant table to track individual information fields
    consultant_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    area_code = db.Column(db.String(3), nullable=True)
    phone = db.Column(db.String(7), nullable=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    consultant_assignments = db.relationship('Assignment', cascade="all, delete", backref='consultant_assignments')

    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = generate_password_hash(password)
    def get_id(self):
        return(self.consultant_id)

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"


class Manager(UserMixin,db.Model):
    __tablename__ = "manager"
    # Manager table to track individual information fields
    manager_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    area_code = db.Column(db.String(3), nullable=True)
    phone = db.Column(db.String(7), nullable=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    manager_type_id = db.Column(db.Integer, db.ForeignKey('manager_type.manager_type_id'), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    manager_projects = db.relationship('Project', cascade="all, delete", backref='manager_projects')

    def __init__(self, first_name, last_name, email, password, manager_type_id):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = generate_password_hash(password)
        self.manager_type_id = manager_type_id
    def get_id(self):
        return(self.manager_id)
    def __repr__(self):
        return f"{self.first_name} {self.last_name}"


class ManagerType(db.Model):
    __tablename__ = "manager_type"
#Creating managerID for each individual manager
    manager_type_id = db.Column(db.Integer, primary_key=True)
    manager_type = db.Column(db.String(30), nullable=False)
    managers = db.relationship('Manager', cascade="all, delete", backref='managers')

    def __init__(self, manager_type):
        self.manager_type = manager_type

    def __repr__(self):
        return f"{self.manager_type}"


class Client(db.Model):
    __tablename__ = "client"
    # Client table to track individual information fields
    client_id = db.Column(db.Integer, primary_key=True)
    poc_first_name = db.Column(db.String(30), nullable=False)
    poc_last_name = db.Column(db.String(100), nullable=False)
    poc_area_code = db.Column(db.String(3), nullable=True)
    poc_phone = db.Column(db.String(7), nullable=True)
    email = db.Column(db.String(50), nullable=False)
    first_contact_date = db.Column(db.Date, nullable=True)
    client_projects = db.relationship('Project', cascade="all, delete", backref='client_projects')

    def __init__(self, poc_first_name, poc_last_name, email, poc_area_code, poc_phone, first_contact_date):
        self.poc_first_name = poc_first_name
        self.poc_last_name = poc_last_name
        self.email = email
        self.poc_area_code = poc_area_code
        self.poc_phone = poc_phone
        self.first_contact_date = first_contact_date


    def __repr__(self):
        return f"{self.poc_first_name} {self.poc_last_name}"


class Project(db.Model):
    __tablename__ = "project"
    # Project table to track individual information fields
    project_id = db.Column(db.Integer, primary_key=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.manager_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    tasks = db.relationship('Task', cascade="all, delete", backref='tasks')
    project_assignments = db.relationship('Assignment', cascade="all, delete", backref='project_assignments')
    stage_id = db.Column(db.Integer, db.ForeignKey('project_stage.stage_id'), nullable=False)

    def __init__(self, manager_id, client_id, start_date, description, end_date, budget):
        self.manager_id = manager_id
        self.client_id = client_id
        self.start_date = start_date
        self.description = description
        self.end_date = end_date
        self.budget = budget
        self.stage_id = 1


    def __repr__(self):
        return f"{self.description}"


class Task(db.Model):
    __tablename__ = "task"
    # Task table to track individual information fields
    task_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=False)
    task_content = db.Column(db.String(150), nullable=False)
    task_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, project_id, task_content, task_date):
        self.project_id = project_id
        self.task_content = task_content
        self.task_date = task_date

    def __repr__(self):
        return f"{self.task_content}"


class ProjectStage(db.Model):
    __tablename__ = "project_stage"
    # Project stage table to track progression
    stage_id = db.Column(db.Integer, primary_key=True)
    project_stage = db.Column(db.String(50), nullable=False)
    ps_projects = db.relationship('Project', cascade="all, delete", backref='ps_projects')

    def __init__(self, project_stage):
        self.project_stage = project_stage

    def __repr__(self):
        return f"{self.project_stage}"


class Assignment(db.Model):
    __tablename__ = "assignment"
    # Assignment table to track information fields
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), primary_key=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('consultant.consultant_id'), primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    allowed_hours = db.Column(db.Integer, nullable=True)
    hours_worked = db.Column(db.Integer, nullable=False)

    def __init__(self, project_id, consultant_id, date):
        self.project_id = project_id
        self.consultant_id = consultant_id
        self.date = date
        self.hours_worked = 0

    def __repr__(self):
        return f"{self.allowed_hours}"