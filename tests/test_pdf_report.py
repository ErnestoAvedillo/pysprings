import os
from pathlib import Path

from springcalc.pymodels.material import Material
from springcalc.lineal.compresion import CompressionSpring
from springcalc.report import SpringPDFReport


def _build_spring():
    material = Material(material_name="SL")
    spring = CompressionSpring(material=material, wire_diameter=2.5)
    spring.set_diameter(outer_diameter=30)
    spring.calculate_spring_properties(nr_coils=None, pitch=20, free_length=100)
    for pos in [30, 40, 50, 60, 70, 80, 90, 100]:
        spring.add_load_position(length=pos)
    return spring


def test_pdf_report_generates_file(tmp_path: Path):
    spring = _build_spring()
    report = SpringPDFReport(spring, title="Test Spring Report")

    output_path = str(tmp_path / "spring_report.pdf")
    result_path = report.build(output_path)

    assert result_path == output_path
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    with open(output_path, "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_pdf_report_without_positions(tmp_path: Path):
    """The report must still build even if no load positions were added."""
    material = Material(material_name="SL")
    spring = CompressionSpring(material=material, wire_diameter=2.5)
    spring.set_diameter(outer_diameter=30)
    spring.calculate_spring_properties(nr_coils=None, pitch=20, free_length=100)

    report = SpringPDFReport(spring)
    output_path = str(tmp_path / "empty_report.pdf")
    report.build(output_path)

    assert os.path.exists(output_path)


def test_goodman_diagram_without_positions():
    """Goodman generation should report a clear, intentional error for empty position data."""
    material = Material(material_name="SL")
    spring = CompressionSpring(material=material, wire_diameter=2.5)
    spring.set_diameter(outer_diameter=30)
    spring.calculate_spring_properties(nr_coils=None, pitch=20, free_length=100)

    result = spring.create_goodman_diagram(show=False)

    assert "error" in result
    assert "no load positions" in result["error"].lower()


if __name__ == "__main__":
    test_pdf_report_generates_file(tmp_path=Path("."))
    test_pdf_report_without_positions(tmp_path=Path("."))