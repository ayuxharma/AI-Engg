import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import os

# calculate dates
today = datetime.now()
week_ago = today - timedelta(days=7)

# format dates for API request
start_date = week_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

    
url = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude=48.8566&longitude=2.3522"
    f"&start_date={start_date}&end_date={end_date}"
    f"&daily=temperature_2m_max,temperature_2m_min"
    f"&timezone=auto"
)

response = requests.get(url)
data = response.json()
print(data)

#---------------------------------------------------------------
#PANDAS

#extract daily data
daily_data = data['daily']

# create a DataFrame
df = pd.DataFrame({
    'date' : daily_data["time"],
    'max_temp' : daily_data["temperature_2m_max"],
    'min_temp' : daily_data["temperature_2m_min"],
})

# convert data string to datetime
df['date'] = pd.to_datetime(df['date'])

print(df)


#---------------------------------------------------------------------
#VIZUALIZATION

# create the plot
plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['max_temp'], marker='o', label='Max Temp (°C)', color='r')
plt.plot(df['date'], df['min_temp'], marker='o', label='Min Temp (°C)', color='b')

# add title and labels
plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.title('Daily Max and Min Temperatures in Paris (Last 7 Days)')
plt.legend()

# rotate x-axis labels for better readability
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

#---------------------------------------------------------------

if not os.path.exists('data'):
    os.makedirs('data')
    
# save to csv
df.to_csv('data/paris_weather_data.csv', index=False)
print("Data saved to 'data/paris_weather_data.csv'")
