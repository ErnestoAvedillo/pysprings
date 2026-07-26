from springcalc.regresiones.factor_f.usar_modelo_factor_f import ModelFactorF
import numpy as np
from math import log10
from springcalc.pymodels.material import Material
from springcalc.pymodels.wire_characteristics import WireCharacteristics
from matplotlib import pyplot as plt
def test_factor_f():
    """Test of the regression model for the factor f"""
    print("=== TEST OF THE REGRESSION MODEL FOR THE FACTOR f ===")

    material = Material(material_name="DH")
    wire_char = WireCharacteristics(material=material, wire_diameter=1.5)
    print(f"Material: {material.material_name}, RMa_min: {wire_char.RMa_min:.2f} MPa")

    # Load model
    modelo = ModelFactorF()

    # Sut values to test (including out-of-range cases)
    cycles_to_test = [950,1000, 1050, 10000, 100000, 1000000, 10000000]  # Cycles to test

    print("cycles| Predicted factor f | Ssf")
    print("-------------------------------")
    SSf = []
    Sse_prime = wire_char.material.elastic_limit_factor * wire_char.RMa_min
    for cycle in cycles_to_test:
        f_predicho = modelo.predict(wire_char.RMa_min)
        if cycle <= 1e3:
            Ssf_prime = cycle**(log10(f_predicho)/3)  # Approximation for low cycle counts
        else:
            if cycle > 1e6:
                cycle = 1e6  # Cap at 1 million cycles for the prediction
            a = f_predicho **2 / wire_char.material.elastic_limit_factor
            b = -log10(f_predicho  * wire_char.RMa_min / Sse_prime) / 3
            Ssf_prime = a * cycle**b

        print(f"{cycle:8} | {f_predicho:.4f}")
        SSf.append(Ssf_prime)

    plt.figure(figsize=(8, 5))
    plt.plot(cycles_to_test, SSf, marker='o')
    plt.xscale('log')
    plt.title("Fatigue strength Ssf' vs Cycles")
    plt.xlabel("Cycles (log scale)")
    plt.ylabel("Fatigue strength Ssf' (MPa)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    test_factor_f()
