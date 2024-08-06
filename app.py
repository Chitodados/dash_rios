import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuração do seaborn
sns.set(style='whitegrid')

df = pd.read_excel('nivel_dos_rios_ultimos_5_anos.xlsx')

# Fragmentar a coluna 'Data' em colunas separadas de dia, mês e ano
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
df['Dia'] = df['Data'].dt.day
df['Mês'] = df['Data'].dt.month
df['Ano'] = df['Data'].dt.year

# Derreter o DataFrame para que as colunas dos rios se tornem linhas
df_melted = df.melt(id_vars=['Data', 'Dia', 'Mês', 'Ano'], var_name='Rio', value_name='Cota')

# Filtrar as linhas para manter apenas as linhas com valores de cota
df_melted = df_melted.dropna(subset=['Cota'])

# Remover a coluna 'Data' já que temos dia, mês e ano
df_melted = df_melted.drop(columns=['Data'])

# Reorganizar as colunas para uma melhor visualização
df_melted = df_melted[['Ano', 'Mês', 'Dia', 'Rio', 'Cota']].rename(columns={'Rio':'rio','Ano':'year','Mês':'month','Dia':'day','Cota':'altura'})

df=df_melted.copy()
# Crie a interface do usuário
st.title('Dashboard dos Níveis dos Rios')

# Opção de seleção múltipla de rios
available_rivers = df['rio'].unique()
selected_rivers = st.multiselect('Escolha o(s) rio(s)', available_rivers, default=available_rivers)

available_years = df['Ano'].unique()
selected_years = st.multiselect('Escolha o(s) ano(s)', available_years, default=available_years)

# Filtra os dados com base nos rios selecionados
filtered_data = df[df['rio'].isin(selected_rivers)]

if not filtered_data.empty:
    # Agrupa os dados por rio
    rios = filtered_data.groupby('rio')

    for rio, data in rios:
        plt.figure(figsize=(18, 8))
        
        # Plot das linhas com transparência padrão (1.0) e incluir na legenda
        sns.lineplot(data=data, x="month", y="altura", hue="year", palette="husl", linewidth=3, estimator='mean', ci=None)
        
        # Plot das sombras dos desvios com maior transparência (alpha=0.2) e não incluir na legenda
        sns.lineplot(data=data, x="month", y="altura", hue="year", palette="husl", linewidth=0, estimator='mean', ci='sd', alpha=0.1, legend=False)
        
        sns.despine(offset=10, trim=True)
        plt.legend(loc='upper right')
        plt.xticks(ticks=range(1, 13))
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Cota (m)', fontsize=14)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['left'].set_linewidth(1.5)
        plt.gca().spines['bottom'].set_linewidth(1.5)
        plt.gca().spines['left'].set_color('gray')
        plt.gca().spines['bottom'].set_color('gray')
        plt.gca().tick_params(axis='both', which='major', labelsize=12, color='gray', width=1.5)
        plt.gca().set_facecolor('#f0f0f0')
        
        # Mostra o gráfico no Streamlit
        st.pyplot(plt)
else:
    st.write('Nenhum dado disponível para os rios selecionados.')
