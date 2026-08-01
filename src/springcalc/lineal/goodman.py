import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pydantic import BaseModel, computed_field, field_validator
from ..pymodels.wire_characteristics import WireCharacteristics
from ..pymodels.material import Material
from springcalc.regresiones.factor_f.usar_modelo_factor_f import ModelFactorF
from math import log10
import io
import base64
from pint import Quantity
from ..pymodels.units import ureg
from .plotting import interactive_backend

class GoodmanData(BaseModel):
    """Data model for the Goodman diagram - validation and data only"""
    material: Material
    diameter: float
    load_type: str = "axial"
    cycles: int = 1e6  # Number of cycles for fatigue analysis, default 1 million

    @field_validator('diameter', mode='before')
    @classmethod
    def validate_diameter(cls, v):
        if isinstance(v, Quantity):
            return float(v.to('mm').magnitude)
        if isinstance(v, (int, float)):
            return float(v)
        return float(ureg(v).to('mm').magnitude)

    @computed_field
    @property
    def wire_characteristics(self) -> WireCharacteristics:
        """Wire characteristics computed automatically"""
        return WireCharacteristics(material=self.material, wire_diameter=self.diameter)


class GoodmanAnalyzer:
    """Service for Goodman analysis - business logic and calculations"""

    def __init__(self, data: GoodmanData, shot_peening: bool = False):
        self.data = data
        self.wire_char = data.wire_characteristics
        self.shot_peening = shot_peening
        self._calculate_factors()

    def _calculate_factors(self):
        """Calculate all strength factors according to Shigley"""
        # 1. Ultimate tensile strength (RMa_min) of the material
        self.Sut = self.wire_char.RMa_min

        # 2. Maximum shear strength (Ssu) - approximated as 0.75 * RMa_min for steels
        self.Ssu = 0.67 * self.Sut

        # 4. Uncorrected shear fatigue limit (Sse')
        # For steel springs, Sse' ≈ 0.5 * Sut is often used for infinite life
        self.Sse_prime = self.wire_char.material.elastic_limit_factor * self.Sut

        # Shigley Mechanical Engineering Design, 9th edition, section 6-8, p. 274
        # Calculation of the fatigue-strength correction factors (Marin factors)
        # surface factor
        if self.shot_peening:
            # Shot peening improves fatigue strength, so a correction factor of 1 can be used
            self.k_a = 1
        else:
            self.k_a = 4.51 * self.Sut**(-0.265)

        # size factor
        if self.data.load_type in ["torsion", "flexion"]:
            self.k_b = 0.879 * (self.data.diameter / 25.4)**(-0.107)
        else:
            self.k_b = 1

        # load factor
        if self.data.load_type == "flexion":
            self.k_c = 1.0
        elif self.data.load_type == "axial":
            self.k_c = 0.85
        else:
            self.k_c = 0.59

        # temperature factor
        self.k_d = 1.0
        # reliability factor
        self.k_e = 1.0
        # fatigue factor
        factor_f_model = ModelFactorF()
        self.factor_f = factor_f_model.predict(self.Ssu)
        if self.data.cycles <= 1e3:
            self.Ssf_prime = self.Sut * self.data.cycles**(log10(self.factor_f)/3)  # Approximation for low cycle counts
        else:
            if self.data.cycles > 1e6:
                cycles = 1e6  # Cap at 1 million cycles for the prediction
            else:
                cycles = self.data.cycles
            a = (self.factor_f  * self.Sut)**2 /  self.Sse_prime
            b = -log10(self.factor_f  * self.Sut / self.Sse_prime) / 3
            self.Ssf_prime = a * cycles**b
        # Corrected fatigue limit (Sse)
        # self.Sse = self.k_a * self.k_b * self.k_c * self.k_d * self.k_e *self.Sse_prime
        self.Sse = self.Sse_prime
        # Corrected shear fatigue limit (Ssf)
        self.Ssf = self.k_a * self.k_b * self.k_c * self.k_d * self.k_e * self.Ssf_prime

    @staticmethod
    def _to_mpa_float(value) -> float:
        if isinstance(value, Quantity):
            return float(value.to('MPa').magnitude)
        return float(value)

    def plot_diagram(self, sigma_max: float, sigma_min: float, show_plot: bool = True):
        """
        Plot the Goodman diagram with the operating point marked

        Args:
            sigma_max: Maximum stress of the load cycle
            sigma_min: Minimum stress of the load cycle
            show_plot: Whether to show the plot immediately

        Returns:
            matplotlib Figure for further flexibility
        """
        sigma_max = self._to_mpa_float(sigma_max)
        sigma_min = self._to_mpa_float(sigma_min)

        with interactive_backend(show_plot):
            fig, ax = plt.subplots(figsize=(10, 8))

            # Goodman diagram coordinates
            V1 = (self.Sse - self.Ssf) / (self.Ssu - self.Ssf) * self.Ssu
            Sv1 = self.Ssu - (self.Ssu - V1) * (self.Ssu + self.Ssf) / self.Ssu

            # Diagram lines
            goodman_x = [0, V1, self.Sse, V1, 0]
            goodman_y = [self.Ssf, self.Sse, self.Sse, Sv1, -self.Ssf]

            ax.plot(goodman_x, goodman_y, 'b-', linewidth=2, label='Goodman envelope')
            ax.fill(goodman_x, goodman_y, alpha=0.3, color='lightblue', label='Safe region')

            # Operating point
            mean_tension = (sigma_max + sigma_min) / 2
            amplitude = (sigma_max - sigma_min) / 2

            ax.plot([mean_tension, mean_tension], [sigma_min, sigma_max],
                    'ro-', linewidth=2, markersize=8, label='Operating point')
            ax.plot(mean_tension, mean_tension, 'go', markersize=10, label=f'σₘ={mean_tension:.1f}, σₐ={amplitude:.1f}')

            # Plot configuration
            ax.set_title(f'Goodman Diagram - Material: {self.data.material.material_name}')
            ax.set_xlabel('Mean Tension σₘ (MPa)')
            ax.set_ylabel('Alternating Tension σₐ (MPa)')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Add technical info
            info_text = f"""Goodman Factors:
        Nr of cycles: {self.data.cycles:.1e}
        Correction factors
        kₐ = {self.k_a:.3f}
        k_b = {self.k_b:.3f}
        k_c = {self.k_c:.3}
        Sut = {self.Ssu:.1f} MPa
        Se = {self.Sse:.1f} MPa
        Sf = {self.Ssf:.1f} MPa
        Security factor (Sf/Sa): {self.calculate_safety_factor(sigma_max, sigma_min):.2f}"""

            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                    verticalalignment='top', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            if show_plot:
                plt.show()

        return fig

    def get_diagram_image(self, sigma_max: float, sigma_min: float):
        """Return the Goodman diagram image in base64"""
        fig = self.plot_diagram(sigma_max, sigma_min, show_plot=False)
        # Save the diagram as base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        goodman_image = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return goodman_image

    def calculate_safety_factor(self, sigma_max: float, sigma_min: float) -> float:
        """
        Calculate the safety factor of the operating point. Shigley 6.12, p. 275

        Args:
            sigma_max: Maximum stress of the cycle
            sigma_min: Minimum stress of the cycle

        Returns:
            Safety factor
        """
        sigma_max = self._to_mpa_float(sigma_max)
        sigma_min = self._to_mpa_float(sigma_min)

        mean_tension = (sigma_max + sigma_min) / 2
        amplitude = (sigma_max - sigma_min) / 2

        # Modified Goodman equation
        if amplitude == 0:
            return float('inf')

        safety_factor = 1 / (amplitude/self.Sse + mean_tension/self.Ssu)
        return safety_factor

    def get_analysis_summary(self, sigma_max: float, sigma_min: float) -> dict:
        """
        Return a complete summary of the Goodman analysis

        Returns:
            Dictionary with all calculated parameters
        """
        sigma_max = self._to_mpa_float(sigma_max)
        sigma_min = self._to_mpa_float(sigma_min)

        return {
            'material': self.data.material.material_name,
            'diameter': self.data.diameter,
            'load_type': self.data.load_type,
            'factors': {
                'k_a': self.k_a,
                'k_b': self.k_b,
                'k_c': self.k_c,
                'k_d': self.k_d,
                'k_e': self.k_e
            },
            'strengths': {
                'Se_MPa': self.Sse,
                'Sf_MPa': self.Ssf,
                'RMa_min_MPa': self.wire_char.RMa_min,
                'RMa_max_MPa': self.wire_char.RMa_max
            },
            'operation_point': {
                'sigma_max_MPa': sigma_max,
                'sigma_min_MPa': sigma_min,
                'mean_tension_MPa': (sigma_max + sigma_min) / 2,
                'amplitude_MPa': (sigma_max - sigma_min) / 2
            },
            'safety_factor': self.calculate_safety_factor(sigma_max, sigma_min)
        }


# Backwards compatibility: keep the original interface so existing code doesn't break
class Goodman(GoodmanAnalyzer):
    """Backwards-compatibility class - uses the new architecture internally"""

    def __init__(self, material: Material, diameter: float, load_type: str = "axial", number_cycles: int = 1e6, shot_peening: bool = False):
        data = GoodmanData(material=material, diameter=diameter, load_type=load_type, cycles=number_cycles)
        super().__init__(data, shot_peening=shot_peening)

    def plot_goodman_graph(self, sigma_max: float, sigma_min: float):
        """Original method kept for backwards compatibility"""
        return self.plot_diagram(sigma_max, sigma_min, show_plot=True)

    def get_goodman_graph(self, sigma_max: float, sigma_min: float):
        """Original method kept for backwards compatibility"""
        return self.plot_diagram(sigma_max, sigma_min, show_plot=False)
