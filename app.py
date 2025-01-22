from src.fhir_client import FHIRClient
import streamlit as st
JSON_DATABASE = 'data/json_database.json'
fullUrl = "http://tutsgnfhir.com"

class DecisionSupportInterface():
    def __init__(self):
        self.client = FHIRClient(
            server_url = fullUrl,
            json_path = JSON_DATABASE
        )

    def search_patients(self, query):
        if not query:
            return self.client.get_all_patient_ids()
        
        results = []  
        for patient_id in self.client.get_all_patient_ids():
            demographics = self.client.get_demographics(patient_id)
            if demographics:
                given, surname, _ = demographics
                if (query.lower() in f"{given} {surname}".lower() or
                    query.lower() in patient_id.lower()):
                    results.append(patient_id)
        return results

    def dashboard(self):
        st.title("Decision Support Interface")
        st.write("The interface is divided into two main sections: the patient information section and the decision support section.")
        
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search by name or ID", "")
        with search_col2:
            st.write("")
            st.write("")
            if st.button("Search"):
                st.session_state.search_results = self.search_patients(search_query)
        
        if 'search_results' in st.session_state:
            filtered_patients = st.session_state.search_results
            if filtered_patients:
                for patient_id in filtered_patients:
                    demographics = self.client.get_demographics(patient_id)
                    if demographics:
                        given, surname, age = demographics
                        st.write(f"Patient: {given} {surname}")
                        st.write(f"Age: {age}")
            else:
                st.warning("No matching patients found")
    def main(self):
        self.dashboard()

if __name__ == "__main__":
    app = DecisionSupportInterface()
    app.main()