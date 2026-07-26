from springcalc.lineal.compresion import CompressionSpring
from springcalc.pymodels.material import Material

# Create the material first
material = Material(material_name="SL")

# Create the spring with the correct class
spring = CompressionSpring(material=material, wire_diameter=2.5)

# Configure the spring's properties (using the correct method names).
# set_diameter sets mean/outer/inner diameter from one of them.
spring.set_diameter(outer_diameter=30)
print(f"✅ Basic CompressionSpring test")
print(f"Material: {spring.material.material_name}")
print(f"Wire diameter: {spring.wire_diameter}")
print(f"Mean diameter: {spring.mean_diameter}")
print(f"Number of coils: {spring.nr_coils}")
print(f"Free length: {spring.free_length}")

# Basic calculation example
if hasattr(spring, 'calculate_spring_index'):
    index = spring.calculate_spring_index()
    print(f"Spring index: {index:.2f}")

if hasattr(spring, 'calculate_wahl_factor'):
    # calculate_wahl_factor returns (factor, category)
    wahl_factor, _ = spring.calculate_wahl_factor()
    if wahl_factor is not None:
        print(f"Wahl factor: {wahl_factor:.3f}")
    else:
        print(f"Wahl factor: Not calculated (null value)")

spring.calculate_spring_properties(nr_coils=10, pitch=None, free_length=100)
positions = [30,40,50,60,70,80,90,100]
for pos in positions:
    spring.add_load_position(length=pos)

spring_data = spring.get_spring_data()
for key, value in spring_data.items():
    print(f"{key}: {value}")

data_positions = spring.get_data_positions()
for pc in data_positions:
    print(f"Position: {pc.position}, Load: {pc.load}, Stress: {pc.stress}, Outer Diameter: {pc.outer_diameter}")

print("🎉 Test completed successfully!")
