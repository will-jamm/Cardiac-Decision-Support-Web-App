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

    def get_height_history(self, patient_id):
        """
        Retrieves the height history for a specified patient.
        This method fetches all observations for the patient and filters for height measurements,
        identified by LOINC code '8302-2' or by having 'height' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose height history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing height measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric height value
            - 'unit': unit of measurement (defaults to 'cm')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "170 cm")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        height_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isHeight = False
                coding_list = self._get_coding(resource)

                for coding in coding_list:
                    if coding.get('code') == '8302-2' or 'height' in coding.get('display', '').lower():
                        isHeight = True
                        break

                if isHeight == True:
                    try:
                        height_value = resource['valueQuantity'].get('value')
                        height_unit = resource['valueQuantity'].get('unit', 'cm')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        height_history.append({
                            'date': observation_date,
                            'value': height_value,
                            'unit': height_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{height_value} {height_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            height_history.sort(key=lambda x: x['date'])

        return height_history

    def get_systolic_blood_pressure_history(self, patient_id):
        """
        Retrieves the systolic blood pressure history for a specified patient.
        This method fetches all observations for the patient and filters for systolic blood pressure measurements,
        identified by LOINC code '8480-6' or by having 'Systolic blood pressure' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose blood pressure history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing systolic blood pressure measurements sorted by date, or None if the
            patient data could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric systolic blood pressure value
            - 'unit': unit of measurement (defaults to 'mm[Hg]')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "110 mm[Hg]")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        systolic_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isSystolic = False
                coding_list = self._get_coding(resource)

                for coding in coding_list:
                    if coding.get('code') == '8480-6' or 'Systolic blood pressure' in coding.get('display', '').lower():
                        isSystolic = True
                        break

                if isSystolic == True:
                    try:
                        systolic_value = resource['valueQuantity'].get('value')
                        systolic_unit = resource['valueQuantity'].get('unit', 'mm[Hg]')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        systolic_history.append({
                            'date': observation_date,
                            'value': systolic_value,
                            'unit': systolic_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{systolic_value} {systolic_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            systolic_history.sort(key=lambda x: x['date'])

        return systolic_history

    def get_diastolic_blood_pressure_history(self, patient_id):
        """
        Retrieves the diastolic blood pressure history for a specified patient.
        This method fetches all observations for the patient and filters for diastolic blood pressure measurements,
        identified by LOINC code '8462-4' or by having 'Diastolic blood pressure' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose blood pressure history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing blood pressure measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric diastolic blood pressure value
            - 'unit': unit of measurement (defaults to 'mm[Hg]')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "70 mm[Hg]")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        diastolic_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isDiastolic = False
                coding_list = self._get_coding(resource)

                for coding in coding_list:
                    if coding.get('code') == '8462-4' or 'diastolic blood pressure' in coding.get('display', '').lower():
                        isDiastolic = True
                        break

                if isDiastolic == True:
                    try:
                        diastolic_value = resource['valueQuantity'].get('value')
                        diastolic_unit = resource['valueQuantity'].get('unit', 'mm[Hg]')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        diastolic_history.append({
                            'date': observation_date,
                            'value': diastolic_value,
                            'unit': diastolic_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{diastolic_value} {diastolic_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            diastolic_history.sort(key=lambda x: x['date'])

        return diastolic_history

    def get_glucose_history(self, patient_id):
        """
        Retrieves the glucose measurement history for a specified patient.
        This method fetches all observations for the patient and filters for glucose measurements,
        identified by specific LOINC codes or by having 'Glucose' in the display text.

        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose glucose history is being requested.

        Returns:
        -------
        list or None:
            A list of dictionaries containing glucose measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric glucose value
            - 'unit': unit of measurement (defaults to 'mg/dL')
            - 'measurement': the display name for the glucose measurement
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "80 mg/dL")

        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        glucose_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isGlucose = False
                coding_list = self._get_coding(resource)

                glucose_codes = [
                    {'code': '2345-7', 'display': 'Glucose SerPl-mCnc'},
                    {'code': '5792-7', 'display': 'Glucose Ur Strip-mCnc'},
                    {'code': '2342-4', 'display': 'Glucose CSF-mCnc'},
                    {'code': '2339-0', 'display': 'Glucose Bld-mCnc'},
                    {'code': '1558-6', 'display': 'Glucose p fast SerPl-mCnc'}
                ]

                for coding in coding_list:
                    for glucose in glucose_codes:
                        if coding.get('code') == glucose['code'] or 'glucose' in coding.get('display', '').lower():
                            isGlucose = True
                            measurement = glucose['display']
                            break
                    if isGlucose:
                        break

                if isGlucose:
                    try:
                        glucose_value = resource['valueQuantity'].get('value')
                        glucose_unit = resource['valueQuantity'].get('unit', 'mg/dL')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')

                        glucose_history.append({
                            'date': observation_date,
                            'value': glucose_value,
                            'unit': glucose_unit,
                            'measurement': measurement,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{glucose_value} {glucose_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue

        glucose_history.sort(key=lambda x: x['date'])

        return glucose_history

    def get_cholesterol_history(self, patient_id):
        """
        Retrieves the cholesterol history for a specified patient.
        This method fetches all observations for the patient and filters for cholestelor measurements,
        identified by LOINC code '2093-3' or by having 'Cholest SerPl-mCnc' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose cholesterol history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing cholesterol measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric cholesterol value
            - 'unit': unit of measurement (defaults to 'mg/dL')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "145 mg/dL")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        cholest_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isCholest = False
                coding_list = self._get_coding(resource)

                for coding in coding_list:
                    if coding.get('code') == '2093-3' or 'cholest SerPl-mCnc' in coding.get('display', '').lower():
                        isCholest = True
                        break

                if isCholest == True:
                    try:
                        cholest_value = resource['valueQuantity'].get('value')
                        cholest_unit = resource['valueQuantity'].get('unit', 'mm[Hg]')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        cholest_history.append({
                            'date': observation_date,
                            'value': cholest_value,
                            'unit': cholest_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{cholest_value} {cholest_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            cholest_history.sort(key=lambda x: x['date'])

        return cholest_history

    def get_heart_rate_history(self, patient_id):
        """
        Retrieves the heart rate history for a specified patient.
        This method fetches all observations for the patient and filters for heart rate measurements,
        identified by LOINC code '8867-4' or by having 'heart_rate' in the display text.
        Parameters:
        ----------
        patient_id : str
            The FHIR ID of the patient whose heart rate history is being requested.
        Returns:
        -------
        list or None:
            A list of dictionaries containing heart rate measurements sorted by date, or None if the patient data
            could not be retrieved.
            Each dictionary contains:
            - 'date': datetime object representing the observation date
            - 'value': numeric heart rate value
            - 'unit': unit of measurement (defaults to '{beats}/min')
            - 'formatted_date': the date formatted as 'YYYY-MM-DD'
            - 'display': formatted string combining the value and unit (e.g., "70 {beats}/min")
        Notes:
        -----
        The method continues processing even if some observations have invalid or missing data.
        """
        heart_rate_history = []
        patient_data = self.get_all_patient_data(patient_id)

        if not patient_data:
            return None

        for entry in patient_data:
            if 'resource' not in entry:
                continue

            resource = entry['resource']
            if resource['resourceType'] == 'Observation':
                isHeartRate = False
                coding_list = self._get_coding(resource)

                for coding in coding_list:
                    if coding.get('code') == '8867-4' or 'heart_rate' in coding.get('display', '').lower():
                        isHeartRate = True
                        break

                if isHeartRate == True:
                    try:
                        heart_rate_value = resource['valueQuantity'].get('value')
                        heart_rate_unit = resource['valueQuantity'].get('unit', '{beats}/min')
                        date_str = resource['effectiveDateTime']
                        observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                        print(observation_date)
                        heart_rate_history.append({
                            'date': observation_date,
                            'value': heart_rate_value,
                            'unit': heart_rate_unit,
                            'formatted_date': observation_date.strftime('%Y-%m-%d'),
                            'display': f"{heart_rate_value} {heart_rate_unit}"
                        })
                    except (ValueError, KeyError) as e:
                        continue
            heart_rate_history.sort(key=lambda x: x['date'])

        return heart_rate_history
