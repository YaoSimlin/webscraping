import requests
import pandas as pd
from datetime import datetime
import time

from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import dateparser
import json

# 1. Connexion au navigateur Web et à l'URL
def connect_to_url(driver_path, url):
    
    # Création d'une instance driver
    driver = webdriver.Firefox(executable_path=driver_path)
    #connexion à l'url
    driver.get(url)
    
    return driver

# 2. Phase d'Authentification pour accéder à l'application 
def authentication(driver, login = "OCITNETAD\\admqv", password = "@Ql1kV13w@"):
    
    # Saisie du Login
    enter_login = driver.find_element_by_id("username") 
    enter_login.clear()
    enter_login.send_keys(login)
    time.sleep(3)
    
    # Saisie du Password
    enter_password = driver.find_element_by_id("password") 
    enter_password.clear()
    enter_password.send_keys(password)
    time.sleep(3)
    
    # Valudation de l'authentification
    driver.find_element_by_class_name("loginSubmitButton").submit()
    time.sleep(5)
    
    return driver

# 3. Phase de recherche des dashborads et de reccupération des dates à jour
def get_service_app(driver, service_name = "Reporting DRDI.qvw", id_ = "14"):
    
    # Phase de recherche du dashboard
    driver.refresh()
    time.sleep(5)
    input_search = driver.find_element_by_class_name("input_search")

    input_search.clear()
    input_search.send_keys(service_name + Keys.RETURN)
    time.sleep(10)
    
    # Accès à la page de l'application
    driver.find_element_by_class_name("name").click()
    time.sleep(60)
    
    # Phase de réccupération des dates de mise à jour
    try :
        WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.ID, id_))
    )
        text = driver.find_element_by_id(id_).find_element_by_class_name("TextObject").text
    except :
        driver.refresh()
        WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.ID, id_))
    ).find_element_by_id(id_).find_element_by_class_name("TextObject").text
    
    # Retour à la page de recherche des applications
    driver.back()
    
    return text

# 4. Traitements des infos collectées
## Gestion des données collectées
def get_update_dates(driver, devices_infos):
    
    update_dates = dict()
    for id_, device in devices_infos.items():
        
        text = get_service_app(driver, service_name = device, id_ = id_)
        
        update_dates[device.replace(".qvw", "")] = text
    
    driver.quit()
    return update_dates

# Extraction des infos de date un text
def extract_date_from_text(text):
    
    thedate = text.split(':')
    thedate = thedate[-1]
    return thedate

##   Traitement des dates
import dateparser
def transform_string_date(str_val):
    try :
        str_val = str_val.lower()
    except :
        pass
    date_ = dateparser.parse(str_val)
    
    return date_.strftime("%Y-%m-%d")

# Sauvegarde des infos sur les mises à jour
def get_data(devices_infos, dirPath = './data'):
    
    df_dates = pd.DataFrame({"applications" : devices_infos.keys(), 
                         "dates_MAJ" : devices_infos.values()}, 
                         columns=["applications", "dates_MAJ"] 
                        )
    
    df_dates.dates_MAJ = df_dates.dates_MAJ.apply(lambda x  : extract_date_from_text(x))
    df_dates.dates_MAJ = df_dates.dates_MAJ.apply(lambda x  : transform_string_date(x))
    
    today = datetime.now().strftime("%Y%m%d_%H")
    df_dates.to_csv(dirPath+'/checking_dashboards_'+today+'.csv', index=False, sep = ';')
    
    return ''

# Chargement des données des dashboards à rechercher
def load_dashboard_infos(path = './configs/liste_dashboards.json') :
    # Opening JSON file
    with open(path) as f:
        data = json.load(f)
        
    return data


if __name__ == "__main__" :
    
    # Affectations de valeur au variables
    dash_path = './Web_Scraping_Dynamique/liste_dashboards.json' #'./configs/liste_dashboards.json'
    dirPath = './Web_Scraping_Dynamique'
    driver_path = "./web_drivers/geckodriver.exe"
    url  = "http://10.242.69.35/qlikview/FormLogin.htm"
    
    devices_infos = load_dashboard_infos(path = dash_path)
    driver = connect_to_url(driver_path = driver_path, url = url)
    driver = authentication(driver = driver, login = "OCITNETAD\\admqv", 
                            password = "@Ql1kV13w@")
    update_dates = get_update_dates(driver = driver, devices_infos = devices_infos)
    get_data(devices_infos = update_dates, dirPath = dirPath)