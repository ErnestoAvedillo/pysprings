from springcalc.lineal.torsion import TorsionSpring
from springcalc.pymodels.material import Material
from math import pi

# Create the material first
material = Material(material_name="SL")
# Create the spring with the correct class
spring = TorsionSpring(material=material, wire_diameter=2.5)
# Configure the spring's properties (using the correct method names)
spring.set_geometry(
    mean_diameter=20.0,
    nr_coils=10,
    pitch=5.0,
    free_angle=45.0,
    fixed_leg_radius=10.0,
    mobile_leg_radius=10.0
)
properties = spring.get_spring_properties()
print("Spring properties after configuration:")
for key, item in properties.items():
    print(f"Value of {key} = {item}")
spring.add_position(angle_travel=10)
spring.add_position(angle_travel=50)
positions = spring.get_positions()
for pos in positions:
    print(f"Position: Load={pos.load} N:")
    print(f"    Stress={pos.stress:.2f} MPa")
    print(f"    Position={pos.position * 180 / pi:.6f} degrees")
    print(f"    Travel={pos.travel * 180 / pi:.6f} degrees")
    print(f"    Outer Diameter={pos.outer_diameter:.6f} mm")
    print(f"    Inner Diameter={pos.inner_diameter:.6f} mm")
    print("-" * 40)
