""" The degree-2 polynomial regression model is used to fit a descending curve to the
factor f vs Sut data. Shigley Mechanical Engineering Design, 9th edition, p. 272, chart 6-18"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
from pandas import read_csv
import json
import os

# Paths relative to the script so it works on any machine.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
# The fitted coefficients are saved inside the package, where they are loaded at
# runtime by springcalc.regresiones.factor_f.usar_modelo_factor_f. Only plain
# numbers are shipped (no pickled sklearn objects) so the library never depends
# on the scikit-learn version used at training time.
COEFS_SALIDA = os.path.join(
    REPO_ROOT, "src", "springcalc", "regresiones", "factor_f", "factor_f_coeffs.json"
)

# 1. Data forming a descending curve
file = os.path.join(SCRIPT_DIR, "factor__f_vs_RMa.csv")
pd = read_csv(file, header=0, skipinitialspace=True)  # skipinitialspace handles spaces after commas
X = pd["Sut"].values.reshape(-1, 1)  # Reshape into a single-column matrix
y = pd["valor_f"].values.reshape(-1, 1)  # Reshape into a single-column matrix
X = np.log(X)  # Transform X so it becomes a descending curve
y = np.log(y)  # Transform y so it becomes a descending curve
# 2. Transform X so the model can capture curves (degree 2)
# This turns X into [X, X^2]
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)

# 3. Train the model with the transformed data
curve_model = LinearRegression()
curve_model.fit(X_poly, y)

# Fold the PolynomialFeatures bias column into the model intercept, so the
# saved coefficients are a plain ascending-power polynomial: c0 + c1*x + c2*x^2.
# NOTE: key 'coefficients_ascending_powers' is the on-disk contract read by
# usar_modelo_factor_f.py.
coefficients = curve_model.coef_[0].copy()
coefficients[0] += curve_model.intercept_[0]
coeffs_data = {
    'descripcion': 'Degree-2 polynomial regression model for factor f vs Sut',
    'entrada': 'Sut (natural log must be applied beforehand)',
    'salida': 'factor f',
    'coefficients_ascending_powers': coefficients.tolist(),
}

# Save as plain JSON (no pickled sklearn objects, so the library never depends
# on the scikit-learn version used at training time).
with open(COEFS_SALIDA, 'w') as f:
    json.dump(coeffs_data, f, indent=4)

print(f"Coefficients saved successfully to '{COEFS_SALIDA}'")

# 4. Prediction and visualization
y_fit = curve_model.predict(poly.transform(X))

# Calculate R² (coefficient of determination) as an accuracy measure
r2 = r2_score(y, y_fit)

plt.scatter(X, y, color='blue', label='Actual data')
plt.plot(X, y_fit, color='green', label=f'Polynomial Regression (R² = {r2:.4f})')
plt.title('Descending Curve Fit')
plt.xlabel('log(Sut)')
plt.ylabel('factor f')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

print(f"Model accuracy (R²): {r2:.4f} ({r2*100:.2f}%)")
