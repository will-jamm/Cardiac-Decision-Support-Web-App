import json
from datetime import date, datetime

class FHIRClient(object):
    def __init__(self, server_url, json_path):
        self.server_url = server_url
        self.json_path = json_path
        self.patient_data = self._load_json_data()
        self.patient_ids = self._get_patient_ids()

    def _load_json_data(self):
        try:
            with open(self.json_path, 'rb') as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            raise FileNotFoundError("JSON database not found. Check the file path.")

    def _get_patient_ids(self):
        id_list = []
        for patient in self.patient_data:
            if patient[0]['resource']['resourceType'] == 'Patient':
                id = patient[0]['resource']['id']
            id_list.append(id)
        return id_list
    
    def get_all_patient_data(self, patient_id):
        request_url = f"{self.server_url}/Patient/{patient_id}"
        for patient in self.patient_data:
            if patient[0]['fullUrl'] == request_url:
                return patient
        return None
    
    def get_demographics(self, patient_id):
        request_url = f"{self.server_url}/Patient/{patient_id}"
        for patient in self.patient_data:
            if patient[0]['fullUrl'] == request_url:
                resource_patient = patient[0]['resource']
                given = resource_patient['name'][0]['given'][0]
                surname = resource_patient['name'][0]['family'][0]
                born = datetime.strptime(resource_patient['birthDate'], '%Y-%m-%d')
                age = self._calculate_age(born)
                return given, surname, age
        return None

    def _calculate_age(self, born):
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    def get_all_patient_ids(self):
        """Return list of all patient IDs"""
        return self.patient_ids
    
    def get_resources(self, patient_id):
        patient_data = self.get_all_patient_data(patient_id)
        
        if patient_data:
            return[resource['resource']['resourceType'] for resource in patient_data]
        return None
            