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
                birthdate = datetime.strptime(resource_patient['birthDate'], '%Y-%m-%d')
                age = self._calculate_age(birthdate, date.today())
                gender = resource_patient['gender']
                return given, surname, birthdate, age, gender
        return None

    def _calculate_age(self, born, reference_date):
        return reference_date.year - born.year - ((reference_date.month, reference_date.day) < (born.month, born.day))
    
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

    def _append_observation_data(self, observations, resource, unit, name):
        """
        Append FHIR observation data to a list of observations.
        This method extracts relevant information from a FHIR observation resource 
        and adds it to the provided observations list in a structured format.
        Args:
            observations (list): List to append the observation data to
            resource (dict): FHIR observation resource containing the data
            unit (str): Default unit to use if not specified in the resource
            name (str): Display name for the observation
        Returns:
            list: Updated observations list with the new observation appended
        Note:
            The resource is expected to contain 'valueQuantity' and 'effectiveDateTime' fields.
            The formatted observation includes the date, value, unit, a formatted date string,
            a display string, and the observation name.
        """
        
        value = resource['valueQuantity'].get('value')
        observation_unit = resource['valueQuantity'].get('unit', unit)
        date_str = resource['effectiveDateTime']
        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
        measurement = resource['code']['coding'][0].get('display')
        observations.append({
            'date': observation_date,
            'value': value,
            'unit': observation_unit,
            'formatted_date': observation_date.strftime('%d-%m-%Y'),
            'display': f"{value:.2f} {unit}",
            'name': name,
            'measurement': measurement
        })
        return observations
        
        
    def _get_observation_history(self, patient_id, observation_codes, default_unit='', name=''):
        """
        Retrieves observation history for a patient with the specified observation codes.
        This method fetches all patient data and filters for specific observation resources
        matching the provided codes or display name.
        Parameters:
        ----------
        patient_id : str
            The ID of the patient to retrieve observations for.
        observation_codes : dict
            Dictionary mapping observation codes to their names. Used to identify relevant observations.
        default_unit : str, optional
            The default unit to use if not specified in the observation. Defaults to empty string.
        name : str, optional
            Name of the observation to filter by display name. Defaults to empty string.
        Returns:
        -------
        list
            A list of dictionaries containing observation data, sorted by date.
            Each dictionary contains date, value, and unit information.
            Returns an empty list if patient data is not found or no matching observations exist.
        """
        patient_data = self.get_all_patient_data(patient_id)
        observations = []
        
        if not patient_data:
            return []
        
        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] != 'Observation':
                continue

            is_target_observation = False
            coding_list = self._get_coding(resource)

            if not coding_list:
                continue

            for coding in coding_list:
                code = coding.get('code')
                display = coding.get('display', '').lower()

                if code in observation_codes:
                    is_target_observation = True
                    observation_name = observation_codes[code]
                    break

                elif name and name.lower() in display:
                    is_target_observation = True
                    observation_name = name
                    break

            if not is_target_observation:
                continue

            observations = self._append_observation_data(observations, resource=resource, unit=default_unit, name=name)
        observations.sort(key=lambda x: x['date'])
        return observations
    
    def get_weight_history(self, patient_id):
        """Get weight history for patient"""
        return self._get_observation_history(
            patient_id,
            {'3141-9': 'Weight'},
            default_unit='kg',
            name='weight'
        )

    def get_height_history(self, patient_id):
        """Get height history for patient"""
        return self._get_observation_history(
            patient_id,
            {'8302-2': 'Height'},
            default_unit='cm',
            name='height'
        )
    
    def get_systolic_blood_pressure_history(self, patient_id):
        """Get systolic blood pressure history for patient"""  
        return self._get_observation_history(
            patient_id,
            {'8480-6': 'Systolic blood pressure'},
            default_unit='mm[Hg]',
            name='systolic blood pressure'
        )

    def get_diastolic_blood_pressure_history(self, patient_id):
        """Get diastolic blood pressure history for patient"""
        return self._get_observation_history(
            patient_id,
            {'8462-4': 'Diastolic blood pressure'},
            default_unit='mm[Hg]',
            name='diastolic blood pressure'
        )

    def get_glucose_history(self, patient_id):
        """Get glucose history for patient"""
        glucose_codes = {
        '2345-7': 'Glucose SerPl-mCnc',
        '5792-7': 'Glucose Ur Strip-mCnc',
        '2342-4': 'Glucose CSF-mCnc',
        '2339-0': 'Glucose Bld-mCnc',
        '1558-6': 'Glucose p fast SerPl-mCnc'
        }
        return self._get_observation_history(
            patient_id,
            glucose_codes, 
            default_unit='mg/dL',
            name='glucose'
        )
    
    def get_cholesterol_history(self, patient_id):
        """Get cholesterol history for patient"""
        return self._get_observation_history(
            patient_id,
            {'2093-3': 'Cholesterol'}, 
            default_unit='mg/dL',
            name='cholest'
        )

    def get_heart_rate_history(self, patient_id):
        """Get heart rate history for patient"""
        return self._get_observation_history(
            patient_id,
            {'8867-4': 'Heart rate'}, 
            default_unit='{beats}/min',
            name='heart rate'
        )
    def get_bmi_history(self, patient_id):
        """Get bmi history for patient"""
        return self._get_observation_history(
            patient_id,
            {'39156-5': 'bmi'},
            default_unit='kg/m2',
            name='bmi'
        )