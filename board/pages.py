from flask import Blueprint, render_template, request, flash, redirect, url_for
import os
import glob
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField 
from wtforms import DecimalField, RadioField, SelectField, TextAreaField, FileField 
from wtforms.validators import InputRequired 
from board.functions.excel_handle import FILENAME1, FIXEDFILE1, save_fix, get_pandas, course_filter, sort_people

bp = Blueprint("pages", __name__)
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads")
old_path = os.path.join(UPLOAD_FOLDER, FILENAME1)
new_path = os.path.join(UPLOAD_FOLDER, FIXEDFILE1)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_grid(path):
    if os.path.exists(path):
        pd = get_pandas(path)
        excel_list = ["Emp No", "Employee Name", "Course ID", "Course Title", "Course Status", "Due Date"]
        pd = pd[excel_list]
        pd = grid_filter(pd)
        pd = grid_sort(pd)
        pd_dict = pd.to_dict('records')
        return pd_dict
    else:
        return []
    
def grid_filter(pd):
    terms = ["OJT", "GEC", "ONL"]
    for i in terms[::-1]:
        if not request.form.get(i):
            terms.remove(i)
    pd = course_filter(pd, terms)
    return pd

def grid_sort(pd):
    # Todo: fix supervisor and due date (string sort != date sort)
    sort_dict = {"Employee": "Employee Name",
                 "Supervisor": "Employee Name",
                 "Course": "Course Title",
                 "Due": "Due Date"}
    sort = request.form.get("sort")
    return sort_people(pd, role=sort_dict[sort]) if sort else pd

def clear_files(path):
    files = glob.glob(os.path.join(path, '*'))
    print(files)
    for f in files:
        os.remove(f)


class MyForm(FlaskForm): 
    name = StringField('Name', validators=[InputRequired()]) 
    password = PasswordField('Password', validators=[InputRequired()]) 
    remember_me = BooleanField('Remember me') 
    salary = DecimalField('Salary', validators=[InputRequired()]) 
    gender = RadioField('Gender', choices=[ 
                        ('male', 'Male'), ('female', 'Female')]) 
    country = SelectField('Country', choices=[('IN', 'India'), ('US', 'United States'), 
                                              ('UK', 'United Kingdom')]) 
    message = TextAreaField('Message', validators=[InputRequired()]) 
    photo = FileField('Photo') 


@bp.route("/", methods=['GET', 'POST'])
@bp.route("/manual", methods=['GET', 'POST'])
def manual():
    filename = "bruh"
    if request.method == 'POST':
        if 'file' in request.files:
            # flash('No file part')
            file = request.files['file']
            if file.filename:
                # flash('No selected file')
                if file and allowed_file(file.filename):
                    clear_files(UPLOAD_FOLDER)
                    filename = secure_filename(file.filename)
                    file.save(old_path)
                    save_fix(old_path, new_path)
    grid = get_grid(new_path)        
    return render_template("pages/manual.html", data = filename, grid = grid)

@bp.route("/automatic")
def automatic():
    form = MyForm()
    return render_template("pages/automatic.html", form = form)

@bp.route("/help")
def _help():
    return render_template("pages/help.html")

