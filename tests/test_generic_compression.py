import math

import pytest

from springcalc.pymodels.material import Material
from springcalc.pymodels.units import ureg
from springcalc.lineal.generic_compression import CompressionSpringGeneral


def _build_constant_geometry_spring():
    """A constant-diameter, constant-pitch spring should behave like a regular one."""
    material = Material(material_name="SH")
    spring = CompressionSpringGeneral(material=material, wire_diameter=2.0)
    spring.mean_diameter_init = 20 * ureg.mm
    spring.pitch_constant = 6 * ureg.mm
    spring.free_length = 60 * ureg.mm
    return spring


def test_theta_max_matches_coil_count():
    spring = _build_constant_geometry_spring()
    theta_max = spring.calculate_theta_max()

    assert theta_max == pytest.approx(2 * math.pi * 10)
    assert spring.nr_coils == pytest.approx(10)


def test_spring_constant_matches_closed_form():
    spring = _build_constant_geometry_spring()
    k = spring.calculate_spring_constant()

    # Closed-form for a constant-diameter helix: k = G*d^4 / (8*D^3*n)
    material = Material(material_name="SH")
    G = material.shear_modulus.to("MPa").magnitude
    expected = G * (2.0**4) / (8 * (20.0**3) * 10)
    assert k.to("N/mm").magnitude == pytest.approx(expected)


def test_solid_length_and_wire_length():
    spring = _build_constant_geometry_spring()
    spring.calculate_spring_constant()

    solid_length = spring.calculate_solid_length()
    assert solid_length.to("mm").magnitude == pytest.approx(20.0)

    wire_length = spring.calculate_wire_length()
    assert wire_length.to("mm").magnitude > 0


def test_simulate_progressive_compression():
    spring = _build_constant_geometry_spring()
    spring.calculate_spring_constant()

    deflection, force, stiffness = spring.simulate_progressive_compression(
        max_deflection=20 * ureg.mm, steps=20
    )

    assert deflection[-1].to("mm").magnitude == pytest.approx(20.0)
    k = spring.spring_constant.to("N/mm").magnitude
    assert force[-1].to("N").magnitude == pytest.approx(k * 20.0, rel=1e-6)
