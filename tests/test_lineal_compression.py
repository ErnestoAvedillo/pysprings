from springcalc.lineal.compresion import CompressionSpring
from springcalc.pymodels.material import Material

# Create the material first
material = Material(material_name="SL")

# Create the spring with the correct class
spring = CompressionSpring(material=material, wire_diameter=2.5)
# Configure the spring's properties (using the correct method names)
spring.set_diameter(outer_diameter=30)
print("✅ Basic CompressionSpring test")

spring.calculate_spring_properties(nr_coils=None, pitch=20, free_length=100)

positions = [30, 40, 50, 60, 70, 80, 90, 100]
for pos in positions:
    try:
        spring.add_load_position(length=pos)
    except ValueError as e:
        print(f"Error adding load position at length {pos}: {e}")

spring_data = spring.get_spring_data()
for key, value in spring_data.items():
    print(f"{key}: {value}")

data_positions = spring.get_data_positions()
for pc in data_positions:
    print(f"Position: {pc.position}, Load: {pc.load}, Stress: {pc.stress}, Outer Diameter: {pc.outer_diameter}")

spring.get_forces_vs_position_graph(show=True)
spring.get_forces_vs_travel_graph(show=True)
spring.get_diameter_graph(show=True)
spring.get_diameter_vs_position_graph(show=True)
spring.create_goodman_diagram(show=True)

spring.calculate_spring_properties(nr_coils=10, pitch=None, free_length=100)

positions = [30, 40, 50, 60, 70, 80, 90, 100]
for pos in positions:
    try:
        spring.add_load_position(length=pos)
    except ValueError as e:
        print(f"Error adding load position at length {pos}: {e}")

spring_data = spring.get_spring_data()
for key, value in spring_data.items():
    print(f"{key}: {value}")

data_positions = spring.get_data_positions()
for pc in data_positions:
    print(f"Position: {pc.position}, Load: {pc.load}, Stress: {pc.stress}, Outer Diameter: {pc.outer_diameter}")

spring.get_forces_vs_position_graph(show=True)
spring.get_forces_vs_travel_graph(show=True)
spring.get_diameter_graph(show=True)
spring.get_diameter_vs_position_graph(show=True)
spring.create_goodman_diagram(show=True)

print("🎉 Test completed successfully!")
