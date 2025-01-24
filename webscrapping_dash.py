from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from datetime import datetime

# Mapeamento de números para nomes dos meses em português
months = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 
    6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 
    10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def get_river_levels(driver, year, month_name):
    # Seleciona o mês
    month_select = Select(driver.find_element(By.NAME, 'mes'))
    month_select.select_by_visible_text(month_name)
    
    # Seleciona o ano
    year_select = Select(driver.find_element(By.NAME, 'ano'))
    year_select.select_by_visible_text(str(year))
    
    # Espera até o botão de pesquisa estar clicável e clica
    wait = WebDriverWait(driver, 10)
    search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.bt-submit[type='submit'][value='Pesquisar']")))
    search_button.click()
    
    # Espera a página carregar os resultados
    time.sleep(5)
    
    # Faz o parsing da tabela
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Encontra o <tbody> usando o seletor fornecido
    tbody = soup.select_one('body > main > div > article > div > table > tbody')
    if not tbody:
        raise Exception("Failed to find the tbody on the page")
    
    # Encontre o cabeçalho da tabela
    header_row = tbody.select_one('tr.th-desktop')
    if not header_row:
        raise Exception("Failed to find the header row on the tbody")

    headers = [th.text.strip() for th in header_row.find_all('th')]
    
    # Se não encontrar <th>, o cabeçalho pode estar na primeira linha como <td>
    if not headers:
        headers = [td.text.strip() for td in header_row.find_all('td')]

    # Encontre as linhas de dados da tabela
    rows = []
    for tr in tbody.find_all('tr')[1:]:
        cells = [td.text.strip() for td in tr.find_all('td')]
        if cells:
            rows.append(cells)

    return headers, rows

def save_data(data, filename):
    if not data:
        raise Exception("No data to save")

    headers, rows = data[0]
    df = pd.DataFrame(rows, columns=headers)
    
    for headers, rows in data[1:]:
        if not rows:
            continue
        temp_df = pd.DataFrame(rows, columns=headers)
        df = pd.concat([df, temp_df], ignore_index=True)

    # Salva em um arquivo Excel (.xlsx)
    df.to_excel(filename, index=False, engine='openpyxl',)

def main():
    end_year = datetime.now().year
    start_year = end_year - 5
    data = []

    # Inicializa o WebDriver (certifique-se de que o caminho para o chromedriver está correto, se não tiver, baixe ele)
    driver_path = 'C:\Python_projetos\chromedriver-win64\chromedriver.exe'  # Atualize para o caminho correto
    options = Options()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://proamanaus.com.br/nivel-dos-rios')
    
    try:
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_name = months[month]
                try:
                    headers, rows = get_river_levels(driver, year, month_name)
                    data.append((headers, rows))
                    print(f"Successfully fetched data for {month_name}/{year}")
                except Exception as e:
                    print(f"Failed to fetch data for {month_name}/{year}: {e}")
    finally:
        driver.quit()

    # Especificar o caminho para salvar o arquivo
    save_path = r'C:\Python_projetos\Webscrapping_Dash_Rios\dados_rios\nivel_dos_rios_ultimos_5_anos.xlsx'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    save_data(data, save_path)

if __name__ == "__main__":
    main()