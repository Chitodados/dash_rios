import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from io import BytesIO
import requests


# Configuração do seaborn
sns.set(style='whitegrid')

# Caminho para o arquivo Excel. Essa opção para caso o arquivo esteja em pasta local:
# file_path = r'C:\Python_projetos\Webscrapping_Dash_Rios\dados_rios\nivel_dos_rios_ultimos_5_anos.xlsx'
# Carregar os dados do Excel
# df = pd.read_excel(file_url)


# URL do arquivo Excel no GitHub. Essa opçao para caso o arquivo já tenha subido p github:
file_url = "https://raw.githubusercontent.com/Chitolina/dash_rios/main/dados_rios/nivel_dos_rios_ultimos_5_anos.xlsx"


# Baixar o conteúdo do arquivo usando requests
response = requests.get(file_url)

# Verificar se o download foi bem-sucedido
if response.status_code == 200:
    # Carregar o conteúdo do arquivo como se fosse um arquivo em memória
    file_content = BytesIO(response.content)
    df = pd.read_excel(file_content)
    st.write(df)
else:
    st.error("Erro ao baixar o arquivo do GitHub")


# Fragmentar a coluna 'Data' em colunas separadas de dia, mês e ano
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
df['Dia'] = df['Data'].dt.day
df['Mês'] = df['Data'].dt.month
df['Ano'] = df['Data'].dt.year.astype(int)  # Garantir que o ano seja int

# Melt no DataFrame para que as colunas dos rios se tornem linhas
df_melted = df.melt(id_vars=['Data', 'Dia', 'Mês', 'Ano'], var_name='Rio', value_name='Cota')

# Filtrar as linhas para manter apenas as linhas com valores de cota
df_melted = df_melted.dropna(subset=['Cota'])

# Remover a coluna 'Data' já que temos dia, mês e ano
df_melted = df_melted.drop(columns=['Data'])

df_melted = df_melted[['Ano', 'Mês', 'Dia', 'Rio', 'Cota']].rename(columns={'Rio': 'rio', 'Ano': 'year', 'Mês': 'month', 'Dia': 'day', 'Cota': 'altura'})

df = df_melted.copy().fillna(0)

# Filtrar rios indesejados, pq em alguns anos não têm dados
df = df.loc[~df['rio'].isin(['Stº. Ant. Içá', 'Iquitos', 'Coari'])]

# Ajustar nomes dos rios
dic = {
    'Tabatinga': 'Tabatinga: Solimões',
    'Itacoatiara': 'Itacoatiara: Rio Amazonas',
    'Manaus': 'Manaus: Rio Amazonas'
}
df['rio'] = df['rio'].replace(dic)





# Opções de rios
rios = df['rio'].unique()
selected_river = st.sidebar.selectbox('Escolha a cidade/rio:', rios)

# Opções de meses
meses = list(range(1, 13))
meses_selecionados = st.sidebar.multiselect(
    'Escolha os meses (para a tabela):', 
    options=["Todos os meses"] + meses, 
    default=["Todos os meses"]
)

# Opções de anos
anos = sorted(df['year'].unique())
anos_selecionados = st.sidebar.multiselect(
    'Escolha os anos para comparar:', 
    options=["Todos os anos"] + anos, 
    default=["Todos os anos"]
)





# Lógica para aplicar os filtros "Todos os meses" ou "Todos os anos"
if "Todos os meses" in meses_selecionados:
    meses_selecionados = meses  # Todos os meses
if "Todos os anos" in anos_selecionados:
    anos_selecionados = anos  # Todos os anos





# Garantir que pelo menos dois anos estejam selecionados
if len(anos_selecionados) < 2:
    st.warning('Por favor, selecione pelo menos dois anos para realizar a comparação.')
    st.stop()

# Função para prever o valor do ARIMA para cada rio. Arima é o método de previsão de dados que usarei pro ano de 2025
def forecast_arima(rio_data, months_to_predict=12):
    # Usar ARIMA para prever
    model = ARIMA(rio_data, order=(1, 1, 1))  
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=months_to_predict)
    return forecast







# Realizando a previsão para o ano de 2025
df_2025_forecast = pd.DataFrame()

for rio in df['rio'].unique():
    for month in range(1, 13):
        # Filtrar dados históricos para cada rio e mês
        rio_month_data = df[(df['rio'] == rio) & (df['month'] == month) & (df['year'] < 2025)]
        if not rio_month_data.empty:
            # Prever os valores para 2025
            forecast_values = forecast_arima(rio_month_data['altura'])
            forecast_df = pd.DataFrame({
                'year': [2025] * len(forecast_values),
                'month': [month] * len(forecast_values),
                'rio': [rio] * len(forecast_values),
                'Previsão': forecast_values
            })
            df_2025_forecast = pd.concat([df_2025_forecast, forecast_df], ignore_index=True)

# Concatenando os dados históricos e a previsão para 2025
df_concat = pd.concat([df, df_2025_forecast])

# Filtrar os dados para o gráfico
graficos = df_concat[(df_concat['rio'] == selected_river) & (df_concat['year'].isin(anos_selecionados))]

# Filtrar os dados para a tabela
filtrada = df[
    (df['rio'] == selected_river) & 
    (df['year'].isin(anos_selecionados)) & 
    (df['month'].isin(meses_selecionados))
]





# Estilização do dash

st.markdown("""
<style>
/* Fundo geral */
main {
    background-color: #F0F2F6;
}

/* Cor do texto principal */
div[data-testid="stMarkdownContainer"] {
    color: #424242 ;
    font-size: 16px;
}

/* Cores específicas para cabeçalhos */
h1, h2, h3, h4, h5, h6 {
    color: #424242 ;
}

/* Cor do título da barra lateral */
[data-testid="stSidebar"] h1 {
    color: #424242 ;
}

/* Fundo da barra lateral */
[data-testid="stSidebar"] {
    background-color: #C8E6C9;
}
</style>
""", unsafe_allow_html=True)




# Gráfico com a evolução das cotas


st.markdown("### Evolução da cota ao longo dos meses e anos")
if not graficos.empty:
    plt.figure(figsize=(12, 6))

    # Gráfico para os dados históricos
    sns.lineplot(data=graficos[graficos['year'] != 2025], x='month', y='altura', hue='year', style='year', markers=True, dashes=False, palette='viridis')

    # Gráfico para os dados de previsão (2025) - linha pontilhada
    sns.lineplot(data=graficos[graficos['year'] == 2025], x='month', y='Previsão', color='red', linestyle='--', label='Previsão 2025')

    plt.title(f'{selected_river}', fontsize=16)
    plt.xlabel('Mês', fontsize=14)
    plt.ylabel('Cota (m)', fontsize=14)
    plt.legend(title='Ano')
    st.pyplot(plt.gcf())
else:
    st.write('Nenhum dado disponível para o gráfico.')

# Tabela de variação mês a mês
st.markdown("### Tabela de Variação de Cota Média")
if not filtrada.empty:
    comparacao = []
    anos_selecionados_sorted = sorted(anos_selecionados)
    for month in sorted(filtrada['month'].unique()):
        for i in range(1, len(anos_selecionados_sorted)):
            ano_1 = anos_selecionados_sorted[i - 1]
            ano_2 = anos_selecionados_sorted[i]
            
            # Calcular médias
            dados_ano_1 = filtrada[(filtrada['year'] == ano_1) & (filtrada['month'] == month)]['altura'].mean()
            dados_ano_2 = filtrada[(filtrada['year'] == ano_2) & (filtrada['month'] == month)]['altura'].mean()
            
            # Verificar se há valores válidos para os anos comparados
            if pd.notna(dados_ano_1) and pd.notna(dados_ano_2):
                # Calcular variações
                variation_absolute = dados_ano_2 - dados_ano_1
                variation_percentage = (variation_absolute / dados_ano_1) * 100 if dados_ano_1 != 0 else 0

                # Adicionar dados à lista
                comparacao.append({
                    'Mês': month,
                    'Ano Anterior': str(ano_1),
                    'Ano Posterior': str(ano_2),  # Garantindo que o ano posterior seja exibido corretamente
                    'Cota Média (m) Ano Anterior': f"{dados_ano_1:.1f}",  # 1 casa decimal
                    'Cota Média (m) Ano Posterior': f"{dados_ano_2:.1f}",  # 1 casa decimal
                    'Variação Absoluta (m)': f"{variation_absolute:.1f}",  # 1 casa decimal
                    'Variação Percentual (%)': f"{variation_percentage:.1f}%"  # 1 casa decimal
                })
    
    if comparacao:
        comparison_df = pd.DataFrame(comparacao)
        comparison_df = comparison_df.set_index('Mês')
        st.dataframe(comparison_df, use_container_width=True)
    else:
        st.write("Nenhuma comparação válida disponível para os dados selecionados.")
else:
    st.write("Nenhum dado disponível para os filtros selecionados.")


st.markdown("---")

st.write("**Fonte dos Dados:** https://proamanaus.com.br/nivel-dos-rios")
st.write("**Desenvolvido por:** [Lucas Chitolina](https://github.com/Chitolina) & [ChatGPT](https://openai.com/index/chatgpt/)")
