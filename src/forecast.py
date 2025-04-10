import pickle
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def forecasting(feat, duration, id):
    df = pd.read_csv("out.csv")
    # f = "heart_rate"
    # f = feat
    only_name_list = ['Ruth C. Black', 'Sophia Reynolds', 'Amy C. Morgan', 'Sarah Y. Graham', 'Billie H. Himston', 'Mary C. Long', 'Ruth C. Cook', 'Thomas Q. Moore', 'Steve Richey', 'Yolanda Warren', 'Paul Luttrell', 'Kimberly Revis', 'Angela Montgomery', 'Amy R. Lee', 'Philip Jones', 'Tiffany Westin', 'Kristyn Walker', 'George McKay', 'Michelle Z. Harris', 'Kimberly S. Moore', 'Donna G. Wilson', 'Carl U. Lee', 'Anthony X. Shaw', 'Anthony Z. Coleman', 'Charles B. Williams', 'Kevin H. Lee', 'Michael I. Lewis', 'Joseph P. Shaw', 'Michelle T. Wilson', 'Sharon P. Green', 'Karen L. Lewis', 'Steven F. Coleman', 'Lisa U. Young', 'Dorothy I. Owens', 'Christopher T. Sherman', 'Penny M. Love', 'Michael J. Peters', 'Mildred E. Hoffman', 'Joshua H. Hill', 'Joshua U. Diaz', 'Amy V. Shaw', 'Joseph I. Ross', 'Robert P. Hill', 'Patrick G. Taylor', 'Joshua P. Williams', 'Carol U. Hughes', 'Daniel A. Johnson', 'Brian Q. Gracia', 'Stephan P. Graham', 'Daniel X. Adams']
    only_pat_id = ['665677','6666001','724111','731673','7321938','736230','765583','767980','7777701','7777702','7777703','7777704','7777705','880378','8888801','8888802','8888803','8888804','629528','640264','644201','1768562','1796238','1869612','1951076','2004454','2042917','2080416','2081539','2113340','2169591','2347217','2354220','2502813','4444001','5555001','5555002','5555003','613876','621799','1032702','1081332','1098667','1134281','1137192','1157764','1186747','1213208','1272431','1288992']
    # id_to_name = only_name_list[only_pat_id.index('665677')]
    id_to_name = only_name_list[only_pat_id.index(str(id))]
    varall = df[df["Name"] == id_to_name]
    vare = varall[varall["Features"] == feat]
    vare = vare.drop(columns=['Features', 'Unit', 'Name'])
    vare.rename(columns={'Values': feat}, inplace=True)

    # Fit ARIMA model (order needs tuning)
    model = ARIMA(vare[feat], order=(5,1,0))
    model = model.fit()
    forecast = model.forecast(steps=duration)  # Predict next 3 days
    print(*forecast.values, sep=', ')

forecasting("oxygen_saturation", 5, 665677)