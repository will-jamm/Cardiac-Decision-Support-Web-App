import matplotlib.pyplot as plt
import streamlit as st


def plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics, client):
    birthdate = demographics[2]

    extract_data = lambda history: ([entry['formatted_date'] for entry in history],
                                    [float(entry['display'].split()[0]) for entry in history],
                                    list(range(len(history)))) if history else ([], [], [])

    weight_timestamps, weights, weight_indices = extract_data(weight_history)
    height_timestamps, heights, height_indices = extract_data(height_history)
    bmi_timestamps, bmis, bmi_indices = extract_data(bmi_history)

    # Calculate BMI if it's not available but weight and height exist
    if not bmi_history and weight_history and height_history:
        bmis = [w / ((h / 100) ** 2) for w, h in zip(weights, heights)]
        bmi_timestamps, bmi_indices = weight_timestamps, list(range(len(bmis)))

    if bmis:
        first_bmi_date, last_bmi_date = bmi_history[0]['date'] if bmi_history else weight_history[0]['date'], \
        bmi_history[-1]['date'] if bmi_history else weight_history[-1]['date']
        age_at_first_bmi, age_at_last_bmi = client._calculate_age(birthdate, first_bmi_date), client._calculate_age(
            birthdate, last_bmi_date)
        st.write(f"Age at First BMI Measurement: {age_at_first_bmi} years")
        st.write(f"Age at Last BMI Measurement: {age_at_last_bmi} years")

    if weight_timestamps or height_timestamps or bmi_timestamps:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax2 = ax1.twinx()

        # Add background color for BMI ranges
        for y, color in zip([77.7, 105, 126], ['#006332', '#D6B656', '#B85450']):
            ax1.axhline(y=y, color=color, linestyle='-', linewidth=1)

        for (start, end, color) in [(0, 77.7, '#DAE8FC'), (77.7, 105, '#D5E8D4'), (105, 126, '#FFF2CC'),
                                    (126, 210, '#F8CECC')]:
            ax1.axhspan(start, end, color=color, alpha=0.7)

        if weight_history:
            ax1.plot(weight_indices, weights, 'ko-', label="Weight")
        if height_history:
            ax1.plot(height_indices, heights, 'o-', color='#004C99', label="Height")
        if bmis:
            ax2.plot(bmi_indices, bmis, 'o-', color='#A75400', label="BMI")

        all_timestamps = sorted(set(weight_timestamps + height_timestamps + bmi_timestamps))
        ax1.set_xticks(range(len(all_timestamps)))
        ax1.set_xticklabels(all_timestamps, rotation=45, ha='right')

        ax1.set_ylabel("Weight (kg) & Height (cm)")
        ax1.set_ylim(0, 210)
        ax1.grid(True, axis='x', linestyle='--', alpha=0.6)
        ax2.set_ylabel(r"BMI (kg/m$^2$)")
        ax2.set_ylim(0, 50)
        ax2.set_yticks(range(0, 55, 5))

        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")
        ax1.set_title("Weight, Height & BMI")
        st.pyplot(fig)
    else:
        st.warning("No weight, height, or BMI data available")
