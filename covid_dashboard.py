import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import shutil
import os
import warnings

# Suprimir warnings do Seaborn sobre paletas
warnings.filterwarnings("ignore", category=UserWarning)

def coletar_dados_covid():
    url = "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv"
    
    try:
        print("📥 Baixando dados atualizados de COVID-19...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        dados = pd.read_csv(StringIO(response.text))
        dados_estados = dados[~dados['state'].isin(['TOTAL', 'BRASIL'])]
        data_mais_recente = dados_estados['date'].max()
        dados_atualizados = dados_estados[dados_estados['date'] == data_mais_recente].copy()
        
        dados_atualizados['Populacao'] = (dados_atualizados['totalCases'] / 
                                        dados_atualizados['totalCases_per_100k_inhabitants']) * 100000
        
        dados_finais = dados_atualizados[['state', 'totalCases', 'deaths', 'Populacao']].copy()
        dados_finais = dados_finais.rename(columns={
            'state': 'Estado',
            'totalCases': 'Casos_Confirmados',
            'deaths': 'Mortes'
        })
        
        dados_finais['Taxa_Mortalidade'] = dados_finais.apply(
            lambda x: (x['Mortes'] / x['Casos_Confirmados'] * 100) if x['Casos_Confirmados'] > 0 else 0,
            axis=1
        )
        
        melhor_estado = dados_finais.loc[dados_finais['Taxa_Mortalidade'].idxmin()].copy()
        pior_estado = dados_finais.loc[dados_finais['Taxa_Mortalidade'].idxmax()].copy()
        
        print("✅ Dados coletados com sucesso!")
        return dados_finais, melhor_estado, pior_estado
        
    except Exception as e:
        print(f"❌ Erro ao coletar dados: {e}")
        return None, None, None

def gerar_visualizacoes(dados, pasta_destino):
    try:
        print("\n🎨 Gerando visualizações...")
        plt.figure(figsize=(18, 14))
        sns.set_theme(style="whitegrid")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.titlesize'] = 14
        
        # Configuração comum para os gráficos
        def configurar_grafico(ax, titulo):
            ax.set_title(titulo, pad=15)
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.bar_label(ax.containers[0], fmt='%.0f', padding=5, fontsize=10)
        
        # Gráfico 1: Casos Confirmados
        plt.subplot(2, 2, 1)
        ax1 = sns.barplot(x='Casos_Confirmados', y='Estado',
                         data=dados.nlargest(10, 'Casos_Confirmados'),
                         palette="Blues_d", hue='Estado', legend=False)
        configurar_grafico(ax1, 'Top 10 Estados - Casos Confirmados')
        
        # Gráfico 2: Óbitos
        plt.subplot(2, 2, 2)
        ax2 = sns.barplot(x='Mortes', y='Estado',
                         data=dados.nlargest(10, 'Mortes'),
                         palette="Reds_d", hue='Estado', legend=False)
        configurar_grafico(ax2, 'Top 10 Estados - Óbitos')
        
        # Gráfico 3: Taxa de Mortalidade
        plt.subplot(2, 2, 3)
        ax3 = sns.barplot(x='Taxa_Mortalidade', y='Estado',
                         data=dados.nlargest(10, 'Taxa_Mortalidade'),
                         palette="Purples_d", hue='Estado', legend=False)
        configurar_grafico(ax3, 'Top 10 Estados - Taxa de Mortalidade (%)')
        
        # Gráfico 4: Incidência
        plt.subplot(2, 2, 4)
        dados['Incidencia'] = (dados['Casos_Confirmados'] / dados['Populacao']) * 100000
        ax4 = sns.barplot(x='Incidencia', y='Estado',
                         data=dados.nlargest(10, 'Incidencia'),
                         palette="Greens_d", hue='Estado', legend=False)
        configurar_grafico(ax4, 'Top 10 Estados - Incidência (por 100k hab.)')
        
        plt.tight_layout()
        output_file = os.path.join(pasta_destino, 'covid_estados.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"🖼️ Visualizações salvas em {output_file}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar visualizações: {e}")

def criar_dashboard_html(pasta_destino, data_str, melhor_estado, pior_estado):
    try:
        print("\n🛠️ Criando página HTML do dashboard...")
        
        def formatar_numero(num):
            return f"{num:,.0f}".replace(",", ".")
        
        def formatar_taxa(taxa):
            return f"{taxa:.2f}".replace(".", ",")
        
        data_formatada = f"{data_str[:4]}-{data_str[4:6]}-{data_str[6:8]}"
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard COVID-19 - {data_formatada}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .destaque {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .melhor {{ color: #27ae60; font-weight: bold; }}
        .pior {{ color: #e74c3c; font-weight: bold; }}
        img {{ max-width: 100%; height: auto; margin-top: 20px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>📊 Dashboard COVID-19 - {data_formatada}</h1>
    
    <div class="destaque">
        <p>Estado com <span class="melhor">menor</span> taxa de mortalidade: 
        <strong>{melhor_estado['Estado']}</strong> ({formatar_taxa(melhor_estado['Taxa_Mortalidade'])}%)</p>
        
        <p>Estado com <span class="pior">maior</span> taxa de mortalidade: 
        <strong>{pior_estado['Estado']}</strong> ({formatar_taxa(pior_estado['Taxa_Mortalidade'])}%)</p>
    </div>
    
    <img src="covid_estados.png" alt="Gráficos COVID-19">
    
    <p><a href="../index.html">↩ Voltar para o histórico</a></p>
</body>
</html>"""
        
        with open(os.path.join(pasta_destino, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("✅ Página HTML criada com sucesso")
            
    except Exception as e:
        print(f"❌ Erro ao criar HTML: {e}")

def criar_index_principal():
    try:
        print("\n📂 Gerando índice principal de dashboards...")
        os.makedirs('docs', exist_ok=True)
        
        pastas = sorted([
            p for p in os.listdir('docs')
            if os.path.isdir(os.path.join('docs', p)) and p.isdigit()
        ], reverse=True)[:10]  # Limitar aos 10 mais recentes

        links = '\n'.join([
            f'<li><a href="{p}/index.html">Dashboard {p[:4]}-{p[4:6]}-{p[6:]}</a></li>'
            for p in pastas
        ])

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Histórico de Dashboards COVID-19</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #3498db; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>📅 Histórico de Dashboards COVID-19</h1>
    <ul>
        {links}
    </ul>
    <p>Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</body>
</html>"""

        with open('docs/index.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        # Criar arquivo .nojekyll
        with open('docs/.nojekyll', 'w') as f:
            pass
            
        print("✅ Índice principal atualizado")
        
    except Exception as e:
        print(f"❌ Erro ao criar índice: {e}")

def main():
    print("\n🔁 Iniciando processo de atualização do dashboard...")
    dados, melhor_estado, pior_estado = coletar_dados_covid()
    
    if dados is not None:
        data_str = datetime.now().strftime('%Y%m%d')
        pasta_destino = os.path.join('docs', data_str)
        os.makedirs(pasta_destino, exist_ok=True)

        # Gerar conteúdo do dashboard
        gerar_visualizacoes(dados, pasta_destino)
        criar_dashboard_html(pasta_destino, data_str, melhor_estado, pior_estado)
        
        # Salvar dados em CSV
        dados.to_csv(os.path.join(pasta_destino, f'dados_{data_str}.csv'),
                     index=False, encoding='utf-8-sig')
        
        # Atualizar índice principal
        criar_index_principal()
        
        print(f"\n🎉 Dashboard atualizado com sucesso! Acesse: docs/{data_str}/index.html")

if __name__ == "__main__":
    main()