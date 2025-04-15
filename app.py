from src.fhir_client import FHIRClient
import streamlit as st
from src import charts
from src.ascvd_risk_calculator import ASCVDRiskCalculator

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

    def display_patient_information(self, demographics, weight, height):

        if len(weight) == 0:
            latest_weight = "No data"
        else:
            latest_weight = weight[-1]['display']

        if len(height) == 0:
            latest_height = "No data"
        else:
            latest_height = height[-1]['display']

        if demographics:
            given, surname, _, age, _ = demographics
            st.write(f"Patient: {given} {surname}")
            st.write(f"Age: {age}")
            st.write(f"Height: {latest_height}")
            st.write(f"Weight: {latest_weight}")


    def display_risk_score(self, demographics, cholesterol_data, systolic_bp, is_treated_bp, is_smoker, has_diabetes):
        if not cholesterol_data or not systolic_bp or not demographics:
            st.info("Not enough data to calculate ASCVD risk.")
            return

        total_chol = cholesterol_data.get("total_cholesterol")
        hdl_chol = cholesterol_data.get("hdl_cholesterol")

        if not total_chol or not hdl_chol:
            st.info("Missing cholesterol data for risk calculation.")
            return

        given, surname, _, age, _ = demographics

        risk_calc = ASCVDRiskCalculator()
        risk = risk_calc.compute_10_year_risk(
            age=age,
            sex='male',  # 🔄 You can improve this later with actual gender data
            total_cholesterol=total_chol,
            hdl_cholesterol=hdl_chol,
            systolic_bp=systolic_bp,
            isBpTreated=is_treated_bp,
            isSmoker=is_smoker,
            hasDiabetes=has_diabetes
        )

        if isinstance(risk, dict):  # handle validation error
            st.warning(risk['message'])
        else:
            st.success(f"10-Year ASCVD Risk Score: **{risk:.2f}%**")

    
    def dashboard(self):
        st.title("Decision Support Interface")
        st.write("The interface is divided into two main sections: the patient information section and the decision support section.")
        
        patient_ids = self.client.get_all_patient_ids()

        with st.form(key='search_form'):
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input("Search by name or ID", "")
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

                    self.display_patient_information(demographics=demographics, weight=weight_history, height=height_history)

                    row1_col1, row1_col2 = st.columns(2)

                    with row1_col1:
                        charts.plot_weight_height_bmi(weight_history, height_history, bmi_history, demographics, self.client)

                    with row1_col2:
                        charts.plot_blood_glucose_level(glucose_history, self.client)

                    row2_col1, row2_col2 = st.columns(2)
                    with row2_col1:
                        charts.plot_blood_pressure(systolic_bp_history, diastolic_bp_history, demographics, self.client)

                    with row2_col2:
                        charts.plot_heart_rate(hr_history, self.client)

                    # Replace dummy inputs with real observation data
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

                    self.display_risk_score(demographics, cholesterol_data, systolic_bp, is_treated_bp, is_smoker,
                                            has_diabetes)

            else:
                st.warning("No matching patients found")

    def main(self):
        self.dashboard()

if __name__ == "__main__":
    app = DecisionSupportInterface()
    app.main()