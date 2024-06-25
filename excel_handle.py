from openpyxl import load_workbook
import pandas as pd
import win32com.client
import os

input_file = "testing_data.xls"
temp_filename = "testing_data.xlsx"


new_path = os.getcwd() + '/' + temp_filename

o = win32com.client.Dispatch("Excel.Application")
o.Visible = False

filename = os.getcwd() + '/' + input_file
output = new_path

wb = o.Workbooks.Open(filename)
wb.SaveAs(new_path, 51)
wb.Close(True)
o.Application.Quit()

def courseFilter(df):
    terms = ["ONL", "GEC", "ONL"]
    return df[df['Course ID'].str.contains('|'.join(terms))]

def sortPeople(df, role = "employee"):
    col = "Employee Name" if role == "employee" else "Supervisor Name"
    return df.sort_values(by=[col])

def completionDiff(df1, df2):
    cols = list(df1.columns)
    stillIncomplete = pd.merge(d1, d2, how='inner', on=cols)
    newlyIncomplete = pd.merge(stillIncomplete, d2, how='outer', on=cols)
    #mention that the form filters have to be the same for first and second weeks (same column headers)
    completed = pd.merge(stillIncomplete, d1, how='outer', on=cols)
    return stillIncomplete, completed, newlyIncomplete

df = pd.read_excel(new_path)
# print(courseFilter(df))
# print(sortPeople(df))
print(list(df.columns))

os.remove(new_path)





