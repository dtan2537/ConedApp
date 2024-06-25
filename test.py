import requests 
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup 
import json
  

with open("creds.json", "r") as file:
    creds = json.load(file)

# Making a GET request 
site = "https://intappsp.coned.com/digitalid/#/home"
site = "https://intappsp.coned.com/LCPortal/GenericForms/GridViewer.aspx?P=3#"
r = requests.get(site, verify=False, auth=HttpNtlmAuth(creds['user'], creds['pass'])) 


print(r.content)
  
# # check status code for response received 
# # success code - 200 
# print(r) 
  
# Parsing the HTML 
soup = BeautifulSoup(r.content, 'html.parser') 
print(soup.prettify()) 

print('hello')