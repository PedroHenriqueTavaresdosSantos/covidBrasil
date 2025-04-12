from fpdf import FPDF
import pandas as pd
from analysis_utils import calculate_variation, top_states

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "COVID-19 Brazil Report", 0, 1, "C")
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_report():
    df = pd.read_csv("../data/casos_brasil.csv", parse_dates=["data"])
    pdf = PDF()
    pdf.add_page()
    
    # Metadata
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Source: Brasil.IO | Updated: {df['data'].max().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(10)
    
    # Analysis
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Key Insights", 0, 1)
    pdf.set_font("Arial", "", 12)
    
    variation = calculate_variation(df)
    text = f"• Monthly change: {'+' if variation > 0 else ''}{variation}% in cases\n"
    text += f"• Total cases: {df['confirmados'].sum():,}\n"
    text += f"• Total deaths: {df['obitos'].sum():,}"
    pdf.multi_cell(0, 10, text)
    pdf.ln(15)
    
    # Top states tables
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Top 5 States - Cases", 0, 1)
    pdf.set_font("Arial", "", 10)
    
    for _, row in top_states(df, "confirmados").iterrows():
        pdf.cell(0, 10, f"{row['estado']}: {row['confirmados']:,}", 0, 1)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Top 5 States - Deaths", 0, 1)
    pdf.set_font("Arial", "", 10)
    
    for _, row in top_states(df, "obitos").iterrows():
        pdf.cell(0, 10, f"{row['estado']}: {row['obitos']:,}", 0, 1)
    
    # Visualizations
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Visualizations", 0, 1)
    pdf.image("../data/graficos/evolucao_mensal.png", x=10, w=180)
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, "Interactive map: /graficos/mapa_estados.html", 0, 1)
    
    pdf.output("../data/relatorios/relatorio_covid.pdf")

if __name__ == "__main__":
    generate_report()