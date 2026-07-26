from pint import Quantity
from ..pymodels.units import ureg
from .generic_lineal import VariableLinealSpring


class CompressionSpringGeneral(VariableLinealSpring):
    solid_length: Quantity = 0.0 * ureg.mm

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
