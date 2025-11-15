from .fea_solver import calculate_fos_from_build123d
from .parametric_cad_solver import create_two_plate_assembly


def calculate_fos(
    plate_length_m: float,
    plate_width_m: float,
    plate_thickness_m: float,
    num_holes: int,
    hole_radius_m: float,
    edge_margin_m: float,
    hole_spacing_m: float,
    hole_offset_from_bottom_m: float,
    plate_gap_mm: float,
    E: float,
    nu: float,
    yield_strength: float,
    traction_values: list[tuple],
) -> float:
    # Create the two-plate assembly
    assembly = create_two_plate_assembly(
        plate_length_m,
        plate_width_m,
        plate_thickness_m,
        num_holes,
        hole_radius_m,
        edge_margin_m,
        hole_spacing_m,
        hole_offset_from_bottom_m,
        plate_gap_mm,
    )

    # Calculate the factor of safety
    fos = calculate_fos_from_build123d(
        build123d_object=assembly,
        E=E,
        nu=nu,
        yield_strength=yield_strength,
        traction_values=traction_values,
    )

    # Return the factor of safety
    return fos
