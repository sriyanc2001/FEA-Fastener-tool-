import copy
from build123d import (
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
    Pos,
    Compound,
    Location,
    Plane,
    export_step,
    mirror
)

def create_two_plate_assembly(
    plate_length,
    plate_width,
    plate_thickness,
    num_holes,
    hole_radius,
    right_margin,
    hole_spacing,
    hole_center_y, 
    output_filename
):
    

    # Create Plate A with holes.
    with BuildPart() as bp:
        # Create a box (centered by default) and then reposition it so its bottom-left corner is at (0,0).
        Box(plate_length, plate_width, plate_thickness)
        bp.part = bp.part.move(Pos(plate_length/2, plate_width/2, 0))
        
        # Compute X-coordinates for the holes.
        x_first = plate_length - right_margin  # First hole's X position.
        x_coords = [x_first - i * hole_spacing for i in range(num_holes)]
        
        # Subtract cylinders (holes) at each computed X position and at the computed Y position.
        for x in x_coords:
            with Locations(Pos(x, hole_center_y, 0)):
                Cylinder(
                    radius=hole_radius,
                    height=plate_thickness + 1.0,  # Slight extra height for a clean subtraction.
                    mode=Mode.SUBTRACT
                )
    plateA = bp.part

    # Create Plate B as a copy of Plate A.
    plateB = copy.deepcopy(plateA)
    
    # Translate Plate B upward along Z (to sit above Plate A).
    translationZ = Location((0, 0, plate_thickness), (0, 0, 1), 0)
    plateB = plateB.locate(translationZ)

    # Mirror Plate B about the XZ plane, which reverses its Y coordinates.
    mirror_plane = Plane.XZ
    plateB_mirrored = mirror(plateB, about=mirror_plane)

    # we translate Plate B upward by twice the y_hole_absolute value.
    y_hole_absolute = hole_center_y  
    plateB_y_translation = 2 * y_hole_absolute

    # Translate Plate B in the Y direction.
    translationY = Location((0, plateB_y_translation, 0), (0, 0, 1), 0)
    plateB_final = plateB_mirrored.locate(translationY)

    # Assemble both plates.
    assembly = Compound(children=[plateA, plateB_final])

    # Export the assembly as a STEP file.
    export_step(assembly, output_filename)

    return assembly


assembly = create_two_plate_assembly(
    plate_length=200.0,
    plate_width=100.0,
    plate_thickness=10.0,
    num_holes=4,
    hole_radius=10.0,
    right_margin=53.87,
    hole_spacing=35.0,
    hole_center_y = 20,           
    output_filename="CAD_2plates.step"
)
