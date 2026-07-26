from pydantic import BaseModel, field_validator, model_validator, ConfigDict, ValidationInfo
import pandas as pd
import os
from typing import List, Optional
from pint import Quantity
from .units import ureg

def get_materials_dataframe() -> pd.DataFrame:
    """Get the full materials DataFrame from materials.csv"""
    # Get the CSV file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    material_dir = os.path.join(os.path.dirname(current_dir), 'material')
    csv_path = os.path.join(material_dir, 'materials.csv')

    try:
        df = pd.read_csv(csv_path)
        # Strip whitespace from all text columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        return df
    except Exception as e:
        print(f"Error reading materials.csv: {e}")
        return pd.DataFrame()

def get_available_materials() -> List[str]:
    """Get the list of available materials from materials.csv"""
    df = get_materials_dataframe()
    if not df.empty:
        return df['denomination'].tolist()
    return []


class Material(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    material_name: str
    young_modulus: Optional[Quantity] = None
    shear_modulus: Optional[Quantity] = None
    elastic_limit_factor: Optional[Quantity] = None
    poisson_coef: Optional[Quantity] = None
    RMa_file: Optional[str] = None

    @field_validator('material_name')
    @classmethod
    def validate_material_name(cls, v):
        """Validate that the material name is in the list of available materials"""
        available_materials = get_available_materials()
        if v not in available_materials:
            raise ValueError(f'Material "{v}" is not valid. Available materials: {", ".join(available_materials)}')
        return v

    @field_validator('young_modulus',
                     'shear_modulus',
                     'elastic_limit_factor',
                     'poisson_coef', mode='before')
    @classmethod
    def validate_positive_quantities(cls, v, info: ValidationInfo):
        """Validate that the quantities are positive and have the correct units"""
        if v is not None:
            try:
                quantity = ureg(v).to('MPa') if info.field_name in ['young_modulus', 'shear_modulus'] else ureg(v)
                if quantity.magnitude <= 0:
                    raise ValueError(f'{info.field_name} must be a positive value with valid units: Pascal (Pa) for young_modulus and shear_modulus, unitless for elastic_limit_factor, and dimensionless for poisson_coef.')
                return quantity
            except Exception as e:
                raise ValueError(f'Error validating {info.field_name}: {e}')
        return v

    @model_validator(mode='after')
    def assign_material_properties(self):
        """Automatically assign material properties based on materials.csv"""
        if self.material_name:
            df = get_materials_dataframe()
            if not df.empty:
                # Strip whitespace from column names
                df.columns = df.columns.str.strip()

                # Find the row matching the material
                material_row = df[df['denomination'] == self.material_name]

                if not material_row.empty:
                    row = material_row.iloc[0]

                    # Assign properties automatically (only if not already set and the value is not empty)
                    if self.young_modulus is None and 'young_modulus' in df.columns:
                        val = row.get('young_modulus')
                        if pd.notna(val) and str(val).strip() != '':
                            self.young_modulus = float(val) * ureg.MPa

                    if self.shear_modulus is None and 'shear_modulus' in df.columns:
                        val = row.get('shear_modulus')
                        if pd.notna(val) and str(val).strip() != '':
                            self.shear_modulus = float(val) * ureg.MPa

                    if self.elastic_limit_factor is None and 'elastic_limit_factor' in df.columns:
                        val = row.get('elastic_limit_factor')
                        if pd.notna(val) and str(val).strip() != '':
                            self.elastic_limit_factor = float(val) * ureg.dimensionless

                    if self.poisson_coef is None and 'poisson_coef' in df.columns:
                        val = row.get('poisson_coef')
                        if pd.notna(val) and str(val).strip() != '':
                            self.poisson_coef = float(val) * ureg.dimensionless

                    if self.RMa_file is None and 'RMa_file' in df.columns:
                        val = row.get('RMa_file')
                        if pd.notna(val) and str(val).strip() != '':
                            self.RMa_file = str(val).strip()

        return self
