from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from typing import Optional, List
from pint import Quantity
from .units import ureg

class LinearPosition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True,
                              validate_assignment=True)

    position: Quantity
    travel: Quantity
    load: Optional[Quantity] = None

    @field_validator('position', 'travel', mode='before')
    @classmethod
    def validate_positive_values(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('mm')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.mm
                else:
                    quantity = ureg(v).to('mm')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    @field_validator('load', mode='before')
    @classmethod
    def validate_load(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('N')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.N
                else:
                    quantity = ureg(v).to('N')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    def __str__(self):
        return (f"Position: {self.position} mm, "
                f"Travel={self.travel} mm, "
                f"Load={self.load} N")

class AngularPosition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    position: Quantity
    travel: Quantity
    load: Optional[Quantity] = None

    @field_validator('position', 'travel', mode='before')
    @classmethod
    def validate_positive_values(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('degree')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.degree
                else:
                    quantity = ureg(v).to('degree')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    @field_validator('load', mode='before')
    @classmethod
    def validate_load(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.N * ureg.mm
                else:
                    quantity = ureg(v)
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    def __str__(self):
        return (f"Position={self.position} degrees, "
                f"Deformation={self.travel} degrees, "
                f"Load={self.load} Nmm")

class LinearLoadPosition(LinearPosition):
    stress: Optional[Quantity] = None
    outer_diameter: Optional[Quantity] = None
    inner_diameter: Optional[Quantity] = None

    @field_validator('outer_diameter', 'inner_diameter', mode='before')
    @classmethod
    def validate_positive_values(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('mm')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.mm
                else:
                    quantity = ureg(v).to('mm')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    @field_validator('stress', mode='before')
    @classmethod
    def validate_quantities(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('MPa')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.MPa
                else:
                    quantity = ureg(v).to('MPa')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    def __str__(self):
        return (f"Stress={self.stress} MPa, "
                f"Outer Diameter={self.outer_diameter} mm, "
                f"Inner Diameter={self.inner_diameter} mm")

class AngularLoadPosition(AngularPosition):
    stress: Optional[Quantity] = None
    outer_diameter: Optional[Quantity] = None
    inner_diameter: Optional[Quantity] = None

    @field_validator('outer_diameter', 'inner_diameter', mode='before')
    @classmethod
    def set_diameter(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('mm')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.mm
                else:
                    quantity = ureg(v).to('mm')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    @field_validator('stress', mode='before')
    @classmethod
    def validate_stress(cls, v):
        if v is not None:
            try:
                if isinstance(v, Quantity):
                    quantity = v.to('MPa')
                elif isinstance(v, (int, float)):
                    quantity = v * ureg.MPa
                else:
                    quantity = ureg(v).to('MPa')
            except Exception as e:
                raise ValueError(f"Value '{v}' is not a valid quantity with units. Error: {e}")
            return quantity
        return v

    def __str__(self):
        return (f"Stress={self.stress} MPa, "
                f"Outer Diameter={self.outer_diameter} mm, "
                f"Inner Diameter={self.inner_diameter} mm")

class LinearPositionsTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    positions: List[LinearLoadPosition] = []

    def add_load_position(self,
                           position: float,
                           travel: float,
                           load: Optional[float] = None,
                           stress: Optional[float] = None,
                           outer_diameter: Optional[float] = None,
                           inner_diameter: Optional[float] = None):
        """Add a new position with its characteristics to the table"""
        new_position = LinearLoadPosition(
            position=position,
            travel=travel,
            load=load,
            stress=stress,
            outer_diameter=outer_diameter,
            inner_diameter=inner_diameter
        )
        self.positions.append(new_position)

    def clear_table(self):
        """Empty the positions table"""
        self.positions = []

    def __str__(self):
            """Return a human-readable representation of the positions table"""
            if not self.positions:
                return "No positions recorded."
            result = "Positions table:\n"
            for idx, pos in enumerate(self.positions, start=1):
                result += (f"Position {idx}: Load={pos.load} N,\n"
                            f"  Stress={pos.stress} MPa,\n"
                            f"  Deformation={pos.position} mm/mm,\n"
                            f"  Travel={pos.travel} mm/mm,\n"
                            f"  Outer Diameter={pos.outer_diameter} mm,\n"
                            f"  Inner Diameter={pos.inner_diameter} mm\n")
            return result

class AngularPositionsTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    positions : List[AngularLoadPosition] = []

    def add_load_position(self,
                            position: float,
                            travel: float,
                            load: Optional[float] = None,
                            stress: Optional[float] = None,
                            outer_diameter: Optional[float] = None,
                            inner_diameter: Optional[float] = None):
        """Add a new position with its characteristics to the table"""
        new_position = AngularLoadPosition(
            position=position,
            travel=travel,
            load=load,
            stress=stress,
            outer_diameter=outer_diameter,
            inner_diameter=inner_diameter
        )
        self.positions.append(new_position)

    def clear_table(self):
        """Empty the positions table"""
        self.positions = []

    def __str__(self):
        """Return a human-readable representation of the positions table"""
        if not self.positions:
            return "No positions recorded."
        result = "Positions table:\n"
        for idx, pos in enumerate(self.positions, start=1):
            result += (f"Position {idx}: Load={pos.load} Nmm,\n"
                        f"  Stress={pos.stress} MPa,\n"
                        f"  Deformation={pos.position} mm/mm,\n"
                        f"  Travel={pos.travel} mm/mm,\n"
                        f"  Outer Diameter={pos.outer_diameter} mm,\n"
                        f"  Inner Diameter={pos.inner_diameter} mm\n")

        return result
