# -*- coding: utf-8 -*-
"""
Web Scraping dos níveis dos rios - Atualização automática via GitHub Actions
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

# Caminho correto do ChromeDriver (ajustado para GitHub Actions)
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

# Configuração do Selenium para rodar sem interface gráfica
options = Options()
options.add_argument("--headless")  # Rodar sem interface gráfica
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Dicionário de meses em português
meses = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# Função para extrair os dados do site
def get_river_levels(driver, year, month_name):
    try:
        # Selecionar o mês
        selecionar_mes = Select(driver.find_element(By.NAME, 'mes'))
        selecionar_mes.select_by_visible_text(month_name)

        # Selecionar o ano
        selecionar_ano = Select(driver.find_element(By.NAME, 'ano'))
        selecionar_ano.select_by_visible_text(str(year))

        # Esperar até o botão de pesquisa estar clicável e clicar
        wait = WebDriverWait(driver, 10)
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.bt-submit[type='submit'][value='Pesquisar']")))
        search_button.click()

        # Esperar os dados carregarem
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > main > div > article > div > table > tbody")))

        # Analisar HTML com BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tbody = soup.select_one('body > main > div > article > div > table > tbody')

        if not tbody:
            print(f"⚠️ Nenhum dado encontrado para {month_name}/{year}. Pulando...")
            return [], []

        # Coletar os cabeçalhos
        header_row = tbody.select_one('tr.th-desktop')
        headers = [th.text.strip() for th in header_row.find_all('th')] if header_row else []
        
        # Coletar as linhas da tabela
        rows = [[td.text.strip() for td in tr.find_all('td')] for tr in tbody.find_all('tr')[1:]]
        
        return headers, rows

    except Exception as e:
        print(f"❌ Erro ao buscar dados de {month_name}/{year}: {e}")
        return [], []

# Função para salvar os dados
def save_data(data, filename):
    if not data:
        print("⚠️ Nenhum dado para salvar.")
        return

    headers, rows = data[0]
    df = pd.DataFrame(rows, columns=headers)

    for headers, rows in data[1:]:
        if rows:
            temp_df = pd.DataFrame(rows, columns=headers)
            df = pd.concat([df, temp_df], ignore_index=True)

    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"📁 Dados salvos com sucesso em {filename}!")

# Função principal
def main():
    end_year = datetime.now().year
    start_year = end_year - 5
    data = []

    # Iniciar o driver
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get('https://proamanaus.com.br/nivel-dos-rios')

    try:
        # Iterar pelos anos e meses
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_name = meses[month]
                headers, rows = get_river_levels(driver, year, month_name)
                if rows:
                    data.append((headers, rows))
                    print(f"✅ Dados de {month_name}/{year} coletados com sucesso!")
    finally:
        driver.quit()

    # Salvar os dados coletados no CSV
    save_path = "nivel_dos_rios.csv"
    save_data(data, save_path)

if __name__ == "__main__":
    main()
