import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from io import BytesIO
import requests

st.markdown("""
    # Monitoramento e Previsão dos Níveis de Água dos Rios

    **Cenário:**

    Sua empresa importa produtos por portos ligados a rios estratégicos. Alguns desses produtos possuem alta sazonalidade de venda no verão. No entanto, existe um histórico de redução significativa na cota dos rios devido à seca, o que pode inviabilizar o transporte por algumas rotas. Diante disso, é essencial monitorar os níveis de água dos rios e projetar tendências futuras para antecipar decisões estratégicas e mitigar riscos

    **Processo proposto:**

    - **Coleta de dados:** Extração automática ([web scraping](https://github.com/Chitolina/dash_rios/blob/main/webscrapping_dash.py/)) de informações brutas de uma fonte confiável ([Proama Amazonas](https://proamanaus.com.br/nivel-dos-rios/));
    - **Atualização automática:** Criada uma pipeline para executar o webscrapping diariamente e atualizar o dado no repositório via Github Actions;
    - **Manipulação e análise:** Processamento dos dados, criação de gráficos informativos e automação das análises utilizando Python;
    - **Projeção futura:** Aplicação de modelos de séries temporais, como ARIMA, para prever os níveis futuros dos rios;
    - **Deploy dinâmico:** Disponibilização das análises e previsões em uma plataforma mais intuitiva e acessível, como um dashboard interativo.
""", unsafe_allow_html=True)

# Configuração do seaborn
sns.set(style='whitegrid')

# Função para carregar os dados (com cache)
@st.cache_data
def load_data():
    # Caminho para o arquivo CSV
    file_path = "nivel_dos_rios.csv"  # Atualize o caminho conforme necessário

    # Verificar se o arquivo existe e ler os dados
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Verificar se o arquivo é mais recente do que o cache
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mod_time > datetime.now() - pd.Timedelta(hours=1):  # Atualizar o cache a cada hora, por exemplo
            st.cache_clear()  # Forçar a limpeza do cache para recarregar os dados

        # Manipulação dos dados (igual ao código original)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        df['Dia'] = df['Data'].dt.day
        df['Mês'] = df['Data'].dt.month
        df['Ano'] = df['Data'].dt.year.astype(int)

        # Melt no DataFrame para que as colunas dos rios se tornem linhas
        df_melted = df.melt(id_vars=['Data', 'Dia', 'Mês', 'Ano'], var_name='Rio', value_name='Cota')
        df_melted = df_melted.dropna(subset=['Cota'])

        df_melted = df_melted[['Ano', 'Mês', 'Dia', 'Rio', 'Cota']].rename(
            columns={'Rio': 'rio', 'Ano': 'year', 'Mês': 'month', 'Dia': 'day', 'Cota': 'altura'}
        )

        df = df_melted.copy().fillna(0)
        df = df.loc[~df['rio'].isin(['Stº. Ant. Içá', 'Iquitos', 'Coari'])]

        dic = {
            'Tabatinga': 'Tabatinga: Solimões',
            'Itacoatiara': 'Itacoatiara: Rio Amazonas',
            'Manaus': 'Manaus: Rio Amazonas'
        }
        df['rio'] = df['rio'].replace(dic)

        return df
    else:
        st.error("Arquivo CSV não encontrado.")
        return None

# Carregar os dados
df = load_data()

# Função para prever o valor do ARIMA para cada rio (com cache)
@st.cache_data
def forecast_arima(rio_data, months_to_predict=12):
    model = ARIMA(rio_data, order=(1, 1, 1))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=months_to_predict)
    return forecast

# Realizando a previsão para o ano de 2025 (com cache)
@st.cache_data
def get_2025_forecast(df):
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
                    'altura': forecast_values  # Use 'altura' para manter a consistência
                })
                df_2025_forecast = pd.concat([df_2025_forecast, forecast_df], ignore_index=True)

    return df_2025_forecast

# Concatenando os dados históricos e a previsão para 2025
df_2025_forecast = get_2025_forecast(df)
df_concat = pd.concat([df, df_2025_forecast])

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

    # Verificar se 2025 está nos anos selecionados ou se "Todos os anos" foi selecionado
    if 2025 in anos_selecionados or "Todos os anos" in anos_selecionados:
        sns.lineplot(data=graficos[graficos['year'] == 2025], x='month', y='altura', color='red', linestyle='--', label='Previsão 2025')

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
                    'Ano Posterior': str(ano_2),
                    'Cota Média (m) Ano Anterior': f"{dados_ano_1:.1f}",
                    'Cota Média (m) Ano Posterior': f"{dados_ano_2:.1f}",
                    'Variação Absoluta (m)': f"{variation_absolute:.1f}",
                    'Variação Percentual (%)': f"{variation_percentage:.1f}%"
                })

    if comparacao:
        comparison_df = pd.DataFrame(comparacao)
        comparison_df = comparison_df.set_index('Mês')
        st.dataframe(comparison_df, use_container_width=True)
    else:
        st.write("Nenhuma comparação válida disponível para os dados selecionados.")
else:
    st.write("Nenhum dado disponível para os filtros selecionados.")

# Botão para baixar os dados de variação
if 'comparison_df' in locals():
    st.download_button(
        label="Baixar dados de variação",
        data=comparison_df.to_csv(index=False).encode('utf-8'),
        file_name=f"variacao_cota_{selected_river}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.write("**Fonte dos Dados:** https://proamanaus.com.br/nivel-dos-rios")
st.write("**Desenvolvido por:** [Lucas Chitolina¹](https://github.com/Chitolina), [Lucas Chitolina²](https://chitolina.github.io), [DeepSeek](https://chat.deepseek.com/) & [ChatGPT](https://chatgpt.com)")
