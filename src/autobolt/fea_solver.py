import tempfile

import build123d
import fenics
import gmsh
import meshio


def _calculate_fos_from_build123d(
    build123d_object: build123d.Shape,
    elastic_modulus: float,
    poissons_ratio: float,
    yield_strength: float,
    traction_values: list[tuple],
):
    """
    Calculate the Factor of Safety (FOS) for a given Build123d object using FEniCS.

    Parameters:
        build123d_object (build123d.Shape): The Build123d object representing the geometry
        elastic_modulus (float): Young's modulus of the material.
        poissons_ratio (float): Poisson's ratio of the material.
        yield_strength (float): Yield strength of the material.
        traction_values (list[tuple]): List of traction force vectors to apply on specified surfaces.

    Returns:
        float: The calculated Factor of Safety (FOS).
    """

    # Make a temporary directory using tempfile
    tempdir = tempfile.TemporaryDirectory()

    # Save the step file to the temporary directory
    step_file = tempdir.name + "/model.step"
    build123d.export_step(build123d_object, step_file)

    msh_file = tempdir.name + "/mesh_merged.msh"
    xdmf_file_mesh = tempdir.name + "/mesh.xdmf"
    xdmf_file_surface_tags = tempdir.name + "surface_tags.xdmf"

    # Initialize GMSH
    gmsh.initialize()

    # Import the STEP file
    gmsh.merge(step_file)

    # Synchronize CAD kernel
    gmsh.model.occ.synchronize()

    # Get all volumes and surfaces
    volumes = gmsh.model.getEntities(dim=3)
    surfaces = gmsh.model.getEntities(dim=2)

    # Assign physical groups to volumes
    for i, volume in enumerate(volumes):
        gmsh.model.addPhysicalGroup(volume[0], [volume[1]], tag=i + 1)

    # Assign physical groups to surfaces
    for i, surface in enumerate(surfaces):
        gmsh.model.addPhysicalGroup(surface[0], [surface[1]], tag=i + 1)

    surface_info = []
    for dim, s in gmsh.model.getEntities(2):
        bb = gmsh.model.occ.getBoundingBox(dim, s)
        ymin, ymax = bb[1], bb[4]
        surface_info.append((s, ymin, ymax))

    global_ymin = min(s[1] for s in surface_info)
    global_ymax = max(s[2] for s in surface_info)

    # Helper function: find the surface tag at a target Y location
    def y_face(surface_info, target_y, tol=1e-6):
        return next(
            tag
            for tag, ymin, ymax in surface_info
            if abs(ymax - ymin) < tol and abs(ymin - target_y) < tol
        )

    # Identify min Y and max Y surfaces
    trac_pos_tag = y_face(surface_info, global_ymin)
    trac_neg_tag = y_face(surface_info, global_ymax)
    zero_disp_tags = [trac_pos_tag]
    traction_tags = [trac_neg_tag]

    gmsh.model.occ.synchronize()

    # Generate the mesh
    gmsh.model.mesh.generate(3)

    gmsh.model.mesh.removeDuplicateNodes()

    # Save the mesh to a .msh file
    gmsh.write(msh_file)

    # Finalize GMSH
    gmsh.finalize()

    # Read the .msh file using meshio
    msh = meshio.read(msh_file)

    # Utility function to extract specific cell types
    def create_mesh(mesh, cell_type, prune_z=False):
        cells = mesh.get_cells_type(cell_type)
        cell_data = mesh.get_cell_data("gmsh:physical", cell_type)
        points = mesh.points[:, :2] if prune_z else mesh.points
        out_mesh = meshio.Mesh(
            points=points,
            cells={cell_type: cells},
            cell_data={"name_to_read": [cell_data]},
        )
        return out_mesh

    # Write the volumetric mesh (tetrahedrons) to mesh.xdmf
    tetra_mesh = create_mesh(msh, "tetra")
    meshio.write(xdmf_file_mesh, tetra_mesh)

    # Write the surface tags (triangles) to surface_tags.xdmf
    triangle_mesh = create_mesh(msh, "triangle")
    meshio.write(xdmf_file_surface_tags, triangle_mesh)

    # Step 2: FEniCS Simulation
    mesh = fenics.cpp.mesh.Mesh()
    with fenics.cpp.io.XDMFFile(xdmf_file_mesh) as infile:
        infile.read(mesh)

    # Load the surface tags in FEniCS
    mvc = fenics.MeshValueCollection("size_t", mesh, 2)
    with fenics.cpp.io.XDMFFile(xdmf_file_surface_tags) as infile:
        infile.read(mvc, "name_to_read")
    mf = fenics.cpp.mesh.MeshFunctionSizet(mesh, mvc)

    # Define function space for displacement
    V = fenics.VectorFunctionSpace(mesh, "CG", 2)
    W = fenics.FunctionSpace(mesh, "CG", 2)

    # Define boundary conditions
    bcs = [
        fenics.DirichletBC(V, fenics.Constant((0.0, 0.0, 0.0)), mf, tag)
        for tag in zero_disp_tags
    ]

    # Define material properties
    mu = elastic_modulus / (2.0 * (1.0 + poissons_ratio))  # Shear modulus
    lmbda = (
        elastic_modulus
        * poissons_ratio
        / ((1.0 + poissons_ratio) * (1.0 - 2.0 * poissons_ratio))
    )  # First Lamé parameter

    # Define strain and stress
    def epsilon(u):
        return 0.5 * (fenics.grad(u) + fenics.grad(u).T)

    def sigma(u):
        return 2.0 * mu * epsilon(u) + lmbda * fenics.tr(epsilon(u)) * fenics.Identity(
            3
        )

    # Define variational problem
    u = fenics.TrialFunction(V)
    v = fenics.TestFunction(V)
    f = fenics.Constant((0.0, 0.0, 0.0))  # Body force (assumed zero)

    # Weak form
    a = fenics.inner(sigma(u), epsilon(v)) * fenics.dx
    ds = fenics.Measure("ds", domain=mesh, subdomain_data=mf)
    L = fenics.dot(f, v) * fenics.dx  # Start with body force term

    # Add traction forces for each specified surface
    for tag, traction in zip(traction_tags, traction_values):
        L += fenics.dot(fenics.Constant(traction), v) * ds(tag)

    # Solve the problem
    u = fenics.Function(V)
    fenics.solve(a == L, u, bcs)

    pvd_file_solution = "../../displacement.pvd"
    fenics.cpp.io.File(pvd_file_solution) << u

    # Compute von Mises stress
    s = sigma(u) - (1.0 / 3) * fenics.tr(sigma(u)) * fenics.Identity(3)
    von_Mises = fenics.project(
        fenics.sqrt(3.0 / 2.0 * fenics.inner(s, s)), W, solver_type="cg"
    )

    pvd_file_solution = "../../stress.pvd"
    fenics.cpp.io.File(pvd_file_solution) << von_Mises

    # Compute maximum von Mises stress
    max_stress = von_Mises.vector().max()

    # Compute Factor of Safety (FOS)
    FOS = yield_strength / max_stress

    return FOS
