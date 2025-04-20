import os
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def get_feature_list():
    csv_path = os.path.join(os.path.dirname(__file__), "out.csv")
    df = pd.read_csv(csv_path)
    return df["Features"].unique().tolist()

def get_patient_name_by_id(patient_id):
    only_name_list = ['Ruth C. Black', 'Sophia Reynolds', 'Amy C. Morgan', 'Sarah Y. Graham', 'Billie H. Himston',
                      'Mary C. Long', 'Ruth C. Cook', 'Thomas Q. Moore', 'Steve Richey', 'Yolanda Warren',
                      'Paul Luttrell', 'Kimberly Revis', 'Angela Montgomery', 'Amy R. Lee', 'Philip Jones',
                      'Tiffany Westin', 'Kristyn Walker', 'George McKay', 'Michelle Z. Harris', 'Kimberly S. Moore',
                      'Donna G. Wilson', 'Carl U. Lee', 'Anthony X. Shaw', 'Anthony Z. Coleman', 'Charles B. Williams',
                      'Kevin H. Lee', 'Michael I. Lewis', 'Joseph P. Shaw', 'Michelle T. Wilson', 'Sharon P. Green',
                      'Karen L. Lewis', 'Steven F. Coleman', 'Lisa U. Young', 'Dorothy I. Owens',
                      'Christopher T. Sherman', 'Penny M. Love', 'Michael J. Peters', 'Mildred E. Hoffman',
                      'Joshua H. Hill', 'Joshua U. Diaz', 'Amy V. Shaw', 'Joseph I. Ross', 'Robert P. Hill',
                      'Patrick G. Taylor', 'Joshua P. Williams', 'Carol U. Hughes', 'Daniel A. Johnson',
                      'Brian Q. Gracia', 'Stephan P. Graham', 'Daniel X. Adams']
    only_pat_id = ['665677', '6666001', '724111', '731673', '7321938', '736230', '765583', '767980', '7777701',
                   '7777702', '7777703', '7777704', '7777705', '880378', '8888801', '8888802', '8888803', '8888804',
                   '629528', '640264', '644201', '1768562', '1796238', '1869612', '1951076', '2004454', '2042917',
                   '2080416', '2081539', '2113340', '2169591', '2347217', '2354220', '2502813', '4444001', '5555001',
                   '5555002', '5555003', '613876', '621799', '1032702', '1081332', '1098667', '1134281', '1137192',
                   '1157764', '1186747', '1213208', '1272431', '1288992']

    return only_name_list[only_pat_id.index(str(patient_id))]


def forecasting(feat, duration, patient_id):
    df_path = os.path.join(os.path.dirname(__file__), "out.csv")
    df = pd.read_csv(df_path)

    try:
        id_to_name = get_patient_name_by_id(patient_id)
    except ValueError:
        return "Patient ID not found."

    varall = df[df["Name"] == id_to_name]
    vare = varall[varall["Features"] == feat]
    vare = vare.drop(columns=['Features', 'Unit', 'Name'])

    if vare.empty or len(vare["Values"]) < 2:
        return "Not enough data to do prediction."

    vare.rename(columns={'Values': feat}, inplace=True)
    model = ARIMA(vare[feat], order=(1, 1, 2))  # A more general model
    model = model.fit()
    forecast = model.forecast(steps=duration)
    return forecast
# forecasting("oxygen_saturation", 5, 665677)