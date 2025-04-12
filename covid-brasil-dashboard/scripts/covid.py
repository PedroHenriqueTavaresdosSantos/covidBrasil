import os
import requests
import pandas as pd
from datetime import datetime

def fetch_covid_data():
    """Coleta dados autenticados da API Brasil.IO"""
    token = os.getenv("BRASIL_IO_TOKEN")
    if not token:
        raise ValueError("Token da API não encontrado. Configure a variável BRASIL_IO_TOKEN")

    headers = {
        "Authorization": f"Token {token}",
        "User-Agent": "Python-COVID19-Brasil-Dashboard"
    }
    
    params = {
        "place_type": "state",
        "is_last": "True",
        "page_size": 100
    }

    try:
        response = requests.get(
            "https://api.brasil.io/v1/dataset/covid19/caso/data/",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data["results"])
        
        # Processamento dos dados
        df = df[["date", "state", "confirmed", "deaths"]].rename(columns={
            "date": "data",
            "state": "estado",
            "confirmed": "confirmados",
            "deaths": "obitos"
        })
        
        df.to_csv("../data/casos_brasil.csv", index=False)
        print(f"Dados atualizados em {datetime.now()}")
        
    except Exception as e:
        print(f"Erro na API: {e}")
        raise

if __name__ == "__main__":
    fetch_covid_data()