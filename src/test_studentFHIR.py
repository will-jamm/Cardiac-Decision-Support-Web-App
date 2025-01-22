import json
from datetime import date, datetime

# Our JSON database
JSON_DATABASE = 'data/json_database.json'

# fullUrl is the full "address" under which all patients are in the "server" (which is now just py database).
fullUrl = "http://tutsgnfhir.com"

with open(JSON_DATABASE, 'rb') as json_file:
    patient_json = json.load(json_file)
#print(type(patient_json))

# You can check the structure of the data by checking the json_database.json file OR
# by writing the following code: print(json.dumps(patient_json, indent = 4)).

# Next, we are saving all the patient ID's. If you have checked the structure of the databse,
# you have seen that it is a list of lists, which contains JSON format data. Under each patient,
# there are resources and resourceTypes, and you can find the id here.
id_list = []
for patient in patient_json:
    if patient[0]['resource']['resourceType'] == 'Patient':
        id = patient[0]['resource']['id']
    id_list.append(id) # sums up to total 50 id, which is the number of the patients


# This function gets all data for the patient, based on the patient id.
def getAllDataForOnePatient(patient_id):
    requesturl = fullUrl + "/Patient/"  + patient_id
    for patient in patient_json:
        if patient[0]['fullUrl'] == requesturl:
            patient_info = patient #['resource']

            return patient_info

def getDemographics(patient_id):
    requesturl = fullUrl + "/Patient/"  + patient_id
    for patient in patient_json:

        if patient[0]['fullUrl'] == requesturl:
            resource_patient = patient[0]['resource']
            given = resource_patient['name'][0]['given'][0]
            surname = resource_patient['name'][0]['family'][0]
            born = datetime.strptime(resource_patient['birthDate'], '%Y-%m-%d')
            age = calculateAge(born)

            return given, surname, age

def calculateAge(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def getAll(id):
    demographics = getDemographics(id)
    return demographics

def getResources(patient_id):
    # requesturl = fullUrl + "/Patient/"  + patient_id
    all_data = getAllDataForOnePatient(patient_id)
    print("Patient ID: ", patient_id)
    i=0
    for item in all_data:
        if all_data[i]['resource']['resourceType'] == 'Encounter':
            print(all_data[i]['resource'])
            try:
                print(all_data[i]['resource']['period'])
            except:
                continue

        elif all_data[i]['resource']['resourceType'] == 'Observation':
            print(all_data[i]['resource'])
            try:
                print(all_data[i]['resource']['effectiveDateTime'])
            except:
                continue

        elif all_data[i]['resource']['resourceType'] == 'Procedure':
            print(all_data[i]['resource'])

        elif all_data[i]['resource']['resourceType'] == 'Condition':
            print(all_data[i]['resource'])

        elif all_data[i]['resource']['resourceType'] == 'MedicationDispense':
            print(all_data[i]['resource'])

        i+=1


for id in id_list:
    patientSummary = getAll(id)
    print("\n", "Next patient: ", patientSummary, "\n")
    getResources(id)
    

# Example
getAllDataForOnePatient('665677')
# getDemographics('665677')
# getResources('665677')



