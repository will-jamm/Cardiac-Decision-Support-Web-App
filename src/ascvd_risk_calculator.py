import pandas as pd
import numpy as np
import math

class ASCVDRiskCalculator:

    def __init__(self):
            self.coefficients = {
                'male' : {
                    'ln_age': 12.344,
                    'ln_total_chol': 11.853,
                    'ln_age_total_chol': -2.664,
                    'ln_hdl': -7.990,
                    'ln_age_hdl': 1.769,
                    'ln_treated_systolic_bp': 1.797,
                    'ln_untreated_systolic_bp': 1.764,
                    'current_smoker': 7.837,
                    'ln_age_smoker': -1.795,
                    'diabetes': 0.658,
                    'baseline_survival': 0.9144,
                    'mean_term': 61.18
                },
                'female': {
                    'ln_age': -29.799,
                    'ln_age_squared': 4.884,
                    'ln_total_chol': 13.540,
                    'ln_age_total_chol': -3.114,
                    'ln_hdl': -13.578,
                    'ln_age_hdl': 3.149,
                    'ln_treated_systolic_bp': 2.019,
                    'ln_untreated_systolic_bp': 1.957,
                    'current_smoker': 7.574,
                    'ln_age_smoker': -1.655,
                    'diabetes': 0.661,
                    'baseline_survival': 0.9665,
                    'mean_term': -29.18
                }
            }

    def compute_10_year_risk(self, age, sex, total_cholesterol, hdl_cholesterol,
                               systolic_bp, isBpTreated, isSmoker, hasDiabetes):
    
        validation = self._validate_inputs(age, sex, total_cholesterol, hdl_cholesterol, systolic_bp)

        if validation['status'] == 'error':
            return validation
        
        coef = self.coefficients[sex]

        baseline_survival = coef['baseline_survival']
        mean_term = coef['mean_term']
        predict = 0

        ln_age = np.log(age)
        ln_total_chol = np.log(total_cholesterol)
        ln_hdl = np.log(hdl_cholesterol)
        age_hdl = ln_age * ln_hdl
        age_smoker = ln_age if isSmoker else 0
        age_total_chol = ln_age * ln_total_chol
        ln_treated_sbp = np.log(systolic_bp) if isBpTreated else 0
        ln_untreated_sbp = 0 if isBpTreated else np.log(systolic_bp)

        predict += coef['ln_age'] * ln_age

        if sex.lower() == "female":
            predict += coef['ln_age_squared'] * (ln_age ** 2)

        predict += coef['ln_total_chol'] * ln_total_chol
        predict += coef['ln_age_total_chol'] * age_total_chol

        predict += coef['ln_hdl'] * ln_hdl
        predict += coef['ln_age_hdl'] * age_hdl

        predict += coef['ln_treated_systolic_bp'] * ln_treated_sbp
        predict += coef['ln_untreated_systolic_bp'] * ln_untreated_sbp

        predict += coef['current_smoker'] * int(isSmoker)
        predict += coef['ln_age_smoker'] * age_smoker

        predict += coef['diabetes'] * int(hasDiabetes)
            
        risk_percent = (1 - (baseline_survival ** np.exp(predict - mean_term))) * 100
            
        return risk_percent

    def _validate_inputs(self, age, sex, total_cholesterol, hdl_cholesterol, systolic_bp):
        
        if age < 40 or age >79:
            return {
                'status': 'error',
                'message': 'Age must be between 40 and 79 years for ASCD risk calculation'
            }
        
        if sex.lower() not in ['male', 'female']:
            return {
                'status': 'error',
                'message': 'Sex must be "male" or "female"'
            }
        
        if total_cholesterol < 130 or total_cholesterol > 320:
            return {
                'status': 'warning',
                'message': 'Total cholesterol outside typical range (130-320 mg/dL)'
            }
        
        if hdl_cholesterol < 20 or hdl_cholesterol > 100:
            return {
                'status': 'warning',
                'message': 'HDL cholesterol outside typical range (20-100 mg/dL)'
            }
        
        if systolic_bp < 90 or systolic_bp > 200:
            return {
                'status': 'warning',
                'message': 'Systolic blood pressure outside typical range (90-200 mmHg)'
            }
        
        return {'status': 'ok'}
    
    def _get_risk_category(self, risk_percent):

        if risk_percent < 5:
            return 'Low'
        
        elif risk_percent < 7.5:
            return 'Borderline'
        
        elif risk_percent < 20:
            return 'Intermediate'
        
        else:
            return 'High'
        
def main():
    calculator = ASCVDRiskCalculator()

    test_patient1 = {
        'age': 55,
        'sex': 'male',
        'total_cholesterol': 213,
        'hdl_cholesterol': 50,
        'systolic_bp': 120,
        'isBpTreated': False,
        'isSmoker': False,
        'hasDiabetes': False
    }

    test_patient2 = {
        'age': 55,
        'sex': 'female',
        'total_cholesterol': 213,
        'hdl_cholesterol': 50,
        'systolic_bp': 120,
        'isBpTreated': False,
        'isSmoker': False,
        'hasDiabetes': False
    }
    
    risk = calculator.compute_10_year_risk(
            age=test_patient2['age'],
            sex=test_patient2['sex'],
            total_cholesterol=test_patient2['total_cholesterol'],
            hdl_cholesterol=test_patient2['hdl_cholesterol'],
            systolic_bp=test_patient2['systolic_bp'],
            isBpTreated=test_patient2['isBpTreated'],
            isSmoker=test_patient2['isSmoker'],
            hasDiabetes=test_patient2['hasDiabetes']
    )

if __name__ == "__main__":
    main()