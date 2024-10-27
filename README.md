# Weather Tracker Application
## Overview
The Weather Tracker Application is a Flask-based web application that fetches real-time weather data for various metro cities in India. It allows users to view current weather conditions, set temperature thresholds for alerts, and visualize historical weather trends. The application uses OpenWeatherMap API to retrieve weather data and SQLite for data storage.

## Features

-Current Weather Data: Fetch and display current weather data for selected cities.
-Temperature Thresholds: Set temperature thresholds and receive alerts via email.
-Forecast Data: Retrieve and display a 5-day weather forecast.
-Daily Weather Summary: Store and visualize daily weather summaries.
-Search History: Keep track of recent searches.
-Visualizations: Generate visualizations for daily summaries, historical trends, and triggered alerts.

## Design Choices
-Flask Framework: Chosen for its simplicity and flexibility in building web applications.
-SQLite Database: Lightweight and serverless database that is easy to integrate and manage for small-scale applications.
-OpenWeatherMap API: Provides reliable weather data which is essential for the application.
-Background Thread: Used for continuously checking weather conditions and sending alerts without blocking the main application.
-Responsive UI: Designed with a focus on user experience, ensuring the application is accessible on different devices.
## Dependencies
To run this application, you need to have the following dependencies installed:
```sh
Python 3.x
Flask
Requests
SQLite3
Matplotlib (for visualizations)
Pandas (for data manipulation)
```

## Installation
### Clone the Repository:

```sh
git clone https://github.com/yourusername/weather-tracker.git
cd weather-tracker
```

## Create a Virtual Environment (optional but recommended):

```sh
python -m venv venv
source venv/bin/activate  
# On Windows 
use `venv\Scripts\activate`
```

## Install Dependencies:

`pip install Flask==2.0.2 requests==2.26.0 pandas matplotlib`

## Set Up Database:

The application will automatically create the SQLite database (weather_data.db) when it runs for the first time.

-Configure Email Alerts: Update the send_email_alert function with your email credentials to enable email notifications for temperature alerts.

## Run the Application:

```sh
python app.py
```
The application will be available at http://127.0.0.1:5000/.

## Running with Docker
To run the application using Docker, you can create a Dockerfile and docker-compose.yml file.

## Use the official Python image from the Docker Hub
`FROM python:3.9-slim`

## Set the working directory
`WORKDIR /app`

## Copy the requirements file
`COPY requirements.txt .`

## Install dependencies
`RUN pip install --no-cache-dir -r requirements.txt`

## Copy the application code
`COPY . .`

## Expose the port
`EXPOSE 5000`

## Command to run the application
`CMD ["python", "app.py"]`

# docker-compose.yml
```sh
version: '3.8'
```
services:
  weather-tracker:
    build: .
    ports:
      - "5000:5000"
    environment:
      - API_KEY=your_openweathermap_api_key

	  
## Build and Run with Docker

### 1. Build the Docker Image:

`docker-compose build`

### 2. Run the Docker Container:

```docker-compose up```

## Usage
-Homepage: Access the homepage to search for weather data by city.
-Set Threshold: Enter a city and temperature threshold to receive alerts.
-Visualizations: Click buttons to visualize daily summaries, historical trends, and triggered alerts.
-Recent Searches: View the recent search history for quick access to previously searched cities.

## Contributing
Please feel free to fork the repository and submit a pull request if you'd like to contribute to this project. Any contributions, bug fixes, or feature requests are welcome!
