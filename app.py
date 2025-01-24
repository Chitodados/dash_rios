import streamlit as st
import pandas as pd
import numpy as np

# Título do aplicativo
st.title('Análise de Variações de Cotação de Rios')

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Faça o upload do arquivo CSV", type="csv")

if uploaded_file is not None:
    # Carregar os dados
    df = pd.read_csv(uploaded_file)

    # Verificar se o DataFrame possui as colunas necessárias
    required_columns = ['Data', 'Ano', 'Mes', 'Rio', 'Cota']
    if all(col in df.columns for col in required_columns):
        st.success("Dados carregados com sucesso!")

        # Seleção do rio
        rio_selecionado = st.selectbox("Selecione o rio:", df['Rio'].unique())

        # Filtrar os dados pelo rio selecionado
        df_rio = df[df['Rio'] == rio_selecionado]

        # Gerar lista de anos disponíveis
        anos_disponiveis = sorted(df_rio['Ano'].unique())

        # Seleção do intervalo de anos
        ano_1, ano_2 = st.select_slider(
            "Selecione o intervalo de anos para análise:",
            options=anos_disponiveis,
            value=(anos_disponiveis[0], anos_disponiveis[-1])
        )

        # Verificar se os anos são consecutivos
        if ano_2 - ano_1 != 1:
            st.warning("Por favor, selecione dois anos consecutivos para a análise.")
        else:
            # Filtrar dados para os anos selecionados
            df_ano_1 = df_rio[df_rio['Ano'] == ano_1]
            df_ano_2 = df_rio[df_rio['Ano'] == ano_2]

            # Inicializar a lista para armazenar a comparação
            comparacao = []

            # Iterar pelos meses
            for month in range(1, 13):
                # Filtrar os dados do mês atual para cada ano
                dados_ano_1 = df_ano_1[df_ano_1['Mes'] == month]['Cota'].mean()
                dados_ano_2 = df_ano_2[df_ano_2['Mes'] == month]['Cota'].mean()

                if pd.notna(dados_ano_1) and pd.notna(dados_ano_2):
                    # Calcular variação absoluta e percentual
                    variation_absolute = dados_ano_2 - dados_ano_1
                    variation_percentage = (variation_absolute / dados_ano_1) * 100

                    # Adicionar dados à lista
                    comparacao.append({
                        'Mês': month,
                        'Ano Anterior': str(ano_1),
                        'Ano Posterior': str(ano_2),
                        'Cota Média (m) Ano Anterior': f"{dados_ano_1:.1f}",  # 1 casa decimal
                        'Cota Média (m) Ano Posterior': f"{dados_ano_2:.1f}",  # 1 casa decimal
                        'Variação Absoluta (m)': f"{variation_absolute:.1f}",  # 1 casa decimal
                        'Variação Percentual (%)': f"{variation_percentage:.1f}"  # 1 casa decimal
                    })

            # Converter a lista em DataFrame para exibição
            df_comparacao = pd.DataFrame(comparacao)
            df_comparacao['Mês'] = df_comparacao['Mês'].apply(lambda x: f"{x:02d}")  # Formatar o mês com dois dígitos

            # Exibir a tabela
            st.dataframe(df_comparacao)
    else:
        st.error(f"As colunas obrigatórias não foram encontradas. Por favor, certifique-se de que o arquivo contém as seguintes colunas: {', '.join(required_columns)}")
else:
    st.info("Por favor, carregue um arquivo CSV para começar a análise.")
