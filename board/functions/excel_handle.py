from openpyxl import load_workbook
import pandas as pd
import win32com.client
import os
import pythoncom


FILENAME1 = "sheet1.xls"
FIXEDFILE1 = FILENAME1[0:-4] + ".xlsx"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "uploads")

def save_fix(old_path, new_path):
    pythoncom.CoInitialize()
    o = win32com.client.Dispatch("Excel.Application")
    o.Visible = False
    wb = o.Workbooks.Open(old_path)
    wb.SaveAs(new_path, 51)
    wb.Close(True)
    o.Application.Quit()

def clear_files(paths: list):
    for path in paths:
        os.remove(path)

def get_pandas(file):
    return pd.read_excel(file)

def course_filter(df, terms = ["OJT", "GEC", "ONL"]):
    return df[df['Course ID'].str.contains('|'.join(terms))]

def sort_people(df, role = "Emp No"):
    return df.sort_values(by=[role])

def completionDiff(df1, df2):
    cols = list(df1.columns)
    stillIncomplete = pd.merge(df1, df2, how='inner', on=cols)
    newlyIncomplete = pd.merge(stillIncomplete, df2, how='outer', on=cols)
    #mention that the form filters have to be the same for first and second weeks (same column headers)
    completed = pd.merge(stillIncomplete, df1, how='outer', on=cols)
    return stillIncomplete, completed, newlyIncomplete

    
    # print(courseFilter(df))
    # print(sortPeople(df))
    # print(list(df.columns))

    





