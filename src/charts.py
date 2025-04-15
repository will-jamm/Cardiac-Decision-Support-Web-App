import matplotlib.pyplot as plt
import streamlit as st
import csv
import os
import matplotlib.lines as mlines
import matplotlib.font_manager as fm
import numpy as np

# Open and read the CSV file. Return dictionary containing the data.
def load_data(file_path):
    bmi_data = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            bmi_data.append(row)
    return bmi_data


def get_bmi_ranges(data, age):
    # If the age is 19 or older, return the row with age >= 19
    if age >= 19:
        return data[-1]  # Get the last row for age >= 19
    else:
        for row in data:
            if int(row['age']) == age:
                return row


def plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics, client):
    birthdate = demographics[2]
    gender = demographics[4]

    weight_dates = []
    weight_values = []
    weight_indices = []
    x_centers_weight = []

    height_dates = []
    height_values = []
    height_indices = []
    x_centers_height = []

    bmi_dates = []
    bmi_values = []
    bmi_indices = []
    x_centers_bmi = []

    # Extract data from database
    if(len(weight_history) >= len(height_history)):

        extract_data = lambda history: ([entry['date'] for entry in history],
                                        [float(entry['display'].split()[0]) for entry in history],
                                        np.linspace(0, 1, len(history))) if history else ([], [], [])

        weight_dates, weight_values, weight_indices = extract_data(weight_history)
        bmi_dates, bmi_values, bmi_indices = extract_data(bmi_history)

        height_dict = {entry['date']: float(entry['display'].split()[0]) for entry in height_history}
        index = 0
        for idx, weight_entry in enumerate(weight_history):
            date = weight_entry['date']
            if date in height_dict:
                height_values.append(height_dict[date])
                height_dates.append(date)
                height_indices.append(index)
                index += 1
        height_indices = np.linspace(0, 1, len(height_indices))
    else:
        extract_data = lambda history: ([entry['date'] for entry in history],
                                        [float(entry['display'].split()[0]) for entry in history],
                                        np.linspace(0, 1, len(history))) if history else ([], [], [])

        height_dates, height_values, height_indices = extract_data(height_history)
        bmi_dates, bmi_values, bmi_indices = extract_data(bmi_history)

        weight_dict = {entry['date']: float(entry['display'].split()[0]) for entry in weight_history}
        index = 0
        for idx, height_entry in enumerate(height_history):
            date = height_entry['date']
            if date in weight_dict:
                weight_values.append(weight_dict[date])
                weight_dates.append(date)
                weight_indices.append(index)
                index += 1

    # Load csv files containing the data for bmi ranges
    if gender == "female":
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        female_bmi_path = os.path.join(data_dir, 'female_bmi.csv')
        bmi_ranges_data = load_data(female_bmi_path)
    else:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        female_bmi_path = os.path.join(data_dir, 'female_bmi.csv')
        bmi_ranges_data = load_data(female_bmi_path)

    # Calculate BMI if it is not in the database and weight and height are
    if not bmi_history and weight_history and height_history:
        weight_dict = {entry['date']: float(entry['display'].split()[0]) for entry in weight_history}
        height_dict = {entry['date']: float(entry['display'].split()[0]) for entry in height_history}

        # Find common dates between weight and height histories
        common_dates = sorted(set(weight_dict.keys()) & set(height_dict.keys()))

        for date in common_dates:
            weight = weight_dict[date]
            height = height_dict[date]
            bmi = weight / ((height / 100) ** 2)  # BMI formula
            bmi_values.append(bmi)
            bmi_dates.append(date)

        bmi_indices = np.linspace(0, 1, len(bmi_values)) # Normalize

    if weight_dates or height_dates or bmi_dates:
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Compute x-coordinates for weight data points
        for i in range(len(weight_indices)):
            x_start = weight_indices[i]
            x_end = weight_indices[i] + 1 / len(weight_indices) if i == len(weight_indices) - 1 else weight_indices[
                i + 1]
            x_center = (x_start + x_end) / 2
            x_centers_weight.append(x_center)

        # Align height data points with corresponding weight dates
        for i in range(len(height_dates)):
            for j in range(len(weight_dates)):
                if(weight_dates[j] == height_dates[i]):
                    x_centers_height.append(x_centers_weight[j])

        # Align BMI data points with corresponding weight dates
        for i in range(len(bmi_dates)):
            for j in range(len(weight_dates)):
                if (weight_dates[j] == bmi_dates[i]):
                    x_centers_bmi.append(x_centers_weight[j])

        # Plot height and weight data
        ax1.plot(x_centers_weight, weight_values, 'o-', linewidth=1.5, color='#1F5E61', label="Weight")
        ax1.plot(x_centers_height, height_values, 'o-', linewidth=1.5, color='#004C99', label="Height")

        # Add background color for BMI ranges
        for i in range(len(bmi_dates)):
            x_start = bmi_indices[i]
            x_end = bmi_indices[i] + 1 / len(bmi_indices) if i == len(bmi_indices) - 1 else bmi_indices[i + 1]
            date = bmi_dates[i]
            age_at_date = client._calculate_age(birthdate, date)

            # Retrieve BMI ranges for the provided age
            bmi_row = get_bmi_ranges(bmi_ranges_data, age_at_date)
            normal_scaled = (210 / 50) * float(bmi_row['normal'])
            overweight_scaled = (210 / 50) * float(bmi_row['overweight'])
            obese_scaled = (210 / 50) * float(bmi_row['obese'])

            # Plot the background colors
            ax1.fill([x_start, x_start, x_end, x_end], [0, normal_scaled, normal_scaled, 0], color='#DAE8FC',
                    alpha=0.7)  # underweight
            ax1.fill([x_start, x_start, x_end, x_end], [normal_scaled, overweight_scaled, overweight_scaled,
                    normal_scaled], color='#D5E8D4', alpha=0.7)  # normal
            ax1.fill([x_start, x_start, x_end, x_end], [overweight_scaled, obese_scaled, obese_scaled,
                     overweight_scaled], color='#FFF2CC', alpha=0.7)  # overweight
            ax1.fill([x_start, x_start, x_end, x_end], [obese_scaled, 210, 210, obese_scaled],
                     color='#F8CECC', alpha=0.7)  # obese

        # Plot the connecting line for BMI datapoints
        ax2 = ax1.twinx()
        ax2.plot(x_centers_bmi, bmi_values, '-', linewidth=1.5, color='black', label="BMI")

        for i in range(len(x_centers_bmi)):
            x_center = x_centers_bmi[i]
            bmi_data_point = bmi_values[i]

            date = bmi_dates[i]
            age_at_date = client._calculate_age(birthdate, date)

            # Retrieve BMI ranges for the provided age
            bmi_row = get_bmi_ranges(bmi_ranges_data, age_at_date)
            normal = float(bmi_row['normal'])
            overweight = float(bmi_row['overweight'])
            obese = float(bmi_row['obese'])

            # Plot individual bmi data points with corresponding color coding
            if bmi_data_point < normal:
                markeredgecolor = 'blue'  # Underweight
            elif normal <= bmi_data_point < overweight:
                markeredgecolor = 'green'  # Normal
            elif overweight <= bmi_data_point < obese:
                markeredgecolor = 'orange'  # Overweight
            else:
                markeredgecolor = 'red'  # Obese,

            ax2.plot(x_center, bmi_data_point, 'o', markeredgecolor=markeredgecolor, markerfacecolor='white',
                markersize=8, markeredgewidth=2)

        # Customize labels
        legend_elements = [
            mlines.Line2D([], [], color='#004C99', linewidth=1.5, marker='o', label='Height'),
            mlines.Line2D([], [], color='black', marker='o', markerfacecolor='white', markersize=8,
                          markeredgewidth=2, label='BMI'),
            mlines.Line2D([], [], color='#1F5E61', linewidth=1.5, marker='o', label='Weight'),
            mlines.Line2D([], [], color='black', markeredgecolor='#0000FF', marker='o',
                          markerfacecolor='white', markersize=8, markeredgewidth=2, label='Underweight'),
            mlines.Line2D([], [], color='#DAE8FC', linewidth=10, label='Underweight (Background)'),
            mlines.Line2D([], [], color='black', markeredgecolor='#00CC00', marker='o',
                          markerfacecolor='white', markersize=8, markeredgewidth=2, label='Normal'),
            mlines.Line2D([], [], color='#D5E8D4', linewidth=10, label='Normal (Background)'),
            mlines.Line2D([], [], color='black', markeredgecolor='#FF8000', marker='o',
                          markerfacecolor='white', markersize=8, markeredgewidth=2, label='Overweight'),
            mlines.Line2D([], [], color='#FFF2CC', linewidth=10, label='Overweight (Background)'),
            mlines.Line2D([], [], color='black', markeredgecolor='#FF0000', marker='o',
                          markerfacecolor='white', markersize=8, markeredgewidth=2, label='Obese'),
            mlines.Line2D([], [], color='#F8CECC', linewidth=10, label='Obese (Background)')
        ]

        font_properties = fm.FontProperties(size=12)
        ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.1, 1), prop=font_properties)

        all_dates = sorted(set(weight_dates + height_dates + bmi_dates))
        ax1.set_xticks(x_centers_weight)
        ax1.set_xticklabels([date.strftime('%d-%m-%Y') for date in all_dates], rotation=45, ha='right', fontsize=9)

        ax1.set_ylabel("Weight (kg) & Height (cm)", fontsize=12)
        ax1.set_ylim(0, 210)
        ax1.grid(True, axis='x', linestyle='--', alpha=0.6)
        ax2.set_ylabel(r"BMI (kg/m$^2$)", fontsize=12)
        ax2.set_ylim(0, 50)
        ax2.set_yticks(range(0, 55, 5))

        ax1.set_title("Weight, Height & BMI", fontsize=16, fontweight='bold')
        st.pyplot(fig)
    else:
        st.warning("No weight, height, or BMI data available")
    return

def get_glucose_ranges(data, measurement):
    for row in data:
        if (row['measurement']) == measurement:
            return row

def plot_blood_glucose_level(glucose_history, client):
    if not glucose_history:
        st.warning("No blood glucose data available")
        return

    # Extract dates and glucose values
    dates = [entry['date'] for entry in glucose_history]
    glucose_values = [float(entry['display'].split()[0]) for entry in glucose_history]
    indices = np.linspace(0, 1, len(glucose_history))  # Normalize

    ymin = min(min(glucose_values) - 50, 0)
    ymax = max(max(glucose_values) + 50, 400)

    fig, ax = plt.subplots(figsize=(10, 5))

    # List to store x_center and glucose_values to plot the line later
    x_centers = []
    y_values = []

    # Load glucose range data from CSV
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    file_path = os.path.join(data_dir, 'glucose_ranges.csv')
    glucose_ranges_data = load_data(file_path)

    for i in range(len(indices)):
        x_start = indices[i]
        x_end = indices[i] + 1 / len(indices) if i == len(indices) - 1 else indices[i + 1]

        x_center = (x_start + x_end) / 2 # Calculate the midpoints for plotting

        # Retrieve glucose ranges for the provided measurement
        measurement = glucose_history[i]['measurement']
        row = get_glucose_ranges(glucose_ranges_data, measurement)

        # Determine the prediabetes and diabetes thresholds
        prediabetes = float(row['prediabetes'])
        diabetes = float(row['diabetes'])
        # Plot the background colors
        ax.fill([x_start, x_start, x_end, x_end], [ymin, prediabetes, prediabetes, ymin], color='#D5E8D4',
                alpha=0.7)  # Normal
        ax.fill([x_start, x_start, x_end, x_end], [prediabetes, diabetes, diabetes, prediabetes], color='#FFF2CC',
                alpha=0.7)  # Prediabetic
        ax.fill([x_start, x_start, x_end, x_end], [diabetes, ymax, ymax, diabetes], color='#F8CECC',
                alpha=0.7)  # Diabetic

        # Store x_center and glucose value for later plotting
        x_centers.append(x_center)
        glucose_value = glucose_values[i]
        y_values.append(glucose_value)

    # Plot the blood glucose datapoints
    ax.plot(x_centers, y_values, '-', linewidth=1.5, color='black', label="Blood Glucose Level")

    for i in range(len(indices)):
        x_center = x_centers[i]
        glucose_value = glucose_values[i]
        measurement = glucose_history[i]['measurement']
        row = get_glucose_ranges(glucose_ranges_data, measurement)

        # Determine the prediabetes and diabetes thresholds
        prediabetes = float(row['prediabetes'])
        diabetes = float(row['diabetes'])

        # Assign marker colors based on glucose level category
        if glucose_value < prediabetes:
            markeredgecolor = 'green'  # Normal
        elif prediabetes <= glucose_value < diabetes:
            markeredgecolor = 'orange'  # Prediabetes
        else:
            markeredgecolor = 'red'  # Diabetes

        # Plot individual glucose data points with corresponding color coding
        ax.plot(x_center, glucose_value, 'o', markeredgecolor=markeredgecolor, markerfacecolor='white',
                markersize=8, markeredgewidth=2, label=measurement)

    # Customize legend
    legend_elements = [
        mlines.Line2D([], [], color='black', marker='o', markerfacecolor='white', markersize=8,
                      markeredgewidth=2, label='Blood Glucose Level'),
        mlines.Line2D([], [], color='black', markeredgecolor='green', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Normal'),
        mlines.Line2D([], [], color='#D5E8D4', linewidth=10, label='Normal (Background)'),
        mlines.Line2D([], [], color='black', markeredgecolor='orange', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Prediabetic'),
        mlines.Line2D([], [], color='#FFF2CC', linewidth=10, label='Prediabetic (Background)'),
        mlines.Line2D([], [], color='black', markeredgecolor='red', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Diabetic'),
        mlines.Line2D([], [], color='#F8CECC', linewidth=10, label='Diabetic (Background)')
    ]

    font_properties = fm.FontProperties(size=12)
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.1, 1), prop=font_properties)
    ax.set_xticks(x_centers)
    if (len(glucose_history) > 40):
        rotation = 90
    else:
        rotation = 45
    ax.set_xticklabels([date.strftime('%d-%m-%Y') for date in dates], rotation=rotation, ha='right', fontsize=9)

    ax.set_ylabel("Blood Glucose Level (mg/dL)", fontsize=12)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    ax.set_title("Blood Glucose Levels", fontsize=16, fontweight='bold')

    st.pyplot(fig)

def get_bp_ranges(bp_ranges_data, age):
    age = int(age)
    for row in bp_ranges_data:
        if age <= int(row['age']):
            return row
    return bp_ranges_data[-1] # Return last row if age > 64

def plot_blood_pressure(systolic_history, diastolic_history, demographics, client):
    if not systolic_history or not diastolic_history:
        st.warning("No blood pressure data available")
        return

    # Extract data from database
    birthdate = demographics[2]
    systolic_dict = {entry['date']: float(entry['display'].split()[0]) for entry in systolic_history}
    diastolic_dict = {entry['date']: float(entry['display'].split()[0]) for entry in diastolic_history}
    common_dates = sorted(set(systolic_dict.keys()) & set(diastolic_dict.keys()))

    dates = []
    systolic_values = []
    diastolic_values = []
    x_centers = []

    for date in common_dates:
        dates.append(date)
        systolic_values.append(systolic_dict[date])
        diastolic_values.append(diastolic_dict[date])

    indices = np.linspace(0, 1, len(dates))

    for i in range(len(indices)):
        x_start = indices[i]
        x_end = indices[i] + 1 / len(indices) if i == len(indices) - 1 else indices[
            i + 1]
        x_center = (x_start + x_end) / 2
        x_centers.append(x_center)

    # Load BP ranges from CSV
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    file_path = os.path.join(data_dir, 'bp_ranges.csv')
    bp_ranges_data = load_data(file_path)

    ymin = min(min(diastolic_values) - 50, 40)
    ymax = max(max(systolic_values) + 50, 200)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_facecolor('#D3D3D3')

    # Plot BP points
    ax.plot(x_centers, systolic_values, '-', linewidth=1.5, color='black')
    ax.plot(x_centers, diastolic_values, '-', linewidth=1.5, color='black')

    for i in range(len(dates)):
        x_center = x_centers[i]
        sys_value = systolic_values[i]
        dia_value = diastolic_values[i]

        age = client._calculate_age(birthdate, dates[i])
        row = get_bp_ranges(bp_ranges_data, age)

        sys_low = float(row['systolic low'])
        sys_elevated = float(row['systolic elevated'])

        dia_low = float(row['diastolic low'])
        dia_elevated = float(row['diastolic elevated'])

        # Assign marker colors based on glucose level category
        if sys_value < sys_low:
            markeredgecolor = 'blue'  # Low
        elif sys_low <= sys_value < sys_elevated:
            markeredgecolor = 'green'  # Normal
        else:
            markeredgecolor = 'red'  # Elevated

        # Plot individual systolic bp data points with corresponding color coding
        ax.plot(x_center, sys_value, 'o', markeredgecolor=markeredgecolor, markerfacecolor='white',
                markersize=8, markeredgewidth=2)

        if dia_value < dia_low:
            markeredgecolor = 'blue'  # Low
        elif dia_low <= dia_value < dia_elevated:
            markeredgecolor = 'green'  # Normal
        else:
            markeredgecolor = 'red'  # Elevated

        # Plot individual systolic bp data points with corresponding color coding
        ax.plot(x_center, dia_value, 'o', markeredgecolor=markeredgecolor, markerfacecolor='white',
                markersize=8, markeredgewidth=2)

    # Legend
    legend_elements = [
        mlines.Line2D([], [], color='black', marker='o', label='Systolic (upper)'),
        mlines.Line2D([], [], color='black', marker='o', label='Diastolic (lower)'),
        mlines.Line2D([], [], color='black', markeredgecolor='red', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Elevated'),
        mlines.Line2D([], [], color='black', markeredgecolor='green', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Normal'),
        mlines.Line2D([], [], color='black', markeredgecolor='blue', marker='o',
                      markerfacecolor='white', markersize=8, markeredgewidth=2, label='Low')
    ]
    font_properties = fm.FontProperties(size=12)
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.1, 1), prop=font_properties)

    ax.set_xticks(x_centers)
    ax.set_xticklabels([date.strftime('%d-%m-%Y') for date in dates], rotation=45, ha='right', fontsize=9)
    ax.set_ylabel("Blood Pressure (mmHg)", fontsize=12)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    ax.set_title("Blood Pressure Levels", fontsize=16, fontweight='bold')

    st.pyplot(fig)

def plot_heart_rate(hr_history, client):
    return