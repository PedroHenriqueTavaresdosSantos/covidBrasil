import pandas as pd
from datetime import timedelta

def calculate_variation(df):
    """Calculate monthly variation percentage"""
    last_date = df["data"].max()
    month_ago = last_date - timedelta(days=30)
    
    current_cases = df[df["data"] == last_date]["confirmados"].sum()
    previous_cases = df[df["data"] >= month_ago]["confirmados"].sum()
    
    return round(((current_cases - previous_cases) / previous_cases) * 100, 2)

def top_states(df, column, n=5):
    """Get top N states by metric"""
    return df.sort_values(column, ascending=False).head(n)[["estado", column]]