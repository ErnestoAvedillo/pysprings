""" The degree-2 polynomial regression model is used to fit a descending curve to the
factor f vs Sut data. Shigley Mechanical Engineering Design, 9th edition, p. 272, chart 6-18"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
from pandas import read_csv
import pickle
import os

from scipy.optimize import curve_fit

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def model_func(x, A, B, C, D, E):
    return (A*x - B)/(C*x - D) + E/x

def torsion_wahl_factor(x):
    return (4*x**2 - x - 1)/(4 * x * (x - 1))

# 1. Data forming a descending curve
file = os.path.join(SCRIPT_DIR, "Wahl factor vs index.csv")
pd = read_csv(file, header=0, skipinitialspace=True)  # skipinitialspace handles spaces after commas
X = pd["index"].values.reshape(-1, 1)  # Reshape into a single-column matrix
y = pd["Wahl_f"].values.reshape(-1, 1)  # Reshape into a single-column matrix
# X = np.log(X)  # Transform X so it becomes a descending curve
y_prima = np.log(y)  # Transform y so it becomes a descending curve
# 2. Transform X so the model can capture curves (degree 2)
# This turns X into [X, X^2]
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)

# 3. Train the model with the transformed data
curve_model = LinearRegression()
curve_model.fit(X_poly, y_prima)

# Save the full model (model + polynomial transformer)
full_model = {
    'modelo': curve_model,
    'poly_transformer': poly,
    'info': {
        'descripcion': 'Degree-2 polynomial regression model for factor f vs Sut',
        'entrada': 'Sut (natural log must be applied beforehand)',
        'salida': 'factor f'
    }
}

# Save to a pickle file
output_file = os.path.join(SCRIPT_DIR, "modelo_factor_f.pkl")
with open(output_file, 'wb') as f:
    pickle.dump(full_model, f)

print(f"Model saved successfully to '{output_file}'")

# 4. Prediction and visualization
y_fit = np.exp(curve_model.predict(poly.transform(X)))


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

popt, pcov = curve_fit(model_func, X.ravel(), y_prima.ravel(), p0=[1, 1, 1, 1, 1])

fit_parameters = {
    'popt': popt,
    'pcov': pcov,
    'param_names': ['A', 'B', 'C', 'D', 'E']
}
output_params_file = os.path.join(SCRIPT_DIR, "parametros_popt.pkl")
with open(output_params_file, 'wb') as file_handle:
    pickle.dump(fit_parameters, file_handle)

print("Fitted parameters:", popt)
print(f"Parameters saved successfully to '{output_params_file}'")

""" The degree-2 polynomial regression model is used to fit a descending curve to the
factor f vs Sut data. Shigley Mechanical Engineering Design, 9th edition, p. 272, chart 6-18"""

with open(output_params_file, 'rb') as file_handle:
    data = pickle.load(file_handle)

popt = data["popt"]
pcov = data["pcov"]

# 4. Prediction and visualization
y_fit = np.exp(model_func(X.ravel(), *popt))

# Calculate R² (coefficient of determination) as an accuracy measure
r2 = r2_score(y.ravel(), y_fit)

plt.scatter(X.ravel(), y.ravel(), color='blue', label='Actual data')
plt.plot(X, y_fit, color='green', label=f'Polynomial Regression (R² = {r2:.4f})')
plt.title('Descending Curve Fit')
plt.xlabel('log(Sut)')
plt.ylabel('factor f')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()


y_fit = torsion_wahl_factor(X.ravel())
r2 = r2_score(y.ravel(), y_fit)
plt.scatter(X.ravel(), y.ravel(), color='blue', label='Actual data')
plt.plot(X, y_fit, color='green', label=f'Polynomial Regression (R² = {r2:.4f})')
plt.title('Descending Curve Fit')
plt.xlabel('log(Sut)')
plt.ylabel('factor f')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
