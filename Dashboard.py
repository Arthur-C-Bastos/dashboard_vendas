import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout = 'wide')

def formata_numero(valor, prefixo = ''):
  for unidade in ['', 'mil']:
   if valor <1000:
    return f'{prefixo} {valor:.2f} {unidade}'
   valor /= 1000
  return f'{prefixo} {valor:.2f} milhões'
 

st.title("DASHBOARD DE VENDAS 🛒")

url = 'https://labdados.com/produtos' 
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
   regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)

if todos_anos:
   ano = ''
else:
   ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}

response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')


filtro_vendedores = st.sidebar.multiselect('vendedores', dados['Vendedor'].unique())
if filtro_vendedores: 
   dados = dados[dados['Vendedor'].isin(filtro_vendedores)]



## Tabelas

##Tabela Receitas
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)



receita_mensal = dados.set_index('Data da compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index()
receita_mensal ['Ano'] = receita_mensal['Data da compra'].dt.year
receita_mensal ['Mes'] = receita_mensal['Data da compra'].dt.month_name()


receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)


##Tabelas Vendas 
vendas_categoria = (
    dados.groupby('Categoria do Produto')
    .size()
    .reset_index(name='Quantidade de Vendas')
    .sort_values('Quantidade de Vendas', ascending=False)
)

vendas_produto = (
    dados.groupby('Produto')
    .size()
    .reset_index(name='Quantidade de Vendas')
    .sort_values('Quantidade de Vendas', ascending=False)
)


avaliacao_categoria = (
    dados.groupby('Categoria do Produto')[['Avaliação da compra']]
    .mean()
    .sort_values('Avaliação da compra', ascending=False)
    .reset_index()
)

pagamento_regiao = (
    dados.groupby(['Local da compra', 'Tipo de pagamento'])
    .size()
    .reset_index(name='Quantidade de Vendas')
)

## Tabelas Vendedores

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count']))







## Gáficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por estado'
)


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano', 
                             title = 'Receita mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')


fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top Estados (receita)')

fig_receita_estados.update_layout(yaxis_title = 'Receita')


fig_receita_categoria = px.bar(receita_categoria,
                               text_auto = True,
                               title = 'Receita por categoria'
                               )
fig_receita_categoria.update_layout(yaxis_title = 'Receita')


fig_vendas_categoria = px.bar(
    vendas_categoria,
    x='Quantidade de Vendas',
    y='Categoria do Produto',
    orientation='h',
    text_auto=True,
    title='Número de Vendas por Categoria',
    color='Categoria do Produto',
    template='seaborn'
)
fig_vendas_categoria.update_layout(showlegend=False, yaxis_title='Categoria')

# Gráfico de vendas por produto (opcional: mostrar apenas top 10)
fig_vendas_produto = px.bar(
    vendas_produto.head(10),
    x='Quantidade de Vendas',
    y='Produto',
    orientation='h',
    text_auto=True,
    title='Top 10 Produtos Mais Vendidos',
    color='Produto',
    template='seaborn'
)
fig_vendas_produto.update_layout(showlegend=False, yaxis_title='Produto')

fig_avaliacao_categoria = px.bar(
    avaliacao_categoria,
    x='Avaliação da compra',
    y='Categoria do Produto',
    orientation='h',
    text_auto='.2f',
    title='Avaliação média por categoria',
    color='Avaliação da compra',
    color_continuous_scale='blues',
    template='seaborn'
)
fig_avaliacao_categoria.update_layout(showlegend=False, xaxis_title='Avaliação média')

fig_pagamento_regiao = px.bar(
    pagamento_regiao,
    x='Local da compra',
    y='Quantidade de Vendas',
    color='Tipo de pagamento',
    title='Métodos de pagamento por região',
    barmode='group',
    text_auto=True,
    template='seaborn'
)
fig_pagamento_regiao.update_layout(yaxis_title='Número de vendas')





##Visualização no Streamlit

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)


    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categoria, use_container_width = True)

with aba2:
    col1, col2 = st.columns(2)

    
    with col1:
        st.metric('Total de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_categoria, use_container_width=True)
        st.plotly_chart(fig_avaliacao_categoria, use_container_width=True)

    with col2:
        st.metric('Categorias únicas', len(dados['Categoria do Produto'].unique()))
        st.plotly_chart(fig_vendas_produto, use_container_width=True)
        st.plotly_chart(fig_pagamento_regiao, use_container_width=True)
        

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$')) 
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)'
                                        ) 
        st.plotly_chart(fig_receita_vendedores)


    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))

        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quanidade de vendas)'
                                        )
        st.plotly_chart(fig_vendas_vendedores)
        






