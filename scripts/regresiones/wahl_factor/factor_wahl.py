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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Data forming a descending curve
file = os.path.join(SCRIPT_DIR, "Wahl factor vs index.csv")
pd = read_csv(file, header=0, skipinitialspace=True)  # skipinitialspace handles spaces after commas
X = pd["index"].values.reshape(-1, 1)  # Reshape into a single-column matrix
y = pd["Wahl_f"].values.reshape(-1, 1)  # Reshape into a single-column matrix
#X = np.log(X)  # Transform X so it becomes a descending curve
#y = np.log(y)  # Transform y so it becomes a descending curve
# 2. Transform X so the model can capture curves (degree 2)
# This turns X into [X, X^2]
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)

# 3. Train the model with the transformed data
curve_model = LinearRegression()
curve_model.fit(X_poly, y)

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
