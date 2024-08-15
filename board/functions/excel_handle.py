from openpyxl import load_workbook
import pandas as pd
import win32com.client
import os
import pythoncom


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
    return pd.read_excel(file, dtype='object')

def class_filter(df, col, terms):
    return df[df[col].str.contains('|'.join(terms), na=False)]

def sort_people(df, role = "Emp No"):
    return df.sort_values(by=[role])

def completionDiff(df1, df2):
    no_status_list = list(df1.columns)
    no_status_list.remove('Course Status')
    df1 = df1[df1['Course Status'] != "Complete"]
    temp_df1 = df1.rename(columns={"Course Status": "CS1"})
    temp_df2 = df2.rename(columns={"Course Status": "CS2"})
    both = pd.merge(temp_df1, temp_df2, how="inner", on=no_status_list)
    df1_only = pd.merge(temp_df1[no_status_list], both[no_status_list], how="outer", on=no_status_list, indicator=True)
    df1_only = df1_only[df1_only["_merge"] == 'left_only']

    df2_only = pd.merge(temp_df2, both[no_status_list], how="outer", on=no_status_list, indicator=True)
    df2_only = df2_only[df2_only["_merge"] == 'left_only']

    df2_only_complete = df2_only[df2_only['CS2'] == 'Complete']
    both_complete = both[both['CS2'] == 'Complete']
    both_complete = both_complete[both_complete['CS1'] != 'Complete']

    newly_complete = pd.concat([both_complete, df1_only[no_status_list], df2_only_complete[no_status_list]])
    newly_complete = newly_complete[no_status_list]
    
    return newly_complete

def statusComp(df1, df2, comp_dict):
    df1_list, df2_list = comp_dict.get("df1_list", []), comp_dict.get("df2_list", []) 
    no_status_list = list(df1.columns).remove('Course Status')
    df1 = class_filter(df1, 'Course Status', df1_list)
    df2 = class_filter(df2, 'Course Status', df2_list)
    df1 = df1.rename(columns={"Course Status": "CS1"})
    df2 = df2.rename(columns={"Course Status": "CS2"})
    both = pd.merge(df1, df2, how="inner", on=no_status_list)
    return both

def nestDict(df):
    _dict = {}
    df.columns = df.iloc[0]
    df = df.drop([0])
    #if mananger isnt there, add manager as well as employee
    # if manager is there, just add employee
    #if manager isnt there and level number is different, search for if employee is there. if they are, add mananager but aobve employee. else add manange rnormally
    for i, r in df[::-1].iterrows():
        manager = r['Manager Name']
        name = r['Name']
        _id = r['Person Number']
        role = r['Job Name']
        default_dict = {'id': '', 'role': '', 'directs': {}}
        if manager not in _dict:
            _dict[manager] = default_dict
        if name not in _dict:
            _dict[manager]['directs'][name] = {'id': _id, 'role': role, 'directs': {}}
        else:
            _dict[name]['id'] = _id
            _dict[name]['role'] = role
            _dict[manager]['directs'][name] = _dict[name]
            _dict.pop(name)
    return _dict
    
def superDict(df):
    df.columns = df.iloc[0]
    df = df.drop([0])
    df = df[["Person Number", "Manager Name"]]
    super_dict = df.set_index('Person Number').T.to_dict('list')
    super_dict = {k.lstrip("0"):v[0] for k, v in super_dict.items()}
    return super_dict

def jsonDict(df):
    return {"nest": nestDict(df),
            "list": superDict(df)}
    





