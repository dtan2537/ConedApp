from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

edgeService = Service(os.getcwd() + '/' + 'msedgedriver.exe')
edgeDriver = webdriver.Edge(service=edgeService)
edgeDriver.maximize_window()

edgeDriver.get("https://intappsp.coned.com/digitalid/#/home")

# element = WebDriverWait(edgeDriver, 20).until(EC.element_to_be_clickable((By.XPATH, '//kendo-autocomplete[@title="Search by employee name or number"]')))
element = edgeDriver.find_element(By.XPATH, '//input[1]')
element.send_keys("38334")
element.send_keys(Keys.RETURN)
button = edgeDriver.find_element(By.ID, "btnSubmitNav")
button.click()
element.clear()
element.send_keys("01232")
button.click()
input('')
# edgeDriver.implicitly_wait(20)
# element.send_keys("01232")
# search = edgeDriver.find_element(By.XPATH, '//*[@title="Search by employee name or number"]')


# print(search)
# search.click()
# search.send_keys("01232")
# search.send_keys(Keys.RETURN)

# print(edgeDriver.title)
