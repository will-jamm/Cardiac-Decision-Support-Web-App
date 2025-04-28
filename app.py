from functools import lru_cache
import time
from src.fhir_client import FHIRClient
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src import charts
from src.ascvd_risk_calculator import ASCVDRiskCalculator
from src.forecast import get_patient_name_by_id, forecasting
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")

JSON_DATABASE = 'data/json_database.json'
fullUrl = "http://tutsgnfhir.com"

class DecisionSupportInterface():
    def __init__(self):
        """Initialize the app with lazy loading"""
        # Initialize client only when needed
        if 'client' not in st.session_state:
            with st.spinner("Initializing system..."):
                st.session_state.client = FHIRClient(
                    server_url=fullUrl,
                    json_path=JSON_DATABASE
                )
    
        self.client = st.session_state.client

    @st.cache_data(ttl=3600)
    def load_patient_data(_client, patient_id):
        """Cache patient data retrieval"""
        return {
            "demographics": _client.get_demographics(patient_id),
            "weight_history": _client.get_weight_history(patient_id),
            "height_history": _client.get_height_history(patient_id),
            "bmi_history": _client.get_bmi_history(patient_id),
            "glucose_history": _client.get_glucose_history(patient_id),
            "systolic_bp_history": _client.get_systolic_blood_pressure_history(patient_id),
            "diastolic_bp_history": _client.get_diastolic_blood_pressure_history(patient_id),
            "hr_history": _client.get_heart_rate_history(patient_id),
            "total_chol": _client.get_latest_total_cholesterol(patient_id),
            "hdl_chol": _client.get_latest_hdl_cholesterol(patient_id),
            "systolic_bp": _client.get_latest_systolic_bp(patient_id),
            "is_treated_bp": _client.is_patient_on_bp_medication(patient_id),
            "is_smoker": _client.is_patient_smoker(patient_id),
            "has_diabetes": _client.does_patient_have_diabetes(patient_id)
        }
    
    @st.cache_data(ttl=3600)
    def get_all_patient_ids(_client):
        """Cache the patient IDs list"""
        return _client.get_all_patient_ids()
    
    @lru_cache(maxsize=32)
    def read_csv_data():
        """Cache CSV reading for forecasting"""
        return pd.read_csv("src/out.csv")
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def build_patient_cache(_client, patient_ids):
        """Build patient cache for searching"""
        patient_cache = {}
        for patient_id in patient_ids:
            demographics = _client.get_demographics(patient_id)
            if demographics:
                patient_cache[patient_id] = demographics
        return patient_cache

    def search_patients(self, query, patient_ids):
    
        if not query:
            return None
        
        query = query.lower()
        
        if not hasattr(self, '_patient_cache') or self._patient_cache is None:

            with st.spinner("Building patient search index..."):
                self._patient_cache = DecisionSupportInterface.build_patient_cache(self.client, patient_ids)

        results = []
        for patient_id, demographics in self._patient_cache.items():
            if demographics:
                given, surname, _, _, _ = demographics
                full_name = f"{given} {surname}".lower()
                
                if query in full_name or query in patient_id.lower():
                    results.append(patient_id)
                    
        return results

    def display_patient_information(self, demographics, weight, height, cholesterol_data, systolic_bp, is_bp_treated, is_smoker, has_diabetes):

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
        
        total_chol = cholesterol_data['total_cholesterol']
        hdl_chol = cholesterol_data['hdl_cholesterol']

        if isinstance(total_chol, dict) and 'value' in total_chol:
            latest_total_chol = total_chol.get('value', "No data")
            total_chol_date = total_chol.get('date', "")
        else:
            latest_total_chol = "No data"
            total_chol_date = ""

        if isinstance(hdl_chol, dict) and 'value' in hdl_chol:
            latest_hdl_chol = hdl_chol.get('value', "No data")
            hdl_chol_date = hdl_chol.get('date', "")
        else:
            latest_hdl_chol = "No data"
            hdl_chol_date = ""

        if isinstance(systolic_bp, dict) and 'value' in systolic_bp:
            latest_systolic_bp = systolic_bp.get('value', "No data")
            systolic_bp_date = systolic_bp.get('date', "")

        elif isinstance(systolic_bp, list) and len(systolic_bp) > 0:

            latest_systolic_bp = systolic_bp[-1].get('value', "No data")
            systolic_bp_date = systolic_bp[-1].get('formatted_date', "")
        else:
            latest_systolic_bp = "No data"
            systolic_bp_date = ""


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
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        if latest_height == "No data":
                            st.write(f"**Height:** {latest_height}")
                        else:
                            st.write(f"**Height:** **{latest_height}** ({height_date})")
            
                        if latest_weight == "No data":
                            st.write(f"**Weight:** {latest_weight}")
                        else:
                            st.write(f"**Weight:** **{latest_weight}** ({weight_date})")

                        if latest_total_chol== "No data":
                            st.write(f"**Total cholesterol:** {latest_total_chol}")
                        else:
                            st.write(f"**Total cholesterol:** **{latest_total_chol} mg/dL** ({total_chol_date})")
                        
                        if latest_hdl_chol == "No data":
                            st.write(f"**HDL cholesterol:** {latest_hdl_chol}")
                        else:
                            st.write(f"**HDL cholesterol:** **{latest_hdl_chol} mg/dL**  ({hdl_chol_date})")
                    
                    with col4:
                        if latest_systolic_bp == "No data":
                            st.write(f"**Systolic BP:** {latest_systolic_bp}")
                        else:
                            st.write(f"**Systolic BP:** **{latest_systolic_bp} mmHg**  ({systolic_bp_date})")

    
    def _create_risk_chart(self, risk_value):

        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Risk Score'],
            y=[risk_value],
            
            width=0.6,
            marker=dict(                  
                color='#FF8C00',
                opacity=0.8,              
                line=dict(                 
                    color='black',      
                    width=1.5             
                ),
                pattern=dict(              
                    shape="/",         
                    solidity=0.5        
                )
            ),
            name='Patient Risk',
            text=[f"<b>{risk_value:.1f}%</b>"],  # Bold text with 1 decimal place
            textposition='outside',              # Position the text above the bar
            textfont=dict(
                size=16,                         # Larger text
                color='black',                   # Black text color
                family='Arial Black'             # Bold font family
            )
        ))
        

        fig.update_layout(
            title=dict(
            text="<b>Chance of heart attack or stroke</b>",
            font=dict(weight='bold'),
            x=0.5,  
            xanchor='center'  # Anchor point for centering
            ),
            yaxis=dict(
            title=dict(text="<b>Risk (%)</b>", font=dict(weight='bold')),
            range=[0, 100]
            ),
            xaxis=dict(
            showticklabels=False
            ),
            height=370,
            width=300,
            margin=dict(l=20, r=20, t=40, b=40),  # Increased bottom margin
            showlegend=False
        )

        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.5,  
            y=-0.15,
            text="<b>10-Year Risk</b>",
            showarrow=False,
            font=dict(
                size=14,
                weight='bold'
            )
        )   
        
        return fig
    
    def display_risk_score(self, demographics, cholesterol_data, systolic_bp, is_treated_bp, is_smoker, has_diabetes):

        risk_cache_key = f"risk_{demographics[0]}_{demographics[1]}"

        if risk_cache_key not in st.session_state:

            if not demographics:
                st.session_state[risk_cache_key] = {"status": "insufficient_data"}
                return

            total_chol_data = cholesterol_data.get('total_cholesterol')
            hdl_chol_data = cholesterol_data.get('hdl_cholesterol')
            
            if not total_chol_data or not hdl_chol_data:
                st.info("Missing cholesterol data for risk calculation.")
                return
                
            if not isinstance(total_chol_data, dict) or 'value' not in total_chol_data or not total_chol_data['value']:
                st.info("Missing cholesterol data for risk calculation.")
                return
                
            if not isinstance(hdl_chol_data, dict) or 'value' not in hdl_chol_data or not hdl_chol_data['value']:
                st.info("Missing cholesterol data for risk calculation.")
                return
                
            if not systolic_bp or not isinstance(systolic_bp, dict) or 'value' not in systolic_bp:
                st.info("Missing systolic BP data for risk calculation.")
                return
                
            total_chol = total_chol_data['value']
            hdl_chol = hdl_chol_data['value']
            systolic_bp_value = systolic_bp['value']

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
            
            if isinstance(risk, dict):
                st.session_state[risk_cache_key] = {
                    "status": "error",
                    "message": risk['message']
                }

            else:
                st.session_state[risk_cache_key] = {
                    "status": "success",
                    "risk": risk,
                    "categories": risk_categories,
                    "fig": self._create_risk_chart(risk),
                    "parameters": {
                        "Total Cholesterol": f"{total_chol} mg/dL",
                        "HDL Cholesterol": f"{hdl_chol} mg/dL",
                        "Systolic BP": f"{systolic_bp} mmHg",
                        "On BP Medication": "Yes" if is_treated_bp else "No",
                        "Current Smoker": "Yes" if is_smoker else "No", 
                        "Diabetes": "Yes" if has_diabetes else "No"
                    }
                }

        cached_result = st.session_state[risk_cache_key]

        if cached_result["status"] == "insufficient_data":
            st.info("Not enough data to calculate ASCVD risk.")
        elif cached_result["status"] == "missing_cholesterol":
            st.info("Missing cholesterol data for risk calculation.")
        elif cached_result["status"] == "error":
            st.warning(cached_result["message"])
        else:
            left_col, right_col = st.columns([1, 1])

            with left_col:
                st.plotly_chart(cached_result["fig"], use_container_width=True)
            
            with right_col:
            # Display risk calculation parameters
                with st.container(border=True):
                    st.subheader("Risk Calculation Parameters")
                    
                    for param, value in cached_result["parameters"].items():
                        st.markdown(f"**{param}:** {value}")
                    
                    # Add risk interpretation based on score
                    risk_score = cached_result["risk"]
                    st.markdown("---")
                    st.markdown("### 10-Year Risk Interpretation")
                    
                    if risk_score < 5.0:
                        st.markdown("**Low risk: < 5%**")
                        st.markdown("• Consider lifestyle modifications")
                    elif risk_score < 7.5:
                        st.markdown("**Borderline risk: 5-7.5%**")
                        st.markdown("• Consider moderate intensity statin")
                        st.markdown("• Emphasize lifestyle modifications")
                    elif risk_score < 20.0:
                        st.markdown("**Intermediate risk: 7.5-20%**")
                        st.markdown("• Moderate intensity statin recommended")
                        st.markdown("• Consider BP management if elevated")
                    else:
                        st.markdown("**High risk: > 20%**")
                        st.markdown("• High intensity statin strongly recommended")
                        st.markdown("• Aggressive management of all risk factors")
                        st.markdown("• Consider aspirin for select patients")
            
    def _display_patient_dashboard(self, patient_id):
        cache_key = f"patient_{patient_id}"
        if cache_key not in st.session_state.get('loaded_patients', {}):
            with st.spinner(f"Loading data for patient {patient_id}..."):
                st.session_state.loaded_patients = st.session_state.get('loaded_patients', {})
                st.session_state.loaded_patients[cache_key] = DecisionSupportInterface.load_patient_data(self.client, patient_id)

        patient_data = st.session_state.loaded_patients[cache_key]

        # Extract data from the cache
        demographics = patient_data["demographics"]
        weight_history = patient_data["weight_history"]
        height_history = patient_data["height_history"]
        bmi_history = patient_data["bmi_history"]
        glucose_history = patient_data["glucose_history"]
        systolic_bp_history = patient_data["systolic_bp_history"]
        diastolic_bp_history = patient_data["diastolic_bp_history"]
        hr_history = patient_data["hr_history"]
        is_bp_treated = patient_data["is_treated_bp"], 
        is_smoker = patient_data["is_smoker"], 
        has_diabetes = patient_data["has_diabetes"]

        cholesterol_data = {
            "total_cholesterol": patient_data["total_chol"],
            "hdl_cholesterol": patient_data["hdl_chol"]
        }

        self.display_patient_information(
            demographics, 
            weight_history, 
            height_history, 
            cholesterol_data,
            systolic_bp_history,
            is_bp_treated,
            is_smoker,
            has_diabetes
        )

        with st.expander("Health Trends", expanded=True):
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                charts.plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics, self.client)
            with row1_col2:
                charts.plot_blood_glucose_level(glucose_history, self.client)
        
            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                charts.plot_blood_pressure(systolic_bp_history, diastolic_bp_history, demographics, self.client)
            with row2_col2:
                charts.plot_heart_rate(hr_history, demographics, self.client)

        with st.expander("### ASCVD Risk Assessment", expanded=True):
            
            self.display_risk_score(
                demographics, 
                cholesterol_data, 
                patient_data["systolic_bp"], 
                patient_data["is_treated_bp"], 
                patient_data["is_smoker"], 
                patient_data["has_diabetes"]
            )

        with st.expander("Health Forecasting", expanded=True):
            self._display_forecasting(patient_id)

    def _display_forecasting(self, patient_id):
        st.markdown("### Forecasting Health Trends")

        df = pd.read_csv("src/out.csv")
    
        allowed_features = [
            "bmi",
            "weight",
            "heart_rate",
            "Systolic blood pressure", 
            "Diastolic blood pressure"
        ]

        features_list_from_csv = df["Features"].unique().tolist()
        filtered_features = [feat for feat in features_list_from_csv if feat in allowed_features]
        
        # Use columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_feat = st.selectbox("Select a health feature", filtered_features)
        with col2:
            duration = st.number_input("Prediction days", min_value=1, max_value=30, value=5)
        
        # Add loading state
        forecast_placeholder = st.empty()


        if st.button("Run Forecast", key=f"forecast_{patient_id}"):
            with forecast_placeholder.container():
                with st.spinner("Calculating forecast..."):
                    # Get unit for selected feature
                    filtered_df = df[(df["Features"] == selected_feat) & 
                                (df["Name"] == get_patient_name_by_id(patient_id))]
                    unit = filtered_df["Unit"].iloc[0] if not filtered_df.empty else ""
                    
                    result = forecasting(selected_feat, duration, patient_id)
                    
                    if isinstance(result, str):
                        st.warning(result)
                    else:
                        st.success(f"Forecasted {selected_feat} for next {duration} days")
                        
                        # Create forecast steps
                        steps = list(range(1, duration + 1))
                        
                        # Plot with Plotly
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=steps, 
                            y=result, 
                            mode='lines+markers',
                            name=selected_feat,
                            line=dict(color='royalblue', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig.update_layout(
                            xaxis_title="Future Time Steps (days)",
                            yaxis_title=f"{selected_feat} ({unit})",
                            title=f"Forecast for {selected_feat}",
                            height=400,
                            margin=dict(l=0, r=0, t=40, b=0),
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)

    def dashboard(self):
        st.title("CARDICARE Cardiac Health Support Interface")

        if 'patient_ids' not in st.session_state:
            st.session_state.patient_ids = self.client.get_all_patient_ids()
            
        with st.sidebar:
            st.text("")

        with st.form(key='search_form'):
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input("Search by patient ID", "")

            with search_col2:
                st.write("")
                st.write("")
                submit_button = st.form_submit_button("Search")
            
            if submit_button:
                with st.spinner("Searching..."):
                    st.session_state.search_results = self.search_patients(search_query, st.session_state.patient_ids)
                    st.session_state.loaded_patients = {}  # Reset loaded patients cache
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            filtered_patients = st.session_state.search_results
        
    
            if len(filtered_patients) > 1:
                patient_tabs = st.tabs([f"Patient {i+1}" for i in range(len(filtered_patients))])
                
                for i, patient_id in enumerate(filtered_patients):
                    with patient_tabs[min(i, len(patient_tabs)-1)]:
                        self._display_patient_dashboard(patient_id)
            else:
                self._display_patient_dashboard(filtered_patients[0])

        elif 'search_results' in st.session_state:
            st.warning("No matching patients found")

    def main(self):
        
        self.dashboard()

if __name__ == "__main__":
    app = DecisionSupportInterface()
    app.main()