from flask import Flask, request, render_template, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import csv
from datetime import datetime
import os


app = Flask(__name__)

@app.route('/')
def index():
    # Load saved data
    records = []
    if os.path.exists('saved_data.csv'):
        with open('saved_data.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            records = list(reader)
    return render_template('index.html', records=records)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        category = request.form['category']

        x_values = [float(request.form[f'x{i}']) for i in range(1, 8)]
        y_values = [float(request.form[f'y{i}']) for i in range(1, 8)]

        slope, offset = np.polyfit(x_values, y_values, 1)
        slope = round(slope, 3)
        offset = round(offset, 3)

        # Predict bellow pressure for 3 kN/m tension
        target_tension = 3.0
        try:
            recommended_pressure = round((target_tension - offset) / slope, 3)
        except ZeroDivisionError:
            recommended_pressure = "undefined"

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save data to CSV
        filename = 'saved_data.csv'
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'Category', 'X Values', 'Y Values', 'Slope', 'Offset'])
            writer.writerow([
                timestamp,
                category,
                ','.join(map(str, x_values)),
                ','.join(map(str, y_values)),
                slope,
                offset
            ])
        
        

        img = generate_plot(x_values, y_values, slope, offset)

        return render_template('result.html', slope=slope, offset=offset, plot_img=img,
                       recommended_pressure=recommended_pressure)

    except Exception as e:
        return str(e)



#route to history page
@app.route('/history')
def history():
    records = []
    if os.path.exists('saved_data.csv'):
        with open('saved_data.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            records = list(reader)
    return render_template('history.html', records=records)



def generate_plot(x_values, y_values, slope, offset):
    # Create a plot with x and y values
    plt.figure(figsize=(6, 4))
    plt.scatter(x_values, y_values, color='blue', label='Data points')

    # Create a line using the slope and offset (y = slope * x + offset)
    x_line = np.linspace(min(x_values), max(x_values), 100)
    y_line = slope * x_line + offset
    plt.plot(x_line, y_line, color='red', label=f'Fit Line: y = {slope}x + {offset}')
    
    # Labels and title
    plt.title('Canvas Tension vs. Pressure Setpoint')
    plt.xlabel('Pressure Setpoint (kPa)')
    plt.ylabel('Canvas Tension (kN/m)')
    plt.legend()

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Encode the plot as base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    # Close the plot to free up memory
    plt.close()

    return img_base64

if __name__ == '__main__':
    app.run(host='0.0.0.0' , debug=True)
