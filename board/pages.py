from flask import render_template, request, flash, redirect, url_for, session
from flask_session import Session
from board import app
import os
import glob
import json
from board.functions.html_copy import PutHtml
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from flask_wtf import FlaskForm 
from wtforms import widgets, SelectField, FileField, SubmitField, SelectMultipleField
from board.functions.excel_handle import save_fix, get_pandas, class_filter, sort_people, nestDict, jsonDict, statusComp
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, relative_path)


with app.app_context():
    Session(app)


config_path = resource_path('config.json')
supervisor_path = resource_path('supervisors.json')
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
UPLOAD_FOLDER =  resource_path("uploads")

@app.context_processor
def resource_link():
    return {"style": resource_path(os.path.join("static", "css", "style.css")),
            "icon": resource_path(os.path.join("static", "icons", "CE_favicon.ico")) }

with open(config_path, 'r') as f:
    global config
    config = json.load(f)

faulty_name = lambda x: x + ".xls"
fixed_name = lambda x: x + ".xlsx"
get_path = lambda x: os.path.join(UPLOAD_FOLDER, x)
get_path_dict = lambda x: {"faulty_name": faulty_name(x), "faulty_path": get_path(faulty_name(x)), "fixed_name": fixed_name(x), "fixed_path": get_path(fixed_name(x))}
not_faulty = lambda filename: '.' in filename and filename.rsplit('.', 1)[1].lower() == 'xlsx'

files_dict = {
    "prev": get_path_dict("prev"),
    "comp1": get_path_dict("comp1"),
    "comp2": get_path_dict("comp2"),
    "sup": get_path_dict("sup")
}


with open(supervisor_path, 'r') as f:
    _dict = json.load(f)
    employee_dict = _dict.get("list", {})


excel_list = config["grid_columns"]
color_dict = config["color_dict"]
courses_list = config["course_prefix"]
status_list = config["statuses"]
group_list = config["email_arrangement"]
comp_status_list = config["comp_status"]
defaults = config["Defaults"]

supervisor_list = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def file_save(file, dictname):
    if not_faulty(file.filename):
        file.save(files_dict[dictname]["fixed_path"])
    else:
        file.save(files_dict[dictname]["faulty_path"])
        save_fix(files_dict[dictname]["faulty_path"], files_dict[dictname]["fixed_path"])



def update_df(form):
    if 'original_df' in session:
        #colors in df?
        df = session['original_df'][excel_list]
        df = grid_filter(df, form)
        df = grid_sort(df)
        session['current_df'] = df

def update_compare(form):
    if 'comp1_df' not in session:
        return
    df1, df2 = session['comp1_df'][excel_list], session['comp2_df'][excel_list]
    comp_dict = comp_status_list.get(form.comp_status.data, {})
    df = statusComp(df1, df2, comp_dict)
    df = comp_grid_filter(df, form)
    df = grid_sort(df)
    session['comp_filter_df'] = df

def update_super(path):
    with open(supervisor_path, 'w') as f:
        temp = jsonDict(get_pandas(path))
        if temp:
            json.dump(temp, f, indent=2) 

def get_grid(df_name):
    if df_name not in session:
        return []
    df = session[df_name]    
    df_dict = df.to_dict('records')
    return df_dict
    
def comp_grid_filter(pd, form):
    terms = form.filterby.data
    pd = class_filter(pd, 'Course ID', terms)
    terms = form.filter_super.data
    pd = class_filter(pd, 'Supervisor', terms)
    return pd

def grid_filter(pd, form):
    terms = form.filterby.data
    pd = class_filter(pd, 'Course ID', terms)
    terms = form.filter_status.data
    pd = class_filter(pd, 'Course Status', terms)
    terms = form.filter_super.data
    pd = class_filter(pd, 'Supervisor', terms)
    return pd

def grid_sort(pd):
    # Todo: fix supervisor and due date (string sort != date sort)
    sort = request.form.get("sort")
    return sort_people(pd, role=sort) if sort else pd

def add_supervisor(df):
    df['Supervisor'] = df.apply(lambda row: employee_dict.get(row['Emp No'].lstrip("0"), "Unknown"), axis = 1)
    return df

def clear_files(path):
    files = glob.glob(os.path.join(path, '*'))
    for f in files:
        os.remove(f)

def generate_email_html(_dict):
    html = ""
    for key in _dict:
        html += f"<br><span>{key} - </span>"
        comma = ','
        for count, item in enumerate(_dict[key]):
            color = ""
            if count == len(_dict[key]) - 1:
                comma = ""
            if item[1] == 'Overdue':
                color = "color: red;"
            html += f"<span style = '{color}'>{item[0]}{comma} </span>"
    return html

def email_df(group):
    parent = group_list[group]['parent']
    child = group_list[group]['child']
    highlight = group_list[group]['highlight_overdue']
    if highlight:
        func = lambda row: [row[child], row['Course Status']]
    else:
        func = lambda row: [row[child], ""]
    if 'current_df' in session:
        df = session['current_df']
        df['Employee Name'] = df['Employee Name'].apply(lambda name: ' '.join(name.split(', ')[::-1]))
        df = df.assign(pairs = df.apply(func, axis=1))
        res = df.groupby(parent)['pairs'].apply(list).to_dict()
        return res
    else:
        return []
    
def preview_func(form):
    if form.validate_on_submit() and form.submit.data:
        file = form.file.data
        if file and allowed_file(file.filename):
            session['original_filename'] = secure_filename(file.filename)
            clear_files(UPLOAD_FOLDER)
            file_save(file, "prev")
            session['original_df'] = add_supervisor(get_pandas(files_dict["prev"]["fixed_path"]))
        elif file and not allowed_file(file.filename):
            flash('Submit a file with extension xls, xlsx, or csv.')
        update_df(form)
    # print(form.errors)

def compare_func(form):
    if form.validate_on_submit() and form.compare.data:
        file1 = form.file1.data
        file2 = form.file2.data
        if file1 and file2 and allowed_file(file1.filename) and allowed_file(file2.filename):
            session['comp1_filename'] = secure_filename(file1.filename)
            session['comp2_filename'] = secure_filename(file2.filename)
            clear_files(UPLOAD_FOLDER)
            file_save(file1, "comp1")
            file_save(file2, "comp2")
            session['comp1_df'] = add_supervisor(get_pandas(files_dict["comp1"]["fixed_path"]))
            session['comp2_df'] = add_supervisor(get_pandas(files_dict["comp2"]["fixed_path"]))
        elif file1 or file2:
            flash('Choose 2 files with extensions .csv, .xls, or .xlsx') 
        update_compare(form)

def copy_func(form, df):
    if form.validate_on_submit() and form.copy.data:
        PutHtml(generate_email_html(df))

def super_func(form):
    if form.validate_on_submit() and form.submit.data:
        file = form.file.data
        if file and allowed_file(file.filename):
            session['sup_filename'] = secure_filename(file.filename)
            clear_files(UPLOAD_FOLDER)
            file_save(file, "sup")
            update_super(files_dict["sup"]["fixed_path"])
        elif file:
            flash('Submit a file with extension xls, xlsx, or csv.')
          
def get_nested_dict():
    #error handling for empty json file or empty session["nest"]?
    if "nest" not in session:
        with open(supervisor_path, 'r') as f:
            _dict = json.load(f)
            session["nest"] = _dict.get("nest", {})
    return session["nest"]

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MultiCheckSelectField(SelectMultipleField):
    widget = widgets.Select()
    option_widget = widgets.CheckboxInput()

class ManualForm(FlaskForm):
    file = FileField('Upload Training Data')
    filterby = MultiCheckboxField('Filter Course', choices = list(zip(courses_list, courses_list)))
    filter_status = MultiCheckboxField('Filter Status', choices = list(zip(status_list, status_list)))
    filter_super = MultiCheckboxField('Filter Supervisor', choices = list(zip(set(employee_dict.values()), set(employee_dict.values()))))
    sort = SelectField('Sort By', choices=list(zip(excel_list, excel_list)))
    sort = MultiCheckSelectField('Sort By', choices=list(zip(excel_list, excel_list)))
    submit = SubmitField('Preview')

class AutomaticForm(ManualForm):
    group = SelectField('Group By', choices= list(zip(group_list.keys(), group_list.keys())))
    copy = SubmitField('Copy HTML')

class CompareForm(ManualForm):
    file1 = FileField('File 1')
    file2 = FileField('File 2')
    compare = SubmitField('Compare')
    submit = None
    file = None
    filter_status = None
    comp_status = SelectField('Status Changed By', choices=list(zip(comp_status_list.keys(), comp_status_list.keys())))

class SupervisorsForm(FlaskForm):
    file = FileField('Upload Directory Sheet')
    submit = SubmitField('View')

@app.route("/", methods=['GET', 'POST'])
@app.route("/manual", methods=['GET', 'POST'])
def manual():
    form = ManualForm(**defaults)
    submitted = preview_func(form)
    grid = get_grid('current_df')       
    filename = session.get("original_filename", "No file")
    # if submitted:
    #     return redirect(url_for("manual", data = filename, grid = grid, form = form, name = filename, color = color_dict))
    return render_template("pages/manual.html", data = filename, grid = grid, form = form, name = filename, color = color_dict)

@app.route("/automatic", methods=['GET','POST'])
def automatic():
    form = AutomaticForm(**defaults)
    submitted = preview_func(form)
    df = email_df(group = form.group.data)
    copy_func(form, df)
    filename = session.get("original_filename", "No file")
    # if submitted:
    #     return redirect(url_for("automatic", form=form, text=df, name = filename))
    return render_template("pages/automatic.html", form=form, text=df, name = filename)

@app.route("/compare", methods=['GET', 'POST'])
def compare():
    form = CompareForm(**defaults)
    submitted = compare_func(form)
    grid = get_grid('comp_filter_df')
    name1, name2 = session.get("comp1_filename", "No file"), session.get("comp2_filename", "No file") 
    # if submitted:
    #     return redirect(url_for("compare", form=form, grid = grid, color = color_dict, name1 = name1, name2 = name2))
    return render_template("pages/compare.html", form=form, grid = grid, color = color_dict, name1 = name1, name2 = name2)

@app.route("/supervisors", methods=['GET', 'POST'])
def supervisors():
    form = SupervisorsForm()
    submitted = super_func(form)
    _dict = get_nested_dict()
    name = session.get("sup_filename", "No file")
    # if submitted:
    #     return redirect(url_for("supervisors", supervisors = _dict, form = form, name = name))
    return render_template("pages/supervisors.html", supervisors = _dict, form = form, name = name)

@app.route("/help")
def _help():
    return render_template("pages/help.html")


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    return render_template("pages/error.html", e=e)

