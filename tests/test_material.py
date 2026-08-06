import shutil

import pytest

from springcalc import Material
from springcalc.pymodels import material as material_module


@pytest.fixture
def isolated_material_dir(tmp_path, monkeypatch):
    """Redirect Material's csv lookups to a throwaway copy so tests never touch the real materials.csv"""
    real_dir = material_module.get_material_dir()
    shutil.copy(f"{real_dir}/materials.csv", tmp_path / "materials.csv")

    monkeypatch.setattr(material_module, "get_material_dir", lambda: str(tmp_path))
    monkeypatch.setattr(material_module, "get_materials_csv_path", lambda: str(tmp_path / "materials.csv"))

    return tmp_path


def test_create_material_registers_and_returns_instance(isolated_material_dir):
    material = Material.create_material(
        material_name="CustomSteel",
        young_modulus="210000 MPa",
        shear_modulus=81000,  # plain numbers are assumed to be in MPa
        elastic_limit_factor=0.5,
        poisson_coef=0.3,
        description="Custom steel for a special order",
        RMa_data=[(2.0, 1500, 1700), (1.0, 1600, 1800)],
    )

    assert material.material_name == "CustomSteel"
    assert material.young_modulus.magnitude == 210000
    assert material.RMa_file == "CustomSteel_RMa.csv"
    assert "CustomSteel" in material_module.get_available_materials()

    # The material is now persisted, so it can be loaded again like any built-in one
    reloaded = Material(material_name="CustomSteel")
    assert reloaded.shear_modulus.magnitude == 81000

    # RMa_data was written sorted by ascending diameter
    rma_path = isolated_material_dir / "CustomSteel_RMa.csv"
    assert rma_path.exists()
    assert rma_path.read_text().splitlines()[1].startswith("1.0")


def test_create_material_rejects_duplicates_unless_overwrite(isolated_material_dir):
    Material.create_material("CustomSteel", "210000 MPa", 81000, 0.5, 0.3)

    with pytest.raises(ValueError):
        Material.create_material("CustomSteel", "210000 MPa", 81000, 0.5, 0.3)

    overwritten = Material.create_material(
        "CustomSteel", "220000 MPa", 81000, 0.5, 0.3, overwrite=True
    )
    assert overwritten.young_modulus.magnitude == 220000


if __name__ == "__main__":
    test_create_material_registers_and_returns_instance()
    test_create_material_rejects_duplicates_unless_overwrite()
