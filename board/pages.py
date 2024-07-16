from flask import Blueprint, render_template, request, flash, redirect, url_for
import os
import glob
import json
from board.functions.html_copy import PutHtml
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm 
from wtforms import widgets, SelectField, MultipleFileField, FileField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired 
from board.functions.excel_handle import save_fix, get_pandas, course_filter, sort_people, read_parquet, save_parquet

bp = Blueprint("pages", __name__)

config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploads")

with open(config_path, 'r') as f:
    global config
    config = json.load(f)

faulty_name = lambda x: x + ".xls"
fixed_name = lambda x: x + ".xlsx"
get_path = lambda x: os.path.join(UPLOAD_FOLDER, x)
get_path_dict = lambda x: {"faulty_name": faulty_name(x), "faulty_path": get_path(faulty_name(x)), "fixed_name": fixed_name(x), "fixed_path": get_path(fixed_name(x))}
not_faulty = lambda filename: '.' in filename and filename.rsplit('.', 1)[1].lower() == 'xlsx'
og_filename = ""

files_dict = {
    "prev": get_path_dict("prev"),
    "comp1": get_path_dict("comp1"),
    "comp2": get_path_dict("comp2"),
    "parquet": {"name": "df.parquet", "path": get_path("df.parquet")},
    "comparq1": {"name": "comp1.parquet", "path": get_path("comp1.parquet")},
    "comparq2": {"name": "comp2.parquet", "path": get_path("comp2.parquet")}
}

excel_list = config["grid_columns"]
color_dict = config["color_dict"]
courses_list = config["course_prefix"]
group_list = config["email_arrangement"]
defaults = config["Defaults"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_parquet(excel_path, form):
    if os.path.exists(excel_path):
        df = get_pandas(excel_path)
        df = df[excel_list]
        df = grid_filter(df, form)
        df = grid_sort(df)
        save_parquet(df, files_dict["parquet"]["path"])
        return df


def get_grid(path):
    if not os.path.exists(path) or not os.path.exists(files_dict["parquet"]["path"]):
        return []
    df = read_parquet(files_dict["parquet"]["path"])    
    df_dict = df.to_dict('records')
    return df_dict
    
def grid_filter(pd, form):
    terms = form.filterby.data
    pd = course_filter(pd, terms)
    return pd

def grid_sort(pd):
    # Todo: fix supervisor and due date (string sort != date sort)
    sort = request.form.get("sort")
    return sort_people(pd, role=sort) if sort else pd


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

def email_df(path, group):
    # if not group:
    #     group = defaults['email_arrangement']
    parent = group_list[group]['parent']
    child = group_list[group]['child']
    highlight = group_list[group]['highlight_overdue']
    if highlight:
        func = lambda row: [row[child], row['Course Status']]
    else:
        func = lambda row: [row[child], ""]
    if os.path.exists(path):
        df = read_parquet(path)
        df['Employee Name'] = df['Employee Name'].apply(lambda name: ' '.join(name.split(', ')[::-1]))
        df = df.assign(pairs = df.apply(func, axis=1))
        res = df.groupby(parent)['pairs'].apply(list).to_dict()
        return res
    else:
        return []
    
def preview_func(form):
    if form.validate_on_submit() and form.submit.data:
        flash('bruh')
        print(dict(request.form))
        file = form.file.data
        print(file)
        # print("file", file.filename)
        if file and allowed_file(file.filename):
            global og_filename
            og_filename = secure_filename(file.filename)
            clear_files(UPLOAD_FOLDER)
            print(file.filename)
            if not_faulty(file.filename):
                file.save(files_dict["prev"]["fixed_path"])
            else:
                file.save(files_dict["prev"]["faulty_path"])
                save_fix(files_dict["prev"]["faulty_path"], files_dict["prev"]["fixed_path"])
        elif file and not allowed_file(file.filename):
            flash('Submit a file with extension xls, xlsx, or csv.')
        update_parquet(files_dict["prev"]["fixed_path"], form)
    print(form.errors)

def compare_func(form):
    if form.validate_on_submit() and form.compare.data:
        file1 = form.file1.data
        file2 = form.file2.data
        if file1 and file2 and allowed_file(file1.filename) and allowed_file(file2.filename):
            if not_faulty(file1.filename) and not_faulty(file2.filename):
                file1.save(files_dict["comp1"]["fixed_path"])
                file2.save(files_dict["comp2"]["fixed_path"])
            else:
                file1.save(files_dict["comp1"]["faulty_path"])
                file2.save(files_dict["comp2"]["faulty_path"])
                save_fix(files_dict["comp1"]["faulty_path"], files_dict["comp1"]["fixed_path"])
                save_fix(files_dict["comp2"]["faulty_path"], files_dict["comp2"]["fixed_path"])
            save_parquet(get_pandas(files_dict["comp1"]["fixed_path"]), files_dict["comparq1"]["path"])    
            save_parquet(get_pandas(files_dict["comp2"]["fixed_path"]), files_dict["comparq2"]["path"])
        else:
            flash('Choose 2 files with extensions .csv, .xls, or .xlsx') 
        #update parquet
        #clear files


def copy_func(form, df):
    if form.validate_on_submit() and form.copy.data:
        PutHtml(generate_email_html(df))


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ManualForm(FlaskForm):
    file = FileField('Upload Training Data')
    filterby = MultiCheckboxField('Filter By', choices = list(zip(courses_list, courses_list)))
    sort = SelectField('Sort By', choices=list(zip(excel_list, excel_list)))
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

@bp.route("/", methods=['GET', 'POST'])
@bp.route("/manual", methods=['GET', 'POST'])
def manual():
    form = ManualForm(**defaults)
    form = ManualForm(request.form)
    filename = "bruh"
    preview_func(form)
    grid = get_grid(files_dict["prev"]["fixed_path"])        
    return render_template("pages/manual.html", data = filename, grid = grid, form = form, name = og_filename, color = color_dict)

@bp.route("/automatic", methods=['GET','POST'])
def automatic():
    form = AutomaticForm(**defaults)
    preview_func(form)
    df = email_df(files_dict["parquet"]["path"], group = form.group.data)
    copy_func(form, df)
    return render_template("pages/automatic.html", form=form, text=df, name = og_filename)

@bp.route("/compare", methods=['GET', 'POST'])
def compare():
    form = CompareForm(**defaults)
    compare_func(form)
    return render_template("pages/compare.html", form=form)

@bp.route("/help")
def _help():
    return render_template("pages/help.html")

