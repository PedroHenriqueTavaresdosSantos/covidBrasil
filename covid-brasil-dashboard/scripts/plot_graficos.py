import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os

def generate_visualizations():
    df = pd.read_csv("../data/casos_brasil.csv", parse_dates=["data"])
    os.makedirs("../data/graficos/", exist_ok=True)
    os.makedirs("../docs/graficos/", exist_ok=True)
    
    # Monthly trend (Matplotlib)
    df["mes"] = df["data"].dt.to_period("M")
    monthly = df.groupby("mes")[["confirmados", "obitos"]].sum()
    
    plt.figure(figsize=(10, 6))
    plt.plot(monthly.index.astype(str), monthly["confirmados"], label="Cases")
    plt.plot(monthly.index.astype(str), monthly["obitos"], label="Deaths")
    plt.title("Monthly COVID-19 Trend in Brazil")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig("../data/graficos/evolucao_mensal.png")
    plt.close()
    
    # State map (Plotly)
    fig = px.choropleth(
        df,
        locations="estado",
        locationmode="BR-UF",
        color="confirmados",
        scope="south america",
        title="Cases by State"
    )
    fig.write_html("../data/graficos/mapa_estados.html")
    fig.write_html("../docs/graficos/mapa_estados.html")  # For GitHub Pages

if __name__ == "__main__":
    generate_visualizations()