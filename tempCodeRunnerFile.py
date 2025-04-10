import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import shutil
import os

def coletar_dados_covid():
    url = "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv"
    
    try:
        print("Baixando dados atualizados de COVID-19...")
        response = requests.get(url)
        response.raise_for_status()
        
        dados = pd.read_csv(StringIO(response.text))
        dados_estados = dados[~dados['state'].str.contains('TOTAL|BRASIL|XX')]
        data_mais_recente = dados_estados['date'].max()
        dados_atualizados = dados_estados[dados_estados['date'] == data_mais_recente].copy()
        
        dados_atualizados['Populacao'] = (dados_atualizados['totalCases'] / 
                                        dados_atualizados['totalCases_per_100k_inhabitants']) * 100000
        
        dados_finais = dados_atualizados[['state', 'totalCases', 'deaths', 'Populacao']]
        dados_finais = dados_finais.rename(columns={
            'state': 'Estado',
            'totalCases': 'Casos_Confirmados',
            'deaths': 'Mortes'
        })
        
        dados_finais['Taxa_Mortalidade'] = dados_finais.apply(
            lambda x: (x['Mortes'] / x['Casos_Confirmados']) * 100 if x['Casos_Confirmados'] > 0 else 0,
            axis=1
        )
        
        melhor_estado = dados_finais.loc[dados_finais['Taxa_Mortalidade'].idxmin()].copy()
        pior_estado = dados_finais.loc[dados_finais['Taxa_Mortalidade'].idxmax()].copy()
        
        print("\nDados coletados com sucesso!")
        return dados_finais, melhor_estado, pior_estado
        
    except Exception as e:
        print(f"\nErro ao coletar dados: {e}")
        return None, None, None

def gerar_visualizacoes(dados, pasta_destino):
    try:
        print("\nGerando visualizações...")
        plt.figure(figsize=(16, 12))
        sns.set_theme(style="whitegrid")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        plt.subplot(2, 2, 1)
        ax1 = sns.barplot(x='Casos_Confirmados', y='Estado', data=dados.sort_values('Casos_Confirmados', ascending=False),
                         palette="Blues_d", legend=False, dodge=False)
        plt.title('Casos Confirmados por Estado', pad=20)
        ax1.bar_label(ax1.containers[0], fmt='%.0f', padding=3, fontsize=9)
        
        plt.subplot(2, 2, 2)
        ax2 = sns.barplot(x='Mortes', y='Estado', data=dados.sort_values('Mortes', ascending=False),
                         palette="Reds_d", legend=False, dodge=False)
        plt.title('Óbitos por Estado', pad=20)
        ax2.bar_label(ax2.containers[0], fmt='%.0f', padding=3, fontsize=9)
        
        plt.subplot(2, 2, 3)
        ax3 = sns.barplot(x='Taxa_Mortalidade', y='Estado', data=dados.sort_values('Taxa_Mortalidade', ascending=False),
                         palette="Purples_d", legend=False, dodge=False)
        plt.title('Taxa de Mortalidade por Estado (%)', pad=20)
        ax3.bar_label(ax3.containers[0], fmt='%.2f', padding=3, fontsize=9)
        
        plt.subplot(2, 2, 4)
        dados['Incidencia'] = (dados['Casos_Confirmados'] / dados['Populacao']) * 100000
        ax4 = sns.barplot(x='Incidencia', y='Estado', data=dados.sort_values('Incidencia', ascending=False),
                         palette="Greens_d", legend=False, dodge=False)
        plt.title('Incidência (casos por 100k hab.)', pad=20)
        ax4.bar_label(ax4.containers[0], fmt='%.1f', padding=3, fontsize=9)
        
        plt.tight_layout()
        output_file = os.path.join(pasta_destino, 'covid_estados.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualizações salvas em {output_file}")
        
    except Exception as e:
        print(f"\nErro ao gerar visualizações: {e}")

def criar_dashboard_html(pasta_destino, data_str, melhor_estado, pior_estado):
    try:
        print("Criando página HTML do dashboard...")
        
        def formatar(valor): return f"{valor:,.0f}".replace(",", ".")
        def formatar_taxa(taxa): return f"{taxa:.2f}".replace(".", ",")
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dashboard COVID-19 - {data_str}</title>
</head>
<body>
    <h1>📊 Dashboard COVID-19 - {data_str}</h1>
    <p>Estado com <strong>menor</strong> taxa de mortalidade: {melhor_estado['Estado']} ({formatar_taxa(melhor_estado['Taxa_Mortalidade'])}%)</p>
    <p>Estado com <strong>maior</strong> taxa de mortalidade: {pior_estado['Estado']} ({formatar_taxa(pior_estado['Taxa_Mortalidade'])}%)</p>
    <img src="covid_estados.png" alt="Gráficos COVID-19" style="max-width: 100%; height: auto;">
</body>
</html>"""
        
        with open(os.path.join(pasta_destino, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
            
    except Exception as e:
        print(f"\nErro ao criar HTML: {e}")

def criar_index_principal():
    print("Gerando índice principal de dashboards...")
    pastas = sorted([
        p for p in os.listdir('docs')
        if os.path.isdir(os.path.join('docs', p)) and p.isdigit()
    ], reverse=True)

    links = '\n'.join([
        f'<li><a href="{p}/index.html">Dashboard {p[:4]}-{p[4:6]}-{p[6:]}</a></li>'
        for p in pastas
    ])

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Histórico de Dashboards COVID-19</title>
</head>
<body>
    <h1>📅 Histórico de Dashboards COVID-19</h1>
    <ul>
        {links}
    </ul>
</body>
</html>"""

    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    print("🔁 Iniciando geração do dashboard...")
    dados, melhor_estado, pior_estado = coletar_dados_covid()
    
    if dados is not None:
        data_str = datetime.now().strftime('%Y%m%d')
        pasta_destino = os.path.join('docs', data_str)
        os.makedirs(pasta_destino, exist_ok=True)

        gerar_visualizacoes(dados, pasta_destino)
        criar_dashboard_html(pasta_destino, data_str, melhor_estado, pior_estado)

        dados.to_csv(os.path.join(pasta_destino, f'dados_covid_brasil_{data_str}.csv'),
                     index=False, encoding='utf-8-sig')
        
        # Criar índice principal e .nojekyll
        os.makedirs('docs', exist_ok=True)
        criar_index_principal()
        with open('docs/.nojekyll', 'w') as f:
            f.write('')

        print(f"\n✅ Dashboard gerado com sucesso em docs/{data_str}/")

if __name__ == "__main__":
    main()
