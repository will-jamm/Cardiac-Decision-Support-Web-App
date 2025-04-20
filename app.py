from src.fhir_client import FHIRClient
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src import charts
from src.ascvd_risk_calculator import ASCVDRiskCalculator
from src.forecast import get_patient_name_by_id, forecasting
import os


# import streamlit_authenticator as stauth

st.set_page_config(layout="wide")

JSON_DATABASE = 'data/json_database.json'
fullUrl = "http://tutsgnfhir.com"

class DecisionSupportInterface():
    def __init__(self):
        self.client = self.initialize_client()

    def initialize_client(self):
        return FHIRClient(
            server_url=fullUrl,
            json_path=JSON_DATABASE
        )

    def search_patients(self, query, patient_ids):
    
        if not query:
            return None
        
        query = query.lower()
        
        if not hasattr(self, '_patient_cache') or self._patient_cache is None:
            # Initialize cache
            self._patient_cache = {}
            for patient_id in patient_ids:
                demographics = self.client.get_demographics(patient_id)
                if demographics:
                    self._patient_cache[patient_id] = demographics

        results = []
        for patient_id, demographics in self._patient_cache.items():
            if demographics:
                given, surname, _, _, _ = demographics
                full_name = f"{given} {surname}".lower()
                
                if query in full_name or query in patient_id.lower():
                    results.append(patient_id)
                    
        return results

    def display_patient_information(self, demographics, weight, height, cholesterol_data):

        if len(weight) == 0:
            latest_weight = "No data"
        else:
            latest_weight = weight[-1]['display']
            weight_date = weight[-1]['formatted_date']

        if len(height) == 0:
            latest_height = "No data"
        else:
            latest_height = height[-1]['display']
            height_date = height[-1]['formatted_date']
        
        total_cholesterol = cholesterol_data['total_cholesterol']
        hdl_cholesterol = cholesterol_data['hdl_cholesterol']

        if demographics:
            given, surname, birthdate, age, sex = demographics
            
            st.title(f"{given} {surname}")                

            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True): 
                    st.subheader("Patient Information")
                    st.write(f"**Age:** {age} years")
                    st.write(f"**Sex:** {sex}")
                    st.write(f"**Date of Birth:** {birthdate}")

            with col2:
                with st.container(border=True):
                    st.subheader("Patient Vitals")
                    
                    if latest_height == "No data":
                        st.write(f"**Height:** **{latest_height}**")
                    else:
                        st.write(f"**Height:** **{latest_height}** ({height_date})")
        
                    if latest_weight == "No data":
                        st.write(f"**Weight:** **{latest_weight}**")
                    else:
                        st.write(f"**Weight:** **{latest_weight}** ({weight_date})")

                    st.write(f"**Total cholesterol:** {total_cholesterol} mg/dL")
                    st.write(f"**HDL cholesterol:** {hdl_cholesterol} mg/dL")

    def _create_risk_chart(self, risk_value, risk_categories):

        categories = list(risk_categories.keys())
        thresholds = list(risk_categories.values())
        colors = ['#E3F2FD', '#90CAF9', '#42A5F5', '#1565C0']
        ranges = [0] + thresholds + [100]

        fig = go.Figure()
        
        for i in range(len(colors)):
            fig.add_trace(go.Bar(
                x=[ranges[i+1] - ranges[i]],
                y=[''],
                orientation='h',
                marker=dict(color=colors[i]),
                base=ranges[i],
                showlegend=False,
                hoverinfo='none'
            ))
        
        for i in thresholds:
            fig.add_annotation(
            x=i,
            y=0.5,
            text=f"{i:.1f}%",
            showarrow=False,
            font=dict(size=13, color='black')
        )

        fig.add_annotation(
            x=risk_value,
            y=0.5,
            text=f"{risk_value:.1f}%",
            showarrow=False,
            font=dict(size=13, color='black')
        )
        

        fig.add_trace(go.Scatter(
            x=[risk_value],
            y=[0],
            mode='markers',
            marker=dict(color='black', size=15, symbol='triangle-up'),
            showlegend=False
        ))
        
        for trace in fig.data:
            if isinstance(trace, go.Bar):
                trace.marker.line = dict(color='black', width=2)

        fig.update_layout(
            title=f"10-Year ASCVD Risk:",
            height=350,
            width=800,
            margin=dict(l=50, r=50, t=80, b=80),
            xaxis=dict(
            range=[0, risk_value],
            showgrid=False
            ),
            yaxis=dict(
            showticklabels=True,
            showgrid=False
            ),
            barmode='stack',
            plot_bgcolor='white'
        )
        
        return fig
    
    def display_risk_score(self, demographics, cholesterol_data, systolic_bp, is_treated_bp, is_smoker, has_diabetes):

        if not cholesterol_data or not systolic_bp or not demographics:
            st.info("Not enough data to calculate ASCVD risk.")
            return

        total_chol = cholesterol_data.get("total_cholesterol")
   
        hdl_chol = cholesterol_data.get("hdl_cholesterol")

        if not total_chol or not hdl_chol:
            st.info("Missing cholesterol data for risk calculation.")
            return

        _, _, _, age, sex = demographics

        risk_calc = ASCVDRiskCalculator()
        risk = risk_calc.compute_10_year_risk(
            age=age,
            sex=sex,  
            total_cholesterol=total_chol,
            hdl_cholesterol=hdl_chol,
            systolic_bp=systolic_bp,
            isBpTreated=is_treated_bp,
            isSmoker=is_smoker,
            hasDiabetes=has_diabetes
        )

        risk_categories = {
            "Low Risk": 5.0,
            "Moderate Risk": 7.5,
            "High Risk": 20.0
        }
        
        if isinstance(risk, dict):  # handle validation error
            st.warning(risk['message'])
        else:
            fig = self._create_risk_chart(risk, risk_categories)

            st.plotly_chart(
                fig
            )
            st.write(f"**10-Year ASCVD Risk Score: {risk:.1f}%**")
            

    
    def dashboard(self):
        st.title("CARDICARE Cardiac Health Support Interface")
        with st.sidebar:
            st.text("Sidebar")
        patient_ids = self.client.get_all_patient_ids()

        with st.form(key='search_form'):
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input("Search by patient ID", "")

            with search_col2:
                st.write("")
                st.write("")
                submit_button = st.form_submit_button("Search")
            
            if submit_button:
                st.session_state.search_results = self.search_patients(search_query, patient_ids)

        if 'search_results' in st.session_state:
        
            filtered_patients = st.session_state.search_results
            if filtered_patients:
                for patient_id in filtered_patients:

                    demographics = self.client.get_demographics(patient_id)
                    weight_history = self.client.get_weight_history(patient_id)
                    height_history = self.client.get_height_history(patient_id)
                    bmi_history = self.client.get_bmi_history(patient_id)
                    glucose_history = self.client.get_glucose_history(patient_id)
                    systolic_bp_history = self.client.get_systolic_blood_pressure_history(patient_id)
                    diastolic_bp_history = self.client.get_diastolic_blood_pressure_history(patient_id)
                    hr_history = self.client.get_heart_rate_history(patient_id)

                    total_chol = self.client.get_latest_total_cholesterol(patient_id)
                    hdl_chol = self.client.get_latest_hdl_cholesterol(patient_id)
                    systolic_bp = self.client.get_latest_systolic_bp(patient_id)

                    is_treated_bp = self.client.is_patient_on_bp_medication(patient_id)
                    is_smoker = self.client.is_patient_smoker(patient_id)
                    has_diabetes = self.client.does_patient_have_diabetes(patient_id)

                    cholesterol_data = {
                        "total_cholesterol": total_chol,
                        "hdl_cholesterol": hdl_chol
                    }

                    self.display_patient_information(demographics=demographics, weight=weight_history, height=height_history, cholesterol_data=cholesterol_data)


                    row1_col1, row1_col2 = st.columns(2)

                    with row1_col1:
                        charts.plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics,
                                                      self.client)

                    with row1_col2:
                        charts.plot_blood_glucose_level(glucose_history, self.client)

                    row2_col1, row2_col2 = st.columns(2)

                    with row2_col1:
                        charts.plot_blood_pressure(systolic_bp_history, diastolic_bp_history, demographics,
                                                       self.client)

                    with row2_col2:
                        charts.plot_heart_rate(hr_history, demographics, self.client)

                    st.divider()
                    st.title("ASCVD Risk Assessment")
                    self.display_risk_score(demographics, cholesterol_data, systolic_bp, is_treated_bp, is_smoker,
                                            has_diabetes)

                    import plotly.graph_objects as go

                    # Inside your forecasting block (after ASCVD Risk assessment)
                    st.divider()
                    if patient_id:
                        st.subheader("Forecasting Health Trends")

                        df = pd.read_csv("src/out.csv")

                        # Define the allowed features
                        allowed_features = [
                            "bmi",
                            "weight",
                            "height",
                            "heart_rate",
                            "Systolic blood pressure",
                            "Diastolic blood pressure"
                        ]

                        features_list_from_csv = df["Features"].unique().tolist()
                        filtered_features = [feat for feat in features_list_from_csv if feat in allowed_features]

                        selected_feat = st.selectbox("Select a health feature", filtered_features)
                        duration = st.number_input("Prediction duration (days)", min_value=1, max_value=30, value=5)

                        if st.button("Run Forecast"):
                            # Get unit for selected feature (any row for this patient + feature)
                            filtered_df = df[
                                (df["Features"] == selected_feat) & (df["Name"] == get_patient_name_by_id(patient_id))]
                            unit = filtered_df["Unit"].iloc[0] if not filtered_df.empty else ""

                            result = forecasting(selected_feat, duration, patient_id)

                            if isinstance(result, str):
                                st.warning(result)
                            else:
                                st.success(f"Forecasted {selected_feat} for next {duration} days:")

                                # Create forecast steps
                                steps = list(range(1, duration + 1))

                                # Plot with Plotly
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(x=steps, y=result, mode='lines+markers', name=selected_feat))

                                fig.update_layout(
                                    xaxis_title="Future Time Steps (days)",
                                    yaxis_title=f"{selected_feat} ({unit})",
                                    title=f"Forecast for {selected_feat}"
                                )

                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Please search for a patient to perform forecasting.")

            else:
                st.warning("No matching patients found")

    def main(self):
        self.dashboard()

if __name__ == "__main__":
    app = DecisionSupportInterface()
    app.main()