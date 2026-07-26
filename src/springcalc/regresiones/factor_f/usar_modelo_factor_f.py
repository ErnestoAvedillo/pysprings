import json
import os
import numpy as np

# Use a package-relative path so the model loads correctly regardless of user home
MODELO = os.path.join(os.path.dirname(__file__), 'factor_f_coeffs.json')

class ModelFactorF:
    def __init__(self, model_path: str = MODELO):
        self.load_factor_f_model(model_path)

    def predict(self, sut_valor):
        """
        Predicts the factor f for a given Sut value.
        Outside the fitted range, between N=10³ and N=10⁶, the values f=0.9 and f=0.76
        are assigned respectively, per Shigley Mechanical Engineering Design, 9th edition,
        chart 6-18, page 272.

        Args:
            sut_valor: Ultimate tensile strength value (Sut)

        Returns:
            factor_f: Predicted value of the factor f
        """
        if sut_valor <= 480:
            return 0.9
        elif sut_valor >= 1380:
            return 0.76

        # Apply the natural logarithm, as during training
        sut_log = np.log(sut_valor)

        # Evaluate the fitted degree-2 polynomial directly (coefficients in
        # ascending power order: c0 + c1*x + c2*x^2)
        factor_f_log = np.polynomial.polynomial.polyval(sut_log, self.coefficients)

        factor_f = np.exp(factor_f_log)  # Convert from log back to the real value

        return factor_f

    def load_factor_f_model(self, model_path):
        """
        Load the fitted polynomial coefficients used to calculate the factor f
        """
        with open(model_path, 'r') as f:
            data = json.load(f)
        self.coefficients = data['coefficients_ascending_powers']
        self.info = {
            'descripcion': data['descripcion'],
            'entrada': data['entrada'],
            'salida': data['salida'],
        }
        return

# Usage example
if __name__ == "__main__":
    # Load model
    modelo = ModelFactorF(MODELO)

    # Show model info
    print("Model info:")
    print(f"Description: {modelo.info['descripcion']}")
    print(f"Input: {modelo.info['entrada']}")
    print(f"Output: {modelo.info['salida']}")
    print()

    # Prediction examples
    valores_sut = [300,500, 600, 700, 800, 1200, 1500]  # Sut values to test

    print("Predictions:")
    for sut in valores_sut:
        factor_f = modelo.predict(sut)
        print(f"Sut = {sut} MPa → factor f = {factor_f:.4f}")
