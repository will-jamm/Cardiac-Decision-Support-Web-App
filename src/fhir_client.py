import json
from datetime import date, datetime
JSON_DATABASE = 'data/json_database.json'
fullUrl = "http://tutsgnfhir.com"

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
    
    def _get_coding(self, resource):
        """
        Extract the coding information from a FHIR resource.
        
        This method tries to access the 'coding' field within the 'code' element 
        of the resource. If the path exists, returns the coding information, 
        otherwise returns None.
        
        Parameters:
        -----------
        resource : dict
            A FHIR resource represented as a dictionary.
            
        Returns:
        --------
        list or None
            The coding information if available, or None if the path doesn't exist.
        """
        if 'code' in resource and 'coding' in resource['code']:
            return resource['code']['coding']
        return None

    def get_weight_history(self, patient_id):
        """
        Retrieves the weight history for a specified patient.
        This method fetches all observations for the patient and filters for weight measurements,
        identified by LOINC code '3141-9' or by having 'weight' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose weight history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing weight measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric weight value
            - 'unit': unit of measurement (defaults to 'kg')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "70 kg")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        weight_history= []
        patient_data = self.get_all_patient_data(patient_id)
        
        if not patient_data:
            return None
        
        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isWeight = False
                coding_list = self._get_coding(resource)
        
                for coding in coding_list:
                    if coding.get('code') == '3141-9' or 'weight' in coding.get('display', '').lower():
                        isWeight = True
                        break

                if isWeight == True:
                    try:
                        weight_value = resource['valueQuantity'].get('value')
                        weight_unit = resource['valueQuantity'].get('unit', 'kg')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        weight_history.append({
                            'date': observation_date,
                            'value': weight_value,
                            'unit': weight_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{weight_value} {weight_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            weight_history.sort(key=lambda x: x['date'])
            
        return weight_history
    
            