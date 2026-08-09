import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard COVID-19 - UNICAMP", layout="wide", page_icon="🦠")

st.title("🦠 Dashboard Interativo COVID-19 (Our World in Data)")
st.caption("Disciplina: Ciência de Dados — Prof. Francisco Fambrini (UNICAMP)")

@st.cache_data(ttl=3600)
def load_data():
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )
    query = """
    SELECT LOCATION, CONTINENT, DATE, TOTAL_CASES, NEW_CASES, TOTAL_DEATHS, NEW_DEATHS 
    FROM OWID_COVID_DATA
    ORDER BY DATE DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df

with st.spinner("Conectando ao Snowflake..."):
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"Erro ao conectar ao Snowflake: {e}")
        st.stop()

st.sidebar.header("Filtros de Análise")
continentes = sorted(df_raw['CONTINENT'].unique())
continente_selecionado = st.sidebar.multiselect("Selecione o(s) Continente(s)", continentes, default=continentes[:2])

df_filtrado = df_raw[df_raw['CONTINENT'].isin(continente_selecionado)]
paises = sorted(df_filtrado['LOCATION'].unique())
pais_selecionado = st.sidebar.selectbox("Selecione um País", paises, index=0 if "Brazil" not in paises else paises.index("Brazil"))

df_pais = df_filtrado[df_filtrado['LOCATION'] == pais_selecionado]
st.subheader(f"Cenário Atual: {pais_selecionado}")

if not df_pais.empty:
    latest_data = df_pais.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Casos", f"{int(latest_data['TOTAL_CASES']):,}")
    col2.metric("Novos Casos", f"{int(latest_data['NEW_CASES']):,}")
    col3.metric("Total de Óbitos", f"{int(latest_data['TOTAL_DEATHS']):,}")
    col4.metric("Novos Óbitos", f"{int(latest_data['NEW_DEATHS']):,}")

st.markdown("---")
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    fig_cases = px.line(df_pais, x='DATE', y='TOTAL_CASES', title=f"Casos em {pais_selecionado}")
    st.plotly_chart(fig_cases, use_container_width=True)

with col_graph2:
    df_comp = df_filtrado.groupby('LOCATION')['TOTAL_DEATHS'].max().reset_index()
    df_comp = df_comp.sort_values(by='TOTAL_DEATHS', ascending=False).head(10)
    fig_bar = px.bar(df_comp, x='LOCATION', y='TOTAL_DEATHS', title="Top 10 Óbitos no Continente")
    st.plotly_chart(fig_bar, use_container_width=True)
