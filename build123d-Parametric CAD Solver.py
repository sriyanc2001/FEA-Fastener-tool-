from build123d import (
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
    Pos,
    copy,
    Compound,
    Location,
    Plane,
    mirror,
    Align,
    export_step
)

def create_two_plate_assembly(
    plate_length_m,
    plate_width_m,
    plate_thickness_m,
    num_holes,
    hole_radius_m,
    edge_margin_m,
    hole_spacing_m,
    hole_offset_from_bottom_m,
    plate_gap_mm,
    output_filename
):
    # convert the gap to meters
    gap_m = plate_gap_mm * 1e-4

    # 1) Build Plate A (with through‑holes)
    with BuildPart() as bp:
        Box(plate_length_m, plate_width_m, plate_thickness_m)
        # center the box around the XY origin
        bp.part = bp.part.move(Pos(plate_length_m/2, plate_width_m/2, 0))

        # compute X‑coordinates of hole centers
        x0 = plate_length_m - edge_margin_m
        x_coords = [x0 - i * hole_spacing_m for i in range(num_holes)]
        
        # subtract each hole
        for x in x_coords:
            with Locations(Pos(x, hole_offset_from_bottom_m, 0)):
                Cylinder(
                    radius=hole_radius_m,
                    height=plate_thickness_m + 1e-3,  # +1 mm to ensure clean cut
                    mode=Mode.SUBTRACT
                )
    plateA = bp.part

    # 2) Copy Plate A → shift up by thickness+gap → mirror in Y → re‑position
    plateB = copy(plateA)
    # shift in Z by plate_thickness + gap
    plateB = plateB.locate(
        Location((0, 0, plate_thickness_m + gap_m), (0,0,1), 0)
    )
    # mirror about the XZ plane (so y→−y)
    plateB = mirror(plateB, about=Plane.XZ)
    # then translate back up in Y by 2*hole_center_y to line holes up
    plateB = plateB.locate(
        Location((0, 2*hole_offset_from_bottom_m, 0), (0,0,1), 0)
    )

    # 3) Create the bolt‑like cylinders (conformal, centered in the holes)
    bolt_height_m = 2 * plate_thickness_m + gap_m
    z_offset_m   = plate_thickness_m / 2 + gap_m / 2 # start mid‑thickness of Plate A

    with BuildPart() as bp2:
        for x in x_coords:
            with Locations(Pos(x, hole_offset_from_bottom_m, z_offset_m)):
                Cylinder(
                    radius=hole_radius_m,
                    height=bolt_height_m,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER)
                )
    bolt_cylinders = bp2.part

    # 4) Assemble
    assembly = Compound(children=[plateA, plateB, bolt_cylinders])

    # 5) Export
    export_step(assembly, output_filename)
    return assembly


# Example usage:
assembly = create_two_plate_assembly(
    plate_length_m    = 0.200,    # [m] length of each plate (along X)
    plate_width_m     = 0.100,    # [m] width of each plate (along Y)
    plate_thickness_m = 0.010,    # [m] thickness of each plate (along Z)
    num_holes         = 4,        # number of bolt holes per plate
    hole_radius_m     = 0.010,    #[m] radius of bolt/hole
    edge_margin_m    = 0.05387,  #[m]distance from right plate edge to first hole center
    hole_spacing_m    = 0.035,    #[m] spacing between consecutive holes (X direction)
    hole_offset_from_bottom_m   = 0.020,    #[m] vertical position of hole centers (Y from bottom edge)
    plate_gap_mm            = 0.01,      # [mm] gap between the two plates
    output_filename   = "CAD_2plates.step" # STEP file output name
)
