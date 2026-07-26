import os
import pickle
import numpy as np

# Use a package-relative path so the model loads correctly regardless of user home
MODELO = os.path.join(os.path.dirname(__file__), 'modelo_factor_f.pkl')

class ModelFactorF:
    def __init__(self, model_path:str=MODELO):
        self.load_factor_f_model(model_path)
        self.poly_transformer = self.full_model['poly_transformer']
        self.info = self.full_model['info']

    def predict(self, sut_valor):
        """
        Predicts the factor f for a given Sut value.
        Outside the fitted range, below N=10³ and above N=10⁶, the values f=0.9 and f=0.76
        are assigned respectively, per Shigley Mechanical Engineering Design, 9th edition,
        chart 6-18, page 272.

        Args:
            sut_valor: Ultimate strength value (Sut)

        Returns:
            factor_f: Predicted value for factor f
        """
        if sut_valor <= 480:
            return 0.9
        elif sut_valor >= 1380:
            return 0.76

        # Apply the natural logarithm
        sut_log = np.log([[sut_valor]])

        # Transform with the polynomial
        sut_poly = self.poly_transformer.transform(sut_log)

        # predict
        factor_f = self.full_model['modelo'].predict(sut_poly)[0][0]

        factor_f = np.exp(factor_f)  # Convert the logarithm to a real value

        return factor_f

    def load_factor_f_model(self, model_path):
        """
        Load the trained model used to calculate the factor f
        """
        with open(model_path, 'rb') as f:
            self.full_model = pickle.load(f)
        return

# Usage example
if __name__ == "__main__":
    # Load model
    model = ModelFactorF(MODELO)

    # Show model information
    print("Model information:")
    print(f"Description: {model.info['descripcion']}")
    print(f"Input: {model.info['entrada']}")
    print(f"Output: {model.info['salida']}")
    print()

    # Prediction examples
    values_sut = [300,500, 600, 700, 800, 1200, 1500]  # Sut values to test

    print("Predictions:")
    for sut in values_sut:
        factor_f = model.predict(sut)
        print(f"Sut = {sut} MPa --> factor f = {factor_f:.4f}")
