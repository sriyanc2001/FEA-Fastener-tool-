import autobolt
import os


def test_autobolt_functionality():

    # Example usage:
    assembly = autobolt.create_two_plate_assembly(
        plate_length_m=0.200,  # [m] length of each plate (along X)
        plate_width_m=0.100,  # [m] width of each plate (along Y)
        plate_thickness_m=0.010,  # [m] thickness of each plate (along Z)
        num_holes=4,  # number of bolt holes per plate
        hole_radius_m=0.010,  # [m] radius of bolt/hole
        edge_margin_m=0.05387,  # [m]distance from right plate edge to first hole center
        hole_spacing_m=0.035,  # [m] spacing between consecutive holes (X direction)
        hole_offset_from_bottom_m=0.020,  # [m] vertical position of hole centers (Y from bottom edge)
        plate_gap_mm=0.01,  # [mm] gap between the two plates
        output_filename="CAD_2plates.step",  # STEP file output name
    )

    print(assembly)

    fos = autobolt.calculate_fos(
        step_file="CAD_2plates.step",
        E=210e9,  # [Pa] Young's modulus for steel
        nu=0.3,  # Poisson's ratio for steel
        yield_strength=200e6,  # [Pa] Yield strength for steel
        traction_values=[(0, -1e6, 0)],  # [Pa] Applied
    )
    print(f"Calculated Factor of Safety: {fos}")
    assert fos > 0, "Factor of Safety should be positive"

    # Delete the file

    os.remove("CAD_2plates.step")
