from springcalc import Material, CompressionSpring, ExtensionSpring
from springcalc.pymodels.units import ureg


def test_compression_spring_category_follows_spring_index():
    """wahl_factor_category must reflect the spring index (C), not the Wahl factor value."""
    material = Material(material_name="SL")
    spring = CompressionSpring(material=material, wire_diameter=2.5)
    spring.set_diameter(outer_diameter=30)
    spring.calculate_spring_properties(pitch=20, free_length=100)

    assert spring.spring_index == 11.0
    assert spring.wahl_factor < 4  # the Wahl factor itself is always small (~1.0-1.4)
    assert spring.wahl_factor_category == "green"  # C=11 is in the [6, 12) "green" range


def test_extension_spring_category_follows_spring_index():
    material = Material(material_name="SH")
    spring = ExtensionSpring(material=material, wire_diameter=1.5)
    spring.set_diameter(outer_diameter=15 * ureg.mm)
    spring.calculate_spring_properties(nr_coils=10, free_length=60)

    assert spring.spring_index == 9.0
    assert spring.wahl_factor_category == "green"  # C=9 is in the [6, 12) "green" range
