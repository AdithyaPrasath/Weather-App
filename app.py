import time
import requests
import sqlite3
from flask import Flask, render_template, request, jsonify
from threading import Thread
import smtplib  # For sending email alerts
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from visualizations import visualize_daily_weather, visualize_historical_trends, visualize_triggered_alerts
import random
from datetime import datetime, timedelta



app = Flask(__name__)

API_KEY = '738448163c752fc5c32b99397fbedf1d'  # OpenWeatherMap API Key
DATABASE = 'weather_data.db'
# List of metros in India to track
METRO_CITIES = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temp REAL,
                feels_like REAL,
                wind REAL,
                uv REAL,
                visibility REAL,
                humidity INTEGER,
                pressure INTEGER,
                dt TIMESTAMP,
                max_temp REAL,
                min_temp REAL,
                condition TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                timestamp TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temp_threshold REAL,
                consecutive_count INTEGER DEFAULT 2
            )
        ''')
        
        # Initialize the daily weather summary table
        init_daily_weather_summary()
        init_forecast_table()

def init_forecast_table():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                date TEXT,
                temp_day REAL,
                temp_min REAL,
                temp_max REAL,
                condition TEXT,
                humidity INTEGER,
                wind_speed REAL
            )
        ''')
        conn.commit()

def init_daily_weather_summary():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_weather_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                date TEXT,
                avg_temp REAL,
                max_temp REAL,
                min_temp REAL,
                total_precipitation REAL,
                avg_wind_speed REAL,
                predominant_condition TEXT
            )
        ''')
        conn.commit()

def fetch_weather_data(city, temp_unit='C'):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(url)
    data = response.json()

    # Convert temperature based on user preference
    if temp_unit == 'F':
        data['main']['temp'] = (data['main']['temp'] * 9/5) + 32
        data['main']['temp_max'] = (data['main']['temp_max'] * 9/5) + 32
        data['main']['temp_min'] = (data['main']['temp_min'] * 9/5) + 32
        data['main']['feels_like'] = (data['main']['feels_like'] * 9/5) + 32

    return data

def save_weather_data(data):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO weather (city, temp, feels_like, wind, uv, visibility, humidity, pressure, dt, max_temp, min_temp, condition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data['main']['temp'], data['main']['feels_like'], data['wind']['speed'], None, 
            data['visibility'], data['main']['humidity'], data['main']['pressure'], 
            time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(data['dt'])),
            data['main'].get('temp_max', None), data['main'].get('temp_min', None),
            data['weather'][0]['main']
        ))
        conn.commit()


def check_thresholds(city, temp):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT temp_threshold, consecutive_count FROM thresholds WHERE city = ?', (city,))
        threshold_data = c.fetchone()

        if threshold_data:
            temp_threshold, consecutive_count = threshold_data
            c.execute('''
                SELECT temp FROM weather WHERE city = ? ORDER BY dt DESC LIMIT ?
            ''', (city, consecutive_count))
            recent_temps = c.fetchall()

            if all(float(recent_temp[0]) > temp_threshold for recent_temp in recent_temps):
                return True  # Threshold exceeded
    return False

def save_daily_weather_summary(city, date, avg_temp, max_temp, min_temp, total_precipitation, avg_wind_speed, predominant_condition):
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO daily_weather_summary (city, date, avg_temp, max_temp, min_temp, total_precipitation, avg_wind_speed, predominant_condition)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (city, date, avg_temp, max_temp, min_temp, total_precipitation, avg_wind_speed, predominant_condition))
            conn.commit()
            print(f"Successfully saved daily summary for {city} on {date}.")  # Debugging line
    except sqlite3.Error as e:
        print(f"Error saving daily summary for {city} on {date}: {e}")  # Print the error

def check_and_alert():
    while True:
        for city in METRO_CITIES:
            weather_data = fetch_weather_data(city)
            print(f"Fetched weather data for {city}: {weather_data}")  # Debugging line
            current_temp = weather_data['main']['temp']
            save_weather_data(weather_data)

            # Check thresholds and send alerts if necessary
            if check_thresholds(city, current_temp):
                print(f"ALERT: Temperature in {city} exceeded the threshold! Current temp: {current_temp}°C")
                send_email_alert(city, current_temp)  # Optional: Send email alert

            # Calculate daily averages and save to daily_weather_summary
            date = time.strftime('%Y-%m-%d', time.gmtime(weather_data['dt']))  # Get the date from the weather data
            avg_temp = current_temp  # You may want to calculate this based on multiple entries
            max_temp = weather_data['main']['temp_max']
            min_temp = weather_data['main']['temp_min']
            total_precipitation = 0.0  # You may need to fetch this from your data
            avg_wind_speed = weather_data['wind']['speed']
            predominant_condition = weather_data['weather'][0]['main']

            # Debugging: Print the values before saving
            print(f"Saving daily summary for {city} on {date}: Avg Temp: {avg_temp}, Max Temp: {max_temp}, Min Temp: {min_temp}, Total Precipitation: {total_precipitation}, Avg Wind Speed: {avg_wind_speed}, Condition: {predominant_condition}")

            # Call the function to save daily weather summary
            save_daily_weather_summary(city, date, avg_temp, max_temp, min_temp, total_precipitation, avg_wind_speed, predominant_condition)

        time.sleep(300)  # Poll every 5 minutes

def send_email_alert(city, temp):
    sender_email = "youremail@example.com"
    receiver_email = "user@example.com"  # Set the user email who needs to receive alerts
    password = "your_email_password"

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Weather Alert: {city}"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"The temperature in {city} has exceeded the threshold! Current temperature: {temp}°C"
    part = MIMEText(text, "plain")
    message.attach(part)

    # Send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def save_forecast_data(city, forecast_data):
    """
    Save the 5-day forecast data into the 'forecast' table in the database.
    Each day's data includes date, temperature, weather conditions, humidity, and wind speed.
    """
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        for day in forecast_data:
            # Insert each day's forecast into the forecast table
            c.execute('''
                INSERT INTO forecast (city, date, temp_day, temp_min, temp_max, condition, humidity, wind_speed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                city,
                day['date'],
                day['temp_day'],
                day['temp_min'],
                day['temp_max'],
                day['condition'],
                day['humidity'],
                day['wind_speed']
            ))
        conn.commit()
    print(f"Forecast data for {city} saved successfully.")

@app.route('/')
def home():
    return render_template('test.html')  # Render the HTML template


@app.route('/get_weather', methods=['GET', 'POST'])
def get_weather():
    if request.method == 'GET':
        city = request.args.get('city')  # Use request.args for GET parameters
        temp_unit = request.args.get('temp_unit', 'C')  # Default to Celsius if not provided
        weather_data = fetch_weather_data(city, temp_unit)
        save_weather_data(weather_data)

        # Save search history
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO search_history (city, timestamp) VALUES (?, ?)', (city, time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()

        return jsonify(weather_data)
    else:
        # Handle POST request as before
        city = request.form['city']
        temp_unit = request.form.get('temp_unit', 'C')  # Default to Celsius if not provided
        weather_data = fetch_weather_data(city, temp_unit)
        save_weather_data(weather_data)

        # Save search history
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO search_history (city, timestamp) VALUES (?, ?)', (city, time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()

        return jsonify(weather_data)
    

@app.route('/get_forecast/<city>')
def get_forecast(city):
    try:
        url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch forecast data'}), response.status_code

        data = response.json()
        
        if 'list' not in data:
            return jsonify({'error': 'No forecast data available'}), 404
        
        forecast_data = []
        seen_dates = set()
        
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if date not in seen_dates:
                seen_dates.add(date)
                forecast_data.append({
                    'date': date,
                    'temp_day': item['main']['temp'],
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'condition': item['weather'][0]['main'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed']
                })
            
            if len(forecast_data) >= 5:
                break

        # Save forecast data to the database
        save_forecast_data(city, forecast_data)

        return jsonify({'forecast': forecast_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    city = request.form.get('city')
    temp_threshold_str = request.form.get('temp_threshold')

    if not city or not temp_threshold_str:
        return jsonify({'error': 'City and temperature threshold are required.'}), 400

    try:
        temp_threshold = float(temp_threshold_str)  # Convert to float
    except ValueError:
        return jsonify({'error': 'Invalid temperature threshold. It must be a number.'}), 400

    consecutive_count = 2  # Fixed consecutive updates count

    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO thresholds (city, temp_threshold, consecutive_count) VALUES (?, ?, ?)', 
                       (city, temp_threshold, consecutive_count))
            conn.commit()
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {e}'}), 500

    return jsonify({'message': f'Threshold set for {city} at {temp_threshold}°C.'})

@app.route('/delete_history', methods=['POST'])
def delete_history():
    city = request.form['city']
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM weather WHERE city = ?', (city,))
        c.execute('DELETE FROM search_history WHERE city = ?', (city,))
        conn.commit()
    return jsonify({'status': 'success', 'message': f'History for {city} deleted'})

@app.route('/search_history', methods=['GET'])
def search_history():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT city, timestamp FROM search_history ORDER BY id DESC LIMIT 10')
        history = c.fetchall()
    return jsonify(history)
@app.route('/recent_searches', methods=['GET'])
def recent_searches():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        query = '''
            SELECT city, temp, max_temp, min_temp, condition, wind, visibility, humidity, pressure
            FROM weather
            WHERE city IN ({})
            AND dt = (SELECT MAX(dt) FROM weather WHERE city = weather.city)
        '''.format(', '.join('?' for _ in METRO_CITIES))
        
        c.execute(query, METRO_CITIES)
        recent_searches = c.fetchall()
    
    return jsonify([
        {
            'city': row[0],
            'temp': row[1],
            'max_temp': row[2],
            'min_temp': row[3],
            'condition': row[4],
            'wind': row[5],
            'visibility': row[6],
            'humidity': row[7],
            'pressure': row[8]
        } for row in recent_searches
    ])

@app.route('/daily_summary', methods=['GET'])
def daily_summary():
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM daily_weather_summary')
            daily_summaries = c.fetchall()

        daily_summaries_json = []
        for summary in daily_summaries:
            daily_summaries_json.append({
                'city': summary[1],
                'date': summary[2],
                'avg_temp': summary[3],
                'max_temp': summary[4],
                'min_temp': summary[5],
                'total_precipitation': summary[6],
                'avg_wind_speed': summary[7],
                'predominant_condition': summary[8]
            })

        return jsonify(daily_summaries_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
    
@app.route('/visualize_daily/<city>', methods=['GET'])
def visualize_daily(city):
    visualize_daily_weather(city)
    return jsonify({'message': f'Daily weather summary for {city} visualized.'})

@app.route('/visualize_historical', methods=['GET'])
def visualize_historical():
    visualize_historical_trends()
    return jsonify({'message': 'Historical trends visualized.'})

@app.route('/visualize_alerts', methods=['GET'])
def visualize_alerts():
    # Example alert data; you should replace this with actual data from your application
    alert_data = {
        'Delhi': 5,
        'Mumbai': 3,
        'Bangalore': 2,
    }
    visualize_triggered_alerts(alert_data)
    return jsonify({'message': 'Triggered alerts visualized.'})
if __name__ == '__main__':
    init_db()
    
    # Start the background thread for continuous tracking
    tracker_thread = Thread(target=check_and_alert)
    tracker_thread.daemon = True  # This ensures the thread will exit when the main program exits
    tracker_thread.start()

    app.run(debug=True)
