import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import shutil
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

def coletar_dados_covid():
    url = "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv"
    
    try:
        print("📊 Coletando dados de COVID-19...")
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

def gerar_visualizacoes(dados, output_dir):
    try:
        print("\n🎨 Gerando visualizações...")
        plt.figure(figsize=(18, 12))
        sns.set_theme(style="whitegrid")
        
        # Gráfico 1: Casos Confirmados
        plt.subplot(2, 2, 1)
        ax1 = sns.barplot(x='Casos_Confirmados', y='Estado', 
                         data=dados.nlargest(10, 'Casos_Confirmados'),
                         palette="Blues_d", hue='Estado', legend=False)
        ax1.set_title('Top 10 Estados - Casos Confirmados', pad=15)
        ax1.bar_label(ax1.containers[0], fmt='%.0f', padding=5)
        
        # Gráfico 2: Óbitos
        plt.subplot(2, 2, 2)
        ax2 = sns.barplot(x='Mortes', y='Estado',
                         data=dados.nlargest(10, 'Mortes'),
                         palette="Reds_d", hue='Estado', legend=False)
        ax2.set_title('Top 10 Estados - Óbitos', pad=15)
        ax2.bar_label(ax2.containers[0], fmt='%.0f', padding=5)
        
        # Gráfico 3: Taxa de Mortalidade
        plt.subplot(2, 2, 3)
        ax3 = sns.barplot(x='Taxa_Mortalidade', y='Estado',
                         data=dados.nlargest(10, 'Taxa_Mortalidade'),
                         palette="Purples_d", hue='Estado', legend=False)
        ax3.set_title('Top 10 Estados - Taxa de Mortalidade (%)', pad=15)
        ax3.bar_label(ax3.containers[0], fmt='%.2f', padding=5)
        
        # Gráfico 4: Incidência
        plt.subplot(2, 2, 4)
        dados['Incidencia'] = (dados['Casos_Confirmados'] / dados['Populacao']) * 100000
        ax4 = sns.barplot(x='Incidencia', y='Estado',
                         data=dados.nlargest(10, 'Incidencia'),
                         palette="Greens_d", hue='Estado', legend=False)
        ax4.set_title('Top 10 Estados - Incidência (por 100k hab.)', pad=15)
        ax4.bar_label(ax4.containers[0], fmt='%.1f', padding=5)
        
        plt.tight_layout()
        output_file = os.path.join(output_dir, 'covid_estados.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"🖼️ Visualizações salvas em {output_file}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar gráficos: {e}")

def criar_pagina_html(output_dir, dados, melhor_estado, pior_estado):
    try:
        print("\n🛠️ Criando página HTML...")
        
        def formatar_numero(num):
            return f"{num:,.0f}".replace(",", ".")
        
        def formatar_taxa(taxa):
            return f"{taxa:.2f}".replace(".", ",")
        
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard COVID-19</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .info-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .melhor {{
            color: #27ae60;
            font-weight: bold;
        }}
        .pior {{
            color: #e74c3c;
            font-weight: bold;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin-top: 20px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>📊 Dashboard COVID-19 - Brasil</h1>
    
    <div class="info-box">
        <p>Data da última atualização: {data_atual}</p>
        <p>Estado com <span class="melhor">menor</span> taxa de mortalidade: 
        <strong>{melhor_estado['Estado']}</strong> ({formatar_taxa(melhor_estado['Taxa_Mortalidade'])}%)</p>
        
        <p>Estado com <span class="pior">maior</span> taxa de mortalidade: 
        <strong>{pior_estado['Estado']}</strong> ({formatar_taxa(pior_estado['Taxa_Mortalidade'])}%)</p>
    </div>
    
    <img src="covid_estados.png" alt="Gráficos COVID-19">
</body>
</html>"""
        
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("✅ Página HTML criada com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro ao criar HTML: {e}")

def main():
    print("\n🚀 Iniciando processo de atualização do dashboard...")
    dados, melhor_estado, pior_estado = coletar_dados_covid()
    
    if dados is not None:
        # Cria a pasta docs se não existir
        os.makedirs('docs', exist_ok=True)
        
        # Gera os gráficos e a página HTML
        gerar_visualizacoes(dados, 'docs')
        criar_pagina_html('docs', dados, melhor_estado, pior_estado)
        
        # Cria arquivos essenciais para GitHub Pages
        with open('docs/.nojekyll', 'w') as f:
            pass
        with open('docs/CNAME', 'w') as f:
            f.write('pedrohenriquetavaresdossantos.github.io')
        
        # Salva os dados completos
        dados.to_csv('docs/dados_completos.csv', index=False, encoding='utf-8-sig')
        
        print("\n🎉 Dashboard atualizado com sucesso!")
        print("🔗 Acesse: https://pedrohenriquetavaresdossantos.github.io/covidBrasil/")

if __name__ == "__main__":
    main()