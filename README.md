
# Web Scraping para Atualização Automática de CSV

## Visão Geral

O objetivo do projeto é realizar a coleta diária de dados através de web scraping, atualizar um arquivo CSV e armazená-lo no repositório do GitHub. Além disso, o fluxo de trabalho é automatizado para garantir que o arquivo CSV esteja sempre atualizado para o dashboard Streamlit.

### Funcionalidades principais:
- Web scraping automático com o **Selenium**.
- Atualização do arquivo CSV no repositório do GitHub.
- Execução programada do script com **GitHub Actions**.
- Possibilidade de rodar o script manualmente.
- Utilização do **chromium-chromedriver** para rodar o Selenium no GitHub Actions.

## Estrutura do Repositório

- **webscrapping_dash_githubactions.py**: Script Python que realiza o web scraping e atualiza o arquivo CSV.
- **nivel_dos_rios.csv**: Arquivo CSV atualizado com os dados coletados pelo script.
- **requirements.txt**: Arquivo de dependências Python.
- **.github/workflows/update_csv.yml**: Workflow do GitHub Actions para rodar o processo de scraping e atualizar o CSV.

## Como Funciona

### 1. **GitHub Actions**

A execução do workflow foi configurada para ser realizada automaticamente todos os dias às 03:00 UTC. O workflow realiza as seguintes etapas:

- **Clonar o repositório**: Baixa o código mais recente do repositório.
- **Instalar dependências**: Instala as dependências necessárias, como `selenium`, `chromium-chromedriver`, entre outras.
- **Rodar o script de web scraping**: Executa o script `webscrapping_dash_githubactions.py`, que coleta dados do site e atualiza o arquivo CSV.
- **Commitar e enviar o CSV atualizado**: O arquivo `nivel_dos_rios.csv` é commitado e enviado de volta ao repositório.

### 2. **Agendamento do Workflow**

O workflow está configurado para rodar automaticamente todos os dias às 03:00 UTC, com o seguinte agendamento:

```yaml
on:
  schedule:
    - cron: '0 3 * * *'  # Roda todos os dias às 03:00 UTC
```

Além disso, o workflow também pode ser executado manualmente através da interface do GitHub Actions, permitindo que você execute o processo a qualquer momento.

### 3. **Web Scraping com Selenium**

O script Python `webscrapping_dash_githubactions.py` utiliza o Selenium para fazer o scraping de dados de um site e salvar essas informações no arquivo CSV.

O Selenium interage com a página web da mesma forma que um usuário faria, o que torna a coleta de dados dinâmica e eficiente.

### 4. **Dependências**

As dependências do projeto estão listadas no arquivo `requirements.txt`. Para instalar as dependências localmente, use o seguinte comando:

```bash
pip install -r requirements.txt
```

## Como Rodar Localmente

Se você quiser rodar o script de **web scraping** localmente, siga os seguintes passos:

### Passo 1: Instale as dependências

Execute o comando abaixo para instalar as dependências do projeto:

```bash
pip install -r requirements.txt
```

### Passo 2: Instale o Chrome e o Chromedriver

Para rodar o Selenium, você precisa do Chrome e do Chromedriver. Baixe e instale o Chrome, e o Chromedriver compatível com sua versão do navegador.

### Passo 3: Execute o script

Para rodar o script de web scraping localmente, basta executar o comando:

```bash
python webscrapping_dash_githubactions.py
```

Isso fará o scraping dos dados e atualizará o arquivo CSV.

## GitHub Actions

O workflow no GitHub Actions está configurado para rodar todos os dias às 03:00 UTC, mas você também pode rodá-lo manualmente na interface do GitHub Actions.

### Como Rodar Manualmente

1. Acesse a aba **Actions** no seu repositório.
2. Encontre o workflow **Atualizar CSV com Web Scraping**.
3. Clique no workflow e depois clique em **Run workflow** para executar o processo manualmente.

## Configuração do GitHub Actions

Aqui está o arquivo `.github/workflows/update_csv.yml` que configura o workflow:

```yaml
name: Atualizar CSV com Web Scraping

on:
  schedule:
    - cron: '0 3 * * *'  # Roda todos os dias às 03:00 UTC
  workflow_dispatch:  # Permite rodar manualmente

jobs:
  update_csv:
    runs-on: ubuntu-latest

    steps:
      - name: Clonar o repositório
        uses: actions/checkout@v4

      - name: Instalar dependências
        run: |
          sudo apt-get update
          sudo apt-get install -y chromium-browser chromium-chromedriver
          pip install -r requirements.txt

      - name: Rodar o script de web scraping
        run: python webscrapping_dash_githubactions.py

      - name: Commitar e enviar o CSV atualizado
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "github-actions@github.com"
          git add nivel_dos_rios.csv
          git commit -m "Atualização automática do CSV"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Permissões para o GitHub Actions

O GitHub Actions usa um token (`GITHUB_TOKEN`) para autenticar e permitir o envio das alterações para o repositório. Este token é gerado automaticamente pelo GitHub e não precisa ser configurado manualmente.

## Contribuições

Se você deseja contribuir com este projeto, fique à vontade para enviar **pull requests**. Qualquer melhoria, correção de bugs ou novas funcionalidades são bem-vindas!
