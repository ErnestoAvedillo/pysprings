import math
import base64
import pytest
from pint import Quantity

from springcalc.pymodels.material import Material
from springcalc.pymodels.units import ureg
from springcalc.lineal.generic_compression import CompressionSpringGeneral
from springcalc.lineal.compresion import CompressionSpring


def _build_constant_geometry_spring():
    """A constant-diameter, constant-pitch spring should behave like a regular one."""
    material = Material(material_name="SH")
    spring = CompressionSpringGeneral(material=material, wire_diameter=2.0)
    spring.set_geometry(func_D=lambda x: 20 * ureg.mm, func_p=lambda x: 6 * ureg.mm, free_length=60 * ureg.mm)
    std_spring = CompressionSpring(material=material, wire_diameter=2.0)
    std_spring.set_geometry(mean_diameter=20 * ureg.mm, pitch=6 * ureg.mm, free_length=60 * ureg.mm)
    positions = [30, 50]
    for pos in positions:
        spring.add_load_position(length=pos * ureg.mm)
        std_spring.add_load_position(length=pos * ureg.mm)
    spring.calculate_spring_properties()
    spring_data = spring.get_spring_data()
    std_spring_data = std_spring.get_spring_data()
    print(f"✅ Constant-geometry CompressionSpringGeneral test, data of the generic class:")
    for key, value in spring_data.items():
        print(f"{key}: {value}")
    print(f"✅ Constant-geometry CompressionSpring test, data of the standard class:")
    for key, value in std_spring_data.items():
        print(f"{key}: {value}")
    print(f"✅ Comparing CompressionSpringGeneral and CompressionSpring data:")
    for key, value in spring_data.items():
        std_value = std_spring_data[key]
        print(f"{key}: {value}, std: {std_value}")
        if isinstance(value, Quantity):
            assert value.magnitude == pytest.approx(std_value.to(value.units).magnitude, rel=0.03)
        else:
            assert value == pytest.approx(std_value, rel=0.03)
    return spring


def test_theta_max_matches_coil_count():
    spring = _build_constant_geometry_spring()
    theta_max = spring.calculate_theta_max()

    assert theta_max == pytest.approx(2 * math.pi * 10)
    assert spring.nr_coils == pytest.approx(10)


def test_2K_constant_pitch(x: Quantity):
    if not isinstance(x, Quantity):
        x = x * ureg.mm
    if x.magnitude < 0 or x.magnitude > 100:
        raise ValueError("x must be between 0 and 100 mm")
    if x.magnitude < 30:
        pitch = 2.5 * ureg.mm
    else:
        pitch = 8.0 * ureg.mm
    return pitch


def test_simulate_progressive_compression():
    spring = _build_constant_geometry_spring()

    spring.set_geometry(func_D=lambda x: 20 * ureg.mm,
                        func_p=lambda x: test_2K_constant_pitch(x),
                        free_length=100 * ureg.mm)

    deflection, force, stiffness = spring.simulate_progressive_compression(
        max_deflection=20 * ureg.mm, steps=20
    )

    # get_progressive_compression_graph returns a base64 PNG (same convention
    # as CompressionSpring's other graph methods, for embedding in HTML/PDF).
    # For local debugging, decode it and write it to disk to look at it,
    # since plt.show() can't open a window under the "Agg" backend.
    plot_data = spring.get_progressive_compression_graph(deflection, force, show=True)
    with open("progressive_compression.png", "wb") as f:
        f.write(base64.b64decode(plot_data))

if __name__ == "__main__":
    # _build_constant_geometry_spring()
    # test_theta_max_matches_coil_count()
    test_simulate_progressive_compression()