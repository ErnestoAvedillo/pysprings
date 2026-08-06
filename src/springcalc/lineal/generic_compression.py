from math import pi
from typing import Optional
import io
import base64
import numpy as np
from pint import Quantity
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from ..pymodels.units import ureg
from .constants import WAHL_FACTOR_CONSTANTS, COMPRESSION_SPRING_END_TYPES, FORMING_TYPES
from ..pymodels.positions import LinearPositionsTable
from .generic_lineal import VariableLinealSpring
from .plotting import interactive_backend

COMPRESSION = 1


class CompressionSpringGeneral(VariableLinealSpring):
    solid_length: Quantity = 0.0 * ureg.mm
    positions: LinearPositionsTable = LinearPositionsTable()
    position_length: Optional[Quantity] = 0.0 * ureg.mm
    position_load: Optional[Quantity] = 0.0 * ureg.N
    position_stress: Optional[Quantity] = 0.0 * ureg.megapascal
    wahl_factor: float = 0.0
    wahl_factor_category: Optional[str] = None
    nr_active_coils: float = 0.0
    number_cycles: int = 1_000_000

    def calculate_active_coils(self) -> float:
        """
        Calculate the number of active coils, discounting the end coils that
        are ground/squared flat and don't contribute to deflection.
        """
        if self.type_conforming == FORMING_TYPES[1]:  # cold formed
            self.nr_active_coils = self.nr_coils - 2
            if self.type_of_end in [COMPRESSION_SPRING_END_TYPES[3], COMPRESSION_SPRING_END_TYPES[4]]:  # unground
                self.nr_active_coils -= 1.5
        else:  # hot formed
            self.nr_active_coils = self.nr_coils - 1.5
        if self.type_of_end in [COMPRESSION_SPRING_END_TYPES[1], COMPRESSION_SPRING_END_TYPES[2]]:  # ground
            self.nr_active_coils -= 0.3
        else:
            self.nr_active_coils -= 1.1
        return self.nr_active_coils

    def _get_active_theta_range(self) -> tuple:
        """
        Narrow the active winding range to exclude the non-deforming end
        coils, split evenly between both ends of the spring.
        """
        if self.theta_max == 0:
            self.calculate_theta_max()
        self.calculate_active_coils()
        inactive_coils = max(self.nr_coils - self.nr_active_coils, 0.0)
        theta_margin = (inactive_coils / 2) * 2 * pi
        return theta_margin, self.theta_max - theta_margin

    def calculate_spring_properties(self, num_points: int = 500) -> dict:
        """
        Calculate all derived properties, including the compression-specific
        ones (active coils, solid length, representative Wahl factor) that
        CompressionSpring also reports.
        """
        super().calculate_spring_properties(num_points=num_points)
        self.calculate_active_coils()
        self.calculate_wahl_factor_at_position(self.free_length / 2)
        self.calculate_solid_length()
        return self.get_spring_data()

    def get_spring_data(self) -> dict:
        """Return a dictionary with the main spring data, matching CompressionSpring's fields."""
        return {
            "material": self.material.material_name,
            "young_modulus": self.material.young_modulus,
            "shear_modulus": self.material.shear_modulus,
            "elastic_limit_factor": self.material.elastic_limit_factor,
            "poisson_coef": self.material.poisson_coef,
            "RMa_file": self.material.RMa_file,
            "wire_diameter": self.wire_diameter,
            "mean_diameter": self.f_mean_diameter(self.free_length / 2),
            "free_length": self.free_length,
            "nr_coils": self.nr_coils,
            "nr_active_coils": self.nr_active_coils,
            "spring_constant": self.spring_constant,
            "spring_index": self.spring_index,
            "wahl_factor": self.wahl_factor,
            "wahl_factor_category": self.wahl_factor_category,
            "solid_length": self.solid_length,
            "wire_length": self.wire_length,
            "number_cycles": self.number_cycles,
            "shot_peening": self.shot_peening,
            "coating": self.coating,
        }

    def calculate_solid_length(self) -> Quantity:
        """
        In a variable-geometry spring (such as a conical one), the coils can
        nest inside one another (telescoping).
        """
        # If the spring nests flat (very different diameters): solid_length = wire_diameter
        # If it's a standard compression spring where coils collide: solid_length = nr_coils * wire_diameter
        # Add a basic check for "nesting" or "telescoping"
        H_val = self.free_length.to('mm').magnitude
        D_start = self.f_mean_diameter(0 * ureg.mm).to('mm').magnitude
        D_end = self.f_mean_diameter(self.free_length).to('mm').magnitude
        d_wire = self.wire_diameter.to('mm').magnitude

        # If the radius difference is greater than the wire diameter per coil, it "nests"
        if abs(D_start - D_end) >= (self.nr_coils * d_wire):
            # Perfect telescoping limit case (every coil fits inside another)
            self.solid_length = d_wire * ureg.mm
        else:
            # Conventional case: coils stack on top of one another
            self.solid_length = self.nr_coils * self.wire_diameter

        return self.solid_length

    def calculate_load_at_position(self, length: Quantity, spring_class: int = COMPRESSION) -> Quantity:
        """Calculate the load at a given position using the overall spring constant."""
        if self.spring_constant == 0:
            self.calculate_spring_constant()
        self.position_length = length
        self.position_load = spring_class * self.spring_constant * (self.free_length - self.position_length)
        self.calculate_stress_at_position(self.position_load)
        return self.position_load

    def calculate_wahl_factor_at_position(self, length: Quantity):
        """Calculate the Wahl factor using the local spring index at a given position."""
        spring_index = self.calculate_spring_index_local(length)
        self.wahl_factor = (4 * spring_index - 1) / (4 * spring_index - 4) + 0.615 / spring_index
        if spring_index < WAHL_FACTOR_CONSTANTS['red'][1]:
            self.wahl_factor_category = 'red'
        elif spring_index < WAHL_FACTOR_CONSTANTS['orange'][1]:
            self.wahl_factor_category = 'orange'
        else:
            self.wahl_factor_category = 'green'
        return self.wahl_factor, self.wahl_factor_category

    def calculate_stress_at_position(self, load: Quantity) -> Quantity:
        """Calculate the stress in the spring wire at a given predefined position."""
        self.calculate_wahl_factor_at_position(self.position_length)
        local_diameter = self.f_mean_diameter(self.position_length)
        self.position_stress = (8 * local_diameter * load) / (pi * self.wire_diameter**3) * self.wahl_factor
        return self.position_stress

    def calculate_outer_diameter_at_position(self, length: Quantity) -> Quantity:
        """Calculate the spring outer diameter at a given position."""
        self.position_length = length
        local_diameter = self.f_mean_diameter(length)
        outer_diameter = local_diameter + self.wire_diameter + \
            local_diameter * self.material.poisson_coef * \
            (self.free_length - self.position_length) / self.free_length
        return outer_diameter

    def add_load_position(self, length: Quantity):
        """Add a load position to the positions table."""
        try:
            if length < self.solid_length:
                raise ValueError("The position cannot be smaller than the spring's solid length")
            load = self.calculate_load_at_position(length)
            stress = self.calculate_stress_at_position(load)
            outer_diameter = self.calculate_outer_diameter_at_position(length)
        except ValueError as e:
            raise ValueError(f"Error adding load position at length {length}: {e}")
        self.positions.add_load_position(
            position=self.position_length,
            travel=self.free_length - self.position_length,
            load=load,
            stress=stress,
            outer_diameter=outer_diameter,
            inner_diameter=max(outer_diameter - 2 * self.wire_diameter, 0 * ureg.mm)
        )

    def empty_tables(self):
        """Clear the positions table."""
        self.positions.clear_table()

    def get_progressive_compression_graph(self, deflection: Quantity, force: Quantity, show: bool = False) -> str:
        """Plot the deflection/force curve from simulate_progressive_compression.

        Returns a base64-encoded PNG, ready to embed in HTML or a PDF report
        (same convention as CompressionSpring's graph methods). The module is
        pinned to the non-interactive "Agg" backend for headless web/PDF use,
        so show=True temporarily switches to a real interactive backend for
        this call (blocking until the window is closed) and restores "Agg"
        afterwards.
        """
        deflection_mm = deflection.to('mm').magnitude
        force_n = force.to('N').magnitude

        with interactive_backend(show):
            plt.figure()
            plt.plot(deflection_mm, force_n, marker='o')
            plt.title('Progressive Compression Simulation')
            plt.xlabel('Deflection (mm)')
            plt.ylabel('Force (N)')
            plt.grid(True)
            if show:
                plt.show()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            plot_data = base64.b64encode(buf.read()).decode()
            buf.close()
            plt.close()

        return plot_data

    def get_3d_plot(self, num_points: int = 500, show: bool = False, isometric: bool = True) -> str:
        """Render the spring's helical centerline in 3D.

        Reuses the same (theta, z, diameter) development as calculate_wire_length,
        so variable diameter/pitch geometries show up as a non-uniform helix.
        Returns a base64-encoded PNG (same convention as the other graph methods).
        Defaults to an orthographic isometric view, matching how spring drawings
        are conventionally presented.
        """
        thetas, zs = self.get_h_theta_development(num_points)
        Ds = np.array([self.f_mean_diameter(z * ureg.mm).to('mm').magnitude for z in zs])
        radii = Ds / 2.0

        xs = radii * np.cos(thetas)
        ys = radii * np.sin(thetas)

        with interactive_backend(show):
            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')
            ax.plot(xs, ys, zs)
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_zlabel('Z (mm)')
            ax.set_title('Spring 3D Model')
            ax.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))
            if isometric:
                ax.set_proj_type('ortho')
                ax.view_init(elev=35.264, azim=45)
            if show:
                plt.show()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            plot_data = base64.b64encode(buf.read()).decode()
            buf.close()
            plt.close()

        return plot_data
