import math
import numpy as np
import pytest
from pint import Quantity

from springcalc.lineal.plotting import interactive_backend
from springcalc.pymodels.material import Material
from springcalc.pymodels.units import ureg
from springcalc.lineal.generic_compression import CompressionSpringGeneral
from springcalc.lineal.animation import CompressionAnimator
from matplotlib import pyplot as plt
from springcalc.report.pdf_report import SpringPDFReport

def linear_diameter(x: Quantity,
                    min_diameter: Quantity,
                    max_diameter: Quantity,
                    free_length: Quantity) -> Quantity:
    if not isinstance(x, Quantity):
        x = x * ureg.mm
    if x.magnitude < 0 or x.magnitude > free_length.magnitude:
        raise ValueError("x must be between 0 and free_length")
    diameter = min_diameter + (max_diameter - min_diameter) * (x / free_length)
    return diameter


def linear_pitch(x: Quantity,
                 min_pitch: Quantity,
                 max_pitch: Quantity,
                 free_length: Quantity) -> Quantity:
    if not isinstance(x, Quantity):
        x = x * ureg.mm
    if x.magnitude < 0 or x.magnitude > free_length.magnitude:
        raise ValueError("x must be between 0 and free_length")
    pitch = max_pitch + (min_pitch - max_pitch) * (x / free_length)
    return pitch


def cuadratic_diameter(x: Quantity,
                       min_diameter: Quantity,
                       max_diameter: Quantity,
                       free_length: Quantity) -> Quantity:
        if not isinstance(x, Quantity):
            x = x * ureg.mm
        if x.magnitude < 0 or x.magnitude > free_length.magnitude:
            raise ValueError("x must be between 0 and free_length")
        aux = 4 * (min_diameter - max_diameter) / free_length
        diameter = aux * (x ** 2 / free_length - x) + min_diameter
        return diameter

def cuadratic_pitch(x: Quantity,
                    min_pitch: Quantity,
                    max_pitch: Quantity,
                    free_length: Quantity) -> Quantity:
    if not isinstance(x, Quantity):
        x = x * ureg.mm
    if x.magnitude < 0 or x.magnitude > free_length.magnitude:
        raise ValueError(f"x is {x} and must be between 0 and free_length")
    aux = 4 * (min_pitch - max_pitch) / free_length
    pitch = aux * (x ** 2 / free_length - x) + min_pitch
    return pitch

def test_cuadratic_diameter():
    diameter_values = []
    for i in range(130):
        x = i * ureg.mm
        diameter = cuadratic_diameter(x,
                                      min_diameter=20 * ureg.mm,
                                      max_diameter=60 * ureg.mm,
                                      free_length=130 * ureg.mm)
        diameter_values.append([i, diameter.to('mm').magnitude])
    diameter_values = np.array(diameter_values)
    with interactive_backend(plt.show):
        plt.plot(diameter_values[:, 0], diameter_values[:, 1])
        plt.xlabel("Position (mm)")
        plt.ylabel("Diameter (mm)")
        plt.title("Variable Diameter")
        plt.show()
    pitch_values = []
    for i in range(130):
        x = i * ureg.mm
        pitch = cuadratic_pitch(x,
                                min_pitch=2.5 * ureg.mm,
                                max_pitch=5.0 * ureg.mm,
                                free_length=130 * ureg.mm)
        pitch_values.append([i, pitch.to('mm').magnitude])
    pitch_values = np.array(pitch_values)
    with interactive_backend(plt.show):
        plt.plot(pitch_values[:, 0], pitch_values[:, 1])
        plt.xlabel("Position (mm)")
        plt.ylabel("Pitch (mm)")
        plt.title("Variable Pitch")
        plt.show()

    material = Material(material_name="SH")
    spring = CompressionSpringGeneral(material=material, wire_diameter=2.0)

    spring.set_geometry(func_D=lambda x: cuadratic_diameter(x,
                                                           min_diameter=20 * ureg.mm,
                                                           max_diameter=60 * ureg.mm,
                                                           free_length=130 * ureg.mm),
                        func_p=lambda x: cuadratic_pitch(x,
                                                         min_pitch=2.5 * ureg.mm,
                                                         max_pitch=5.0 * ureg.mm,
                                                         free_length=130 * ureg.mm),
                        free_length=130 * ureg.mm)
    spring.calculate_spring_properties()
    spring_data = spring.get_spring_data()
    print(f"✅ Progressive-pitch CompressionSpringGeneral test, data of the generic class:")
    for key, value in spring_data.items():
        print(f"{key}: {value}")
    positions = [120, 100]
    for pos in positions:
        spring.add_load_position(length=pos * ureg.mm)

    deflection, force, stiffness = spring.simulate_progressive_compression(
        max_deflection=40 * ureg.mm, steps=20
    )

    # get_progressive_pitch_graph returns a base64 PNG (same convention
    # as CompressionSpring's other graph methods, for embedding in HTML/PDF).
    # For local debugging, decode it and write it to disk to look at it,
    # since plt.show() can't open a window under the "Agg" backend.
    plot_data = spring.get_progressive_compression_graph(deflection, force, show=True)
    spring_data = spring.get_3d_plot(show=True)
    report = SpringPDFReport(spring=spring, title="Variable Diameter and Pitch Spring Report")
    report.build(output_path="variable_diameter_pitch_spring_report.pdf")


def test_linear_diameter():
    diameter_values = []
    for i in range(130):
        x = i * ureg.mm
        diameter = linear_diameter(x,
                                   min_diameter=20 * ureg.mm,
                                   max_diameter=60 * ureg.mm,
                                   free_length=130 * ureg.mm)
        print(f"x: {x}, diameter: {diameter}")
        diameter_values.append([i, diameter.to('mm').magnitude])
    diameter_values = np.array(diameter_values)
    with interactive_backend(plt.show):
        plt.plot(diameter_values[:, 0], diameter_values[:, 1])
        plt.xlabel("Position (mm)")
        plt.ylabel("Diameter (mm)")
        plt.title("Variable Diameter")
        plt.show()

    material = Material(material_name="SH")
    spring = CompressionSpringGeneral(material=material, wire_diameter=2.0)
    spring.set_geometry(func_D=lambda x: linear_diameter(x,
                                                         min_diameter=20 * ureg.mm,
                                                         max_diameter=60 * ureg.mm,
                                                         free_length=130 * ureg.mm),
                        func_p=lambda x: linear_pitch(x,
                                                      min_pitch=2.5 * ureg.mm,
                                                      max_pitch=5.0 * ureg.mm,
                                                      free_length=130 * ureg.mm),
                        free_length=130 * ureg.mm)
    spring.calculate_spring_properties()
    spring_data = spring.get_spring_data()
    print(f"✅ Linear-diameter CompressionSpringGeneral test, data of the generic class:")
    for key, value in spring_data.items():
        print(f"{key}: {value}")
    positions = [120, 100]
    for pos in positions:
        spring.add_load_position(length=pos * ureg.mm)

    deflection, force, stiffness = spring.simulate_progressive_compression(
        max_deflection=40 * ureg.mm, steps=20
    )
    plot_data = spring.get_progressive_compression_graph(deflection, force, show=True)
    spring_data = spring.get_3d_plot(show=True)
    report = SpringPDFReport(spring=spring, title="Variable Diameter and Pitch Spring Report")
    report.build(output_path="linear_diameter_pitch_spring_report.pdf")


def test_progressive_compression_animation():
    """Render the coils closing up under progressive load as an animated GIF.

    For local debugging, the GIF is written next to the test so it can be
    opened directly, since there's no "show" window for an animation the way
    there is for a static plot.
    """
    material = Material(material_name="SH")
    spring = CompressionSpringGeneral(material=material, wire_diameter=2.0)
    spring.set_geometry(func_D=lambda x: cuadratic_diameter(x,
                                                           min_diameter=20 * ureg.mm,
                                                           max_diameter=60 * ureg.mm,
                                                           free_length=130 * ureg.mm),
                        func_p=lambda x: cuadratic_pitch(x,
                                                         min_pitch=2.5 * ureg.mm,
                                                         max_pitch=5.0 * ureg.mm,
                                                         free_length=130 * ureg.mm),
                        free_length=130 * ureg.mm)
    spring.calculate_spring_properties()

    animator = CompressionAnimator(spring)
    output_path = animator.create_gif(
        max_deflection=40 * ureg.mm, output_path="progressive_compression.gif",
        steps=40, num_points=300, fps=12,
    )
    positions = [120, 100]
    for pos in positions:
        spring.add_load_position(length=pos * ureg.mm)
    print(f"✅ Progressive compression animation written to {output_path}")
    spring_data = spring.get_spring_data()
    print(f"Data of the generic class:")
    for key, value in spring_data.items():
        print(f"{key}: {value}")
    spring.get_3d_plot(show=True)
    report = SpringPDFReport(spring=spring, title="Progressive Compression Animation Report")
    report.build(output_path="progressive_compression_animation_report.pdf")


if __name__ == "__main__":
    # test_linear_diameter()
    # test_cuadratic_diameter()
    test_progressive_compression_animation()
