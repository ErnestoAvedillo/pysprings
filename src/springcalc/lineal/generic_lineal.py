from typing import Callable, Optional
from pint import Quantity
import numpy as np
from pydantic import ConfigDict, field_validator
from ..pymodels.units import ureg
from .constants import WAHL_FACTOR_CONSTANTS, COMPRESSION_SPRING_END_TYPES
from ..pymodels.wire_characteristics import WireCharacteristics
from typing import Optional
from pint import Quantity
from ..pymodels.units import ureg
from pydantic import field_validator, ConfigDict
import numpy as np
from scipy.integrate import quad
from scipy.optimize import fsolve

# (Keep your other imports: ureg, WireCharacteristics, Material, etc.)


class VariableLinealSpring(WireCharacteristics):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    # --- Base parameters of the generic spring ---
    free_length: Quantity = 0.0 * ureg.mm
    nr_coils: float = 0.0
    nr_active_coils: float = 0.0
    shot_peening: bool = False
    coating: Optional[str] = None
    spring_index: float = 0.0  # Note: for variable geometries this index varies locally.
    spring_constant: Quantity = 0.0 * ureg.N / ureg.mm

    # --- NEW: functional attributes for variable geometry ---
    # Store functions that receive the height 'h' (Quantity) and return a Quantity
    f_mean_diameter: Callable[[Quantity], Quantity] = lambda h: 0.0 * ureg.mm
    f_pitch: Callable[[Quantity], Quantity] = lambda h: 0.0 * ureg.mm

    # Keep physical bounds for quick initializations
    mean_diameter_init: Quantity = 0.0 * ureg.mm
    pitch_constant: Quantity = 0.0 * ureg.mm
    wire_length: Quantity = 0.0 * ureg.mm
    type_of_end: str = "ground"
    type_conforming: str = "cold"
    theta_max: float = 0.0  # Total helix rotation angle (radians)

    # --- Your validators stay the same (trimmed here for brevity) ---
    @field_validator('free_length', mode='before')
    @classmethod
    def validate_dimensions(cls, v):
        if v is not None:
            if isinstance(v, Quantity):
                return v.to('mm')
            return float(v) * ureg.mm
        return v

    def __init__(self, material, wire_diameter: float, **data):
        data.update({'material': material, 'wire_diameter': wire_diameter})
        super().__init__(**data)

        # By default, if no custom functions are given, initialize as a constant linear spring
        if 'f_mean_diameter' not in data:
            self.f_mean_diameter = lambda h: self.mean_diameter_init
        if 'f_pitch' not in data:
            self.f_pitch = lambda h: self.pitch_constant

    def establish_geometrical_function(self, func_D: Callable[[Quantity], Quantity], func_p: Callable[[Quantity], Quantity]):
        """Allows injecting any variable geometry into the spring"""
        self.f_mean_diameter = func_D
        self.f_pitch = func_p

    def calculate_spring_index_local(self, h: Quantity) -> float:
        """The spring index now depends on which part (h) of the spring you measure"""
        D_local = self.f_mean_diameter(h)
        return float(D_local.to('mm').magnitude / self.wire_diameter.to('mm').magnitude)

    def calculate_theta_max(self) -> float:
        """
        Determines theta_max by integrating: d_theta = (2*pi / p(h)) * dh
        from h = 0 to free_length.
        """
        H_val = self.free_length.to('mm').magnitude

        # Integrand function: extracts the magnitude in mm of the local pitch
        def integrand(h_mm):
            local_pitch = self.f_pitch(h_mm * ureg.mm).to('mm').magnitude
            if local_pitch <= 0:
                raise ValueError("The pitch at any point of h must be greater than zero.")
            return (2 * np.pi) / local_pitch

        theta_max, _ = quad(integrand, 0, H_val)
        self.theta_max = theta_max
        # Update the total number of coils
        self.nr_coils = theta_max / (2 * np.pi)
        return self.theta_max

    def get_h_theta_development(self, num_points=500):
        """
        Solves the correspondence between the angle theta and the height h.
        Returns numpy arrays in millimeters.
        """
        if self.theta_max == 0:
            self.calculate_theta_max()

        thetas = np.linspace(0, self.theta_max, num_points)
        zs = np.zeros(num_points)

        # Numerically solve the cumulative integral for each angle
        for i, theta in enumerate(thetas):
            if i == 0:
                zs[i] = 0.0
                continue

            def equation(z_test):
                # fsolve passes z_test as a 1-element array; quad's bounds need a plain scalar.
                z_val = float(np.atleast_1d(z_test)[0])
                # Integral from 0 to z_test of (2*pi / p(h)) dh
                val, _ = quad(lambda h: (2 * np.pi) / self.f_pitch(h * ureg.mm).to('mm').magnitude, 0, z_val)
                return val - theta

            # Find the root (initial guess = previous point)
            zs[i] = fsolve(equation, zs[i-1])[0]

        return thetas, zs


    def calculate_wire_length(self, num_points=500) -> Quantity:
        """Calculate the wire length by integrating the arc-length differential (ds)"""
        thetas, zs = self.get_h_theta_development(num_points)

        # Get diameters at each z step
        Ds = np.array([self.f_mean_diameter(z * ureg.mm).to('mm').magnitude for z in zs])
        radii = Ds / 2.0

        # 3D cartesian coordinates of the axis
        xs = radii * np.cos(thetas)
        ys = radii * np.sin(thetas)

        # Numerical derivatives with respect to theta
        dtheta = thetas[1] - thetas[0]
        dx_dtheta = np.gradient(xs, dtheta)
        dy_dtheta = np.gradient(ys, dtheta)
        dz_dtheta = np.gradient(zs, dtheta)

        # ds = sqrt( dx^2 + dy^2 + dz^2 )
        ds = np.sqrt(dx_dtheta**2 + dy_dtheta**2 + dz_dtheta**2)

        # Total integrated length
        L_mm = np.trapezoid(ds, thetas)
        self.wire_length = L_mm * ureg.mm
        return self.wire_length



    def calculate_spring_constant(self, num_points=500) -> Quantity:
        """
        Calculate the equivalent spring stiffness (K) considering the coils in series.
        1/K = integral_0^theta_max [ 8 * D(theta)^3 / (G * d^4 * 2*pi) ] dtheta
        """
        thetas, zs = self.get_h_theta_development(num_points)
        Ds = np.array([self.f_mean_diameter(z * ureg.mm).to('mm').magnitude for z in zs])

        d_val = self.wire_diameter.to('mm').magnitude
        # Access the material's shear modulus (ensure it's in MPa or N/mm²)
        G_val = self.material.shear_modulus.to('N/mm**2').magnitude

        # Integrand function for the local flexibility (1/dK)
        local_flexibility = (8 * Ds**3) / (G_val * (d_val**4) * 2 * np.pi)

        # Numerical integration using the trapezoidal rule
        total_flexibility = np.trapezoid(local_flexibility, thetas)

        K_val = 1.0 / total_flexibility  # N/mm
        self.spring_constant = K_val * (ureg.N / ureg.mm)
        return self.spring_constant

    def simulate_progressive_compression(self, max_deflection: Quantity, steps: int = 100, num_points: int = 500):
        """
        Simulates step-by-step compression accounting for oblique contact between coils.
        Returns the force vs. deflection curve and the evolution of the instantaneous stiffness.
        """
        # 1. Get the initial free-state (unloaded) trajectory
        thetas, zs_free = self.get_h_theta_development(num_points)
        Ds = np.array([self.f_mean_diameter(z * ureg.mm).to('mm').magnitude for z in zs_free])
        radii = Ds / 2.0

        d_val = self.wire_diameter.to('mm').magnitude
        G_val = self.material.shear_modulus.to('N/mm**2').magnitude

        # We'll store the compression state at each step
        deflection_history = []
        force_history = []
        stiffness_history = []

        # Angular step for one full turn (to compare adjacent coils)
        # Find how many discretization points equal 2*pi radians
        dtheta = thetas[1] - thetas[0]
        points_per_turn = int(round((2 * np.pi) / dtheta))

        # Initialize the accumulated force and deformation
        current_force = 0.0 # Newtons
        # Deformation of each point along the z axis
        delta_y = np.zeros_like(zs_free)

        target_max_deflection = max_deflection.to('mm').magnitude
        deflection_step = target_max_deflection / steps

        for step in range(steps + 1):
            current_deflection = step * deflection_step

            # --- OBLIQUE CONTACT DETECTION ---
            # Build a mask of active zones (1.0 = active, 0.0 = collided/locked)
            is_active = np.ones_like(thetas)

            for i in range(len(thetas) - points_per_turn):
                # Index of the adjacent upper coil
                i_sup = i + points_per_turn

                # Current vertical distance in mm
                z_inf_actual = zs_free[i] - delta_y[i]
                z_sup_actual = zs_free[i_sup] - delta_y[i_sup]
                Pz_actual = abs(z_sup_actual - z_inf_actual)

                # Radius difference (variable geometry)
                delta_R = abs(radii[i_sup] - radii[i])

                # Collision condition
                if delta_R < d_val:
                    # Oblique physical collision limit
                    Pz_limite = np.sqrt(d_val**2 - delta_R**2)
                    if Pz_actual <= Pz_limite:
                        # If they collide, both sections and everything in between are deactivated
                        is_active[i:i_sup+1] = 0.0
                else:
                    # If delta_R >= d, there is telescoping. No direct collision above,
                    # but we need to watch whether it reaches the spring's floor plane once fully flattened.
                    pass

            # --- INSTANTANEOUS STIFFNESS CALCULATION (K_inst) ---
            # Local differential flexibility: if not active, its flexibility is 0 (infinite stiffness)
            local_flexibility = (8 * Ds**3) / (G_val * (d_val**4) * 2 * np.pi)
            active_local_flexibility = local_flexibility * is_active

            total_flex = np.trapezoid(active_local_flexibility, thetas)

            if total_flex <= 1e-9:
                # The spring has reached full lock-up (solid height)
                K_inst = float('inf')
            else:
                K_inst = 1.0 / total_flex

            # --- UPDATE FORCE AND DEFORMATION ---
            if step > 0:
                # dF = K_inst * d_deflection
                force_increment = K_inst * deflection_step if K_inst != float('inf') else 0.0
                current_force += force_increment

                # Distribute the differential deformation locally.
                # The more flexible zones (larger diameter or active) deform more.
                if K_inst != float('inf'):
                    # Local deformation proportional to the local flexibility
                    deformation_factor = active_local_flexibility / total_flex
                    delta_y += deformation_factor * deflection_step

            deflection_history.append(current_deflection)
            force_history.append(current_force)
            stiffness_history.append(K_inst)

            if K_inst == float('inf'):
                # If the spring is fully locked, end the simulation
                break

        return (np.array(deflection_history) * ureg.mm,
                np.array(force_history) * ureg.N,
                np.array(stiffness_history) * (ureg.N / ureg.mm))
