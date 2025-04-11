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
        
        melhor_estado['Casos_Formatados'] = f"{melhor_estado['Casos_Confirmados']:,.0f}".replace(",", ".")
        melhor_estado['Mortes_Formatadas'] = f"{melhor_estado['Mortes']:,.0f}".replace(",", ".")
        pior_estado['Casos_Formatados'] = f"{pior_estado['Casos_Confirmados']:,.0f}".replace(",", ".")
        pior_estado['Mortes_Formatadas'] = f"{pior_estado['Mortes']:,.0f}".replace(",", ".")
        
        print("\nDados coletados com sucesso!")
        return dados_finais, melhor_estado, pior_estado
        
    except Exception as e:
        print(f"\nErro ao coletar dados: {e}")
        return None, None, None

def gerar_visualizacoes(dados):
    try:
        print("\nGerando visualizações...")
        plt.figure(figsize=(16, 12))
        
        sns.set_theme(style="whitegrid")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # Gráfico 1: Casos confirmados
        plt.subplot(2, 2, 1)
        ax1 = sns.barplot(x='Casos_Confirmados', y='Estado', 
                         data=dados.sort_values('Casos_Confirmados', ascending=False),
                         palette="Blues_d", legend=False, dodge=False)
        plt.title('Casos Confirmados por Estado', pad=20)
        ax1.bar_label(ax1.containers[0], fmt='%.0f', padding=3, fontsize=9)
        
        # Gráfico 2: Óbitos
        plt.subplot(2, 2, 2)
        ax2 = sns.barplot(x='Mortes', y='Estado',
                         data=dados.sort_values('Mortes', ascending=False),
                         palette="Reds_d", legend=False, dodge=False)
        plt.title('Óbitos por Estado', pad=20)
        ax2.bar_label(ax2.containers[0], fmt='%.0f', padding=3, fontsize=9)
        
        # Gráfico 3: Taxa de mortalidade
        plt.subplot(2, 2, 3)
        ax3 = sns.barplot(x='Taxa_Mortalidade', y='Estado',
                         data=dados.sort_values('Taxa_Mortalidade', ascending=False),
                         palette="Purples_d", legend=False, dodge=False)
        plt.title('Taxa de Mortalidade por Estado (%)', pad=20)
        ax3.bar_label(ax3.containers[0], fmt='%.2f', padding=3, fontsize=9)
        
        # Gráfico 4: Incidência
        plt.subplot(2, 2, 4)
        dados['Incidencia'] = (dados['Casos_Confirmados'] / dados['Populacao']) * 100000
        ax4 = sns.barplot(x='Incidencia', y='Estado',
                         data=dados.sort_values('Incidencia', ascending=False),
                         palette="Greens_d", legend=False, dodge=False)
        plt.title('Incidência (casos por 100k hab.)', pad=20)
        ax4.bar_label(ax4.containers[0], fmt='%.1f', padding=3, fontsize=9)
        
        plt.tight_layout()
        plt.savefig('covid_estados.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Visualizações salvas em covid_estados.png")
        
    except Exception as e:
        print(f"\nErro ao gerar visualizações: {e}")

def criar_pagina_html(dados, melhor_estado, pior_estado):
    try:
        print("\nCriando página HTML...")
        
        def formatar_numero(num):
            return f"{num:,.0f}".replace(",", ".")
        
        def formatar_taxa(taxa):
            return f"{taxa:.2f}".replace(".", ",")
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <!-- Seu template HTML completo aqui -->
        </html>
        """
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_template)
        print("Página HTML criada: index.html")
        
    except Exception as e:
        print(f"\nErro ao criar página HTML: {e}")

def main():
    print("Iniciando geração do dashboard...")
    dados_covid, melhor_estado, pior_estado = coletar_dados_covid()
    
    if dados_covid is not None:
        gerar_visualizacoes(dados_covid)
        criar_pagina_html(dados_covid, melhor_estado, pior_estado)
        
        # Preparar arquivos para GitHub Pages
        os.makedirs('docs', exist_ok=True)
        
        for arquivo in ['index.html', 'covid_estados.png']:
            if os.path.exists(arquivo):
                shutil.copy(arquivo, 'docs/')        
        with open('docs/.nojekyll', 'w') as f:
            pass
        
        data_atual = datetime.now().strftime('%Y%m%d')
        dados_covid.to_csv(f'docs/dados_covid_{data_atual}.csv', index=False, encoding='utf-8-sig')
        
        print("\n✅ Dashboard gerado com sucesso na pasta docs/")
        print(f"Acesse: https://pedrohenriquetavaresdossantos.github.io/covidBrasil/")
    else:
        print("\n❌ Falha na geração do dashboard")

if __name__ == "__main__":
      main()