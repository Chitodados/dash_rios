# -*- coding: utf-8 -*-
"""
Created on Sat Mar  1 17:54:16 2025

@author: lucas
"""

import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
import time
from selenium import webdriver

# Instalar o chromedriver automaticamente
chromedriver_autoinstaller.install()

# Configurar o Selenium com o Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Opcional: rodar sem abrir uma janela do navegador

# Dicionário de meses em português
meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 
         6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

# Função para extrair os dados do site
def get_river_levels(driver, year, month_name):
    selecionar_mes = Select(driver.find_element(By.NAME, 'mes'))
    selecionar_mes.select_by_visible_text(month_name)

    selecionar_ano = Select(driver.find_element(By.NAME, 'ano'))
    selecionar_ano.select_by_visible_text(str(year))

    wait = WebDriverWait(driver, 10)
    search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.bt-submit[type='submit'][value='Pesquisar']")))
    search_button.click()

    time.sleep(5)

    soup = BeautifulSoup(.page_source, 'html.parser')
    tbody = soup.select_one('body > main > div > article > div > table > tbody')

    if not tbody:
        raise Exception("Failed to find the tbody on the page")

    header_row = tbody.select_one('tr.th-desktop')
    headers = [th.text.strip() for th in header_row.find_all('th')] if header_row else []
    
    rows = [[td.text.strip() for td in tr.find_all('td')] for tr in tbody.find_all('tr')[1:]]

    return headers, rows

# Função para salvar os dados
def save_data(data, filename):
    if not data:
        raise Exception("No data to save")

    headers, rows = data[0]
    df = pd.DataFrame(rows, columns=headers)

    for headers, rows in data[1:]:
        if rows:
            temp_df = pd.DataFrame(rows, columns=headers)
            df = pd.concat([df, temp_df], ignore_index=True)

    df.to_csv(filename, index=False, encoding='utf-8')

# Função principal
def main():
    end_year = datetime.now().year
    start_year = end_year - 5
    data = []

    # Configuração do Selenium para rodar no GitHub Actions (Chrome Headless)
    options = Options()
    options.add_argument("--headless")  # Rodar sem interface gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chrome")  # Caminho do chrome no Linux
    driver = webdriver.Chrome(options=options)

    driver.get('https://proamanaus.com.br/nivel-dos-rios')

    try:
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_name = meses[month]
                try:
                    headers, rows = get_river_levels(driver, year, month_name)
                    data.append((headers, rows))
                    print(f"✅ Dados de {month_name}/{year} coletados com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao buscar dados de {month_name}/{year}: {e}")
    finally:
        driver.quit()

    # Salvar o CSV na pasta do repositório
    save_path = "nivel_dos_rios.csv"
    save_data(data, save_path)

if __name__ == "__main__":
    main()
