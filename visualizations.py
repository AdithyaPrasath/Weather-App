# visualizations.py

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DATABASE = 'weather_data.db'  # Replace with your actual database name

def fetch_daily_weather_summaries():
    with sqlite3.connect(DATABASE) as conn:
        query = "SELECT * FROM daily_weather_summary"
        df = pd.read_sql_query(query, conn)
    return df

def visualize_daily_weather(city):
    df = fetch_daily_weather_summaries()
    city_data = df[df['city'] == city]
    city_data['date'] = pd.to_datetime(city_data['date'])
    city_data = city_data.sort_values('date')
    
    plt.figure(figsize=(12, 6))
    plt.plot(city_data['date'], city_data['avg_temp'], label='Average Temperature', marker='o')
    plt.plot(city_data['date'], city_data['max_temp'], label='Max Temperature', marker='o')
    plt.plot(city_data['date'], city_data['min_temp'], label='Min Temperature', marker='o')
    
    plt.title(f'Daily Weather Summary for {city}')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()

def visualize_historical_trends():
    df = fetch_daily_weather_summaries()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    plt.figure(figsize=(12, 6))
    
    for city in df['city'].unique():
        city_data = df[df['city'] == city]
        plt.plot(city_data['date'], city_data['avg_temp'], label=city, marker='o')
    
    plt.title('Historical Average Temperature Trends')
    plt.xlabel('Date')
    plt.ylabel('Average Temperature (°C)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()

def visualize_triggered_alerts(alert_data):
    cities = list(alert_data.keys())
    alert_counts = list(alert_data.values())
    
    plt.figure(figsize=(10, 5))
    plt.bar(cities, alert_counts, color='orange')
    
    plt.title('Triggered Alerts by City')
    plt.xlabel('City')
    plt.ylabel('Number of Alerts')
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()