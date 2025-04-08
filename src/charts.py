import matplotlib.pyplot as plt
import streamlit as st
import csv
import os
import matplotlib.lines as mlines
from datetime import datetime

# Open and read the CSV file. Return dictionary containing the data.
def load_bmi_data(file_path):
    bmi_data = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            bmi_data.append(row)
    return bmi_data


def get_bmi_for_age(bmi_data, age):
    # If the age is 19 or older, return the row with age >= 19
    if age >= 19:
        return bmi_data[-1]  # Get the last row for age >= 19
    else:
        for row in bmi_data:
            if int(row['age']) == age:
                return row


def plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics, client):
    birthdate = demographics[2]
    gender = demographics[4]

    weight_dates = []
    weight_values = []
    weight_indices = []
    weight_data_points = []

    height_dates = []
    height_values = []
    height_indices = []
    height_data_points = []

    bmi_dates = []
    bmi_values = []
    bmi_indices = []
    bmi_data_points = []


    if(len(weight_history) >= len(height_history)):

        extract_data = lambda history: ([entry['date'] for entry in history],
                                        [float(entry['display'].split()[0]) for entry in history],
                                        list(range(len(history)))) if history else ([], [], [])

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
                height_data_points.append(idx)
        weight_data_points = weight_indices
        bmi_data_points = bmi_indices
    else:
        extract_data = lambda history: ([entry['date'] for entry in history],
                                        [float(entry['display'].split()[0]) for entry in history],
                                        list(range(len(history)))) if history else ([], [], [])

        height_dates, height_values, height_indices = extract_data(height_history)
        bmi_dates, bmi_values, bmi_indices = extract_data(bmi_history)

        weight_dict = {entry['date']: float(entry['display'].split()[0]) for entry in weight_history}
        weight_data_points = []
        index = 0
        for idx, height_entry in enumerate(height_history):
            date = height_entry['date']
            if date in weight_dict:
                weight_values.append(weight_dict[date])
                weight_dates.append(date)
                weight_indices.append(index)
                index += 1
                weight_data_points.append(idx)
        height_data_points = height_indices

    if gender == "female":
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        female_bmi_path = os.path.join(data_dir, 'female_bmi.csv')
        bmi_ranges_data = load_bmi_data(female_bmi_path)
    else:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        female_bmi_path = os.path.join(data_dir, 'female_bmi.csv')
        bmi_ranges_data = load_bmi_data(female_bmi_path)

    if not bmi_history and weight_history and height_history:
        bmi_data_points = []
        bmi_indices = list(range(len(weight_history)))
        height_dict = {entry['date']: float(entry['display'].split()[0]) for entry in height_history}

        for idx, weight_entry in enumerate(weight_history):
            date = weight_entry['date']
            if date in height_dict:
                weight = float(weight_entry['display'].split()[0])
                height = height_dict[date]
                bmi = weight / ((height / 100) ** 2)
                bmi_values.append(bmi)
                bmi_dates.append(date)
                bmi_data_points.append(idx)

    if weight_dates or height_dates or bmi_dates:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax2 = ax1.twinx()
        ax2.plot(bmi_data_points, bmi_values, 'o-', color='black', markerfacecolor='white', linewidth=1.5, label="BMI", markersize=8, markeredgewidth=2)

        # Add background color for BMI ranges
        for i in range(len(bmi_indices) - 1):
            x_start = bmi_indices[i]
            x_end = bmi_indices[i + 1]
            if(x_end < len(bmi_dates)):
                date = bmi_dates[x_end]
                age_at_date = client._calculate_age(birthdate, date)

                # Retrieve BMI ranges for the provided age
                bmi_row = get_bmi_for_age(bmi_ranges_data, age_at_date)
                normal_scaled = (210 / 50) * float(bmi_row['normal'])
                overweight_scaled = (210 / 50) * float(bmi_row['overweight'])
                obese_scaled = (210 / 50) * float(bmi_row['obese'])

                normal = float(bmi_row['normal'])
                overweight = float(bmi_row['overweight'])
                obese = float(bmi_row['obese'])
                xmin = x_start / (len(bmi_data_points)-2)
                xmax = x_end / (len(bmi_data_points)-2)

                for (start, end, color) in [
                    (0, normal_scaled, '#DAE8FC'),
                    (normal_scaled, overweight_scaled, '#D5E8D4'),
                    (overweight_scaled, obese_scaled, '#FFF2CC'),
                    (obese_scaled, 210, '#F8CECC')
                ]:
                    ax1.axhspan(start, end, xmin=xmin, xmax=xmax, color=color, alpha=0.7)
                if i < len(bmi_data_points) - 1:
                    current_bmi_index = bmi_data_points[i]
                else:
                    current_bmi_index = None

                if current_bmi_index is not None:
                    if bmi_values[x_start] < normal:
                        markeredgecolor = '#0000FF'  # Underweight
                    elif normal <= bmi_values[x_start] < overweight:
                        markeredgecolor = '#00CC00'  # Normal
                    elif overweight <= bmi_values[x_start] < obese:
                        markeredgecolor = '#FF8000'  # Overweight
                    else:
                        markeredgecolor = '#FF0000'  # Obese

                    # Plot the BMI points
                    ax2.plot(current_bmi_index, bmi_values[x_start], 'o', color='black', markeredgecolor=markeredgecolor,
                             markerfacecolor='white', markersize=8, markeredgewidth=2)

            last_bmi_index = bmi_data_points[-1]
            last_bmi = bmi_values[len(bmi_values) - 1]
            age_at_last_bmi = client._calculate_age(birthdate, weight_history[len(bmi_values) - 1]['date'])
            bmi_row = get_bmi_for_age(bmi_ranges_data, age_at_last_bmi)
            normal_scaled = float(bmi_row['normal'])
            overweight_scaled = float(bmi_row['overweight'])
            obese_scaled = float(bmi_row['obese'])

            if last_bmi < normal_scaled:
                markeredgecolor = '#0000FF'  # Underweight
            elif normal_scaled <= last_bmi < overweight_scaled:
                markeredgecolor = '#00CC00'  # Normal
            elif overweight_scaled <= last_bmi < obese_scaled:
                markeredgecolor = '#FF8000'  # Overweight
            else:
                markeredgecolor = '#FF0000'  # Obese

            ax2.plot(last_bmi_index, last_bmi, 'o', markeredgecolor=markeredgecolor,
                     markerfacecolor='white', markersize=8, markeredgewidth=2)

        if weight_history:
            ax1.plot(weight_data_points, weight_values, 'o-', linewidth=1.5, color='#1F5E61', label="Weight")
        if height_history:
            ax1.plot(height_data_points, height_values, 'o-', linewidth=1.5, color='#004C99', label="Height")

        legend_elements = [
            mlines.Line2D([], [], color='#004C99', linewidth=1.5, marker='o', label='Height'),
            mlines.Line2D([], [], color='black', marker='o',
                          markerfacecolor='white', markersize=8, markeredgewidth=2, label='BMI'),
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

        ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.1, 1))

        all_dates = sorted(set(weight_dates + height_dates + bmi_dates))
        ax1.set_xticks(range(len(all_dates)))
        ax1.set_xticklabels([date.strftime('%d-%m-%Y') for date in all_dates], rotation=45, ha='right')

        ax1.set_ylabel("Weight (kg) & Height (cm)")
        ax1.set_ylim(0, 210)
        ax1.grid(True, axis='x', linestyle='--', alpha=0.6)
        ax2.set_ylabel(r"BMI (kg/m$^2$)")
        ax2.set_ylim(0, 50)
        ax2.set_yticks(range(0, 55, 5))

        ax1.set_title("Weight, Height & BMI")
        st.pyplot(fig)
    else:
        st.warning("No weight, height, or BMI data available")