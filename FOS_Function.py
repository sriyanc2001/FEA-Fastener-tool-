from fenics import *
import gmsh
import meshio

def calculate_fos(step_file, E, nu, yield_strength, zero_disp_tags, traction_tags, traction_values):
    
    
    msh_file = "mesh.msh"
    xdmf_file_mesh = "mesh.xdmf"
    xdmf_file_surface_tags = "surface_tags.xdmf"

    # Initialize GMSH
    gmsh.initialize()

    # Import the STEP file
    gmsh.merge(step_file)

    # Get all volumes and surfaces
    volumes = gmsh.model.getEntities(dim=3)
    surfaces = gmsh.model.getEntities(dim=2)

    # Assign physical groups to volumes
    for i, volume in enumerate(volumes):
        gmsh.model.addPhysicalGroup(volume[0], [volume[1]], tag=i + 1)

    # Assign physical groups to surfaces
    for i, surface in enumerate(surfaces):
        gmsh.model.addPhysicalGroup(surface[0], [surface[1]], tag=i + 1)

    # Synchronize the model
    gmsh.model.occ.synchronize()

    # Generate the mesh
    gmsh.model.mesh.generate(3)

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
        out_mesh = meshio.Mesh(points=points, cells={cell_type: cells}, cell_data={"name_to_read": [cell_data]})
        return out_mesh

    # Write the volumetric mesh (tetrahedrons) to mesh.xdmf
    tetra_mesh = create_mesh(msh, "tetra")
    meshio.write(xdmf_file_mesh, tetra_mesh)

    # Write the surface tags (triangles) to surface_tags.xdmf
    triangle_mesh = create_mesh(msh, "triangle")
    meshio.write(xdmf_file_surface_tags, triangle_mesh)

    # Step 2: FEniCS Simulation
    
    # Load the mesh
    mesh = Mesh()
    with XDMFFile(xdmf_file_mesh) as infile:
        infile.read(mesh)

    # Load the surface tags in FEniCS
    mvc = MeshValueCollection("size_t", mesh, 2)
    with XDMFFile(xdmf_file_surface_tags) as infile:
        infile.read(mvc, "name_to_read")
    mf = cpp.mesh.MeshFunctionSizet(mesh, mvc)

    # Define function space for displacement
    V = VectorFunctionSpace(mesh, "CG", 2)
    W = FunctionSpace(mesh, "CG", 2)

    # Define boundary conditions
    bcs = [DirichletBC(V, Constant((0.0, 0.0, 0.0)), mf, tag) for tag in zero_disp_tags]

    # Define material properties
    mu = E / (2.0 * (1.0 + nu))  # Shear modulus
    lmbda = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))  # First Lamé parameter

    # Define strain and stress
    def epsilon(u):
        return 0.5 * (grad(u) + grad(u).T)

    def sigma(u):
        return 2.0 * mu * epsilon(u) + lmbda * tr(epsilon(u)) * Identity(3)

    # Define variational problem
    u = TrialFunction(V)
    v = TestFunction(V)
    f = Constant((0.0, 0.0, 0.0))  # Body force (assumed zero)

    # Weak form
    a = inner(sigma(u), epsilon(v)) * dx
    ds = Measure("ds", domain=mesh, subdomain_data=mf)
    L = dot(f, v) * dx  # Start with body force term

    # Add traction forces for each specified surface
    for tag, traction in zip(traction_tags, traction_values):
        L += dot(Constant(traction), v) * ds(tag)
    
    # Solve the problem
    u = Function(V)
    solve(a == L, u, bcs)

    pvd_file_solution = "displacement.pvd"
    File(pvd_file_solution) << u

    # Compute von Mises stress
    s = sigma(u) - (1.0 / 3) * tr(sigma(u)) * Identity(3)
    von_Mises = project(sqrt(3.0 / 2.0 * inner(s, s)), W, solver_type="cg")

    pvd_file_solution = "stress.pvd"
    File(pvd_file_solution) << von_Mises

    # Compute maximum von Mises stress
    max_stress = von_Mises.vector().max()

    # Compute Factor of Safety (FOS)
    FOS =  yield_strength/max_stress

    return FOS

# Input parameters
step_file = "/home/sriyan/Assem2.STEP"
E = 210e9
nu = 0.3
yield_strength = 200e6
zero_disp_tags = [1,2,3,4,11,12,13,14,15,16,17,18,25,26,27,28] 
traction_tags = [10, 24]
traction_values = [(1e6, 0, 0), (-1e6, 0, 0)]

# Calculate FOS
FOS = calculate_fos(step_file, E, nu, yield_strength, zero_disp_tags, traction_tags, traction_values)
print(f"Factor of Safety (FOS): {FOS}")