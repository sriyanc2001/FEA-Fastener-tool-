# FEniCS-GMSH Automation for Factor of Safety (FOS) Calculation

This project automates the process of calculating the **Factor of Safety (FOS)** for a 3D geometry defined in a STEP file. It uses **GMSH** for mesh generation and **FEniCS** for finite element analysis (FEA). The workflow is encapsulated in a single Python function, making it easy to use and integrate into larger workflows.

---

## Table of Contents
1. [Overview](#overview)
2. [Dependencies](#dependencies)
3. [Inputs](#inputs)
4. [Outputs](#outputs)


---

## Overview

The project consists of two Python functions, `create_two_plate_assembly`, which builds a STEP file of two overlapping plates with holes and can be customized to different plate and hole dimensions. This STEP file along with material properties as input to `calculate_fos` function which returns the Factor of Safety (FOS) along with stress and displacement plots. The functions performs the following steps:

1. **Parametric 3D Model Generation**: Uses build123d to generate a 3D model from parametric data.
2. **Mesh Generation**: Uses GMSH to generate a 3D mesh from the STEP file.
3. **Mesh Conversion**: Converts the GMSH mesh into XDMF format for use in FEniCS.
4. **Finite Element Analysis**: Solves the mechanical problem using FEniCS to compute stresses and diplacements.
5. **FOS Calculation**: Computes the von Mises stress and calculates the Factor of Safety (FOS) based on the yield stress.

---

## Dependencies

The code relies on the following Python libraries:
- **build123d**: For 3D Model generation. 
- **FEniCS**: For finite element analysis.
- **GMSH**: For mesh generation.
- **meshio**: For converting GMSH mesh files to XDMF format.

Make sure you have the following installed:
- Python 3.x
- FEniCS (install via [FEniCS documentation](https://fenicsproject.org/download/))
- GMSH (install via [GMSH documentation](https://gmsh.info/doc/texinfo/gmsh.html))
- `meshio` (install via `pip install meshio`)
- `build123d` (install via `pip install build123d`)
---

## Inputs

| Parameter         | Type                | Description                                                                 | Example Value                     |
|-------------------|---------------------|-----------------------------------------------------------------------------|-----------------------------------|
| `step_file`       | string              | Path to STEP file containing 3D geometry                                   | `"geometry.step"`                |
| `E`               | float               | Young's modulus in Pascals (Pa)                                             | `210e9` (for steel)              |
| `nu`              | float               | Poisson's ratio (unitless)                                                  | `0.3`                            |
| `yield_strength`  | float               | Material yield strength in Pascals (Pa)                                     | `200e6`                          |
| `zero_disp_tags`  | list of integers    | Surface tags where displacement = 0 (fixed boundaries)                     | `[1, 2, 3]`                      |
| `traction_tags`   | list of integers    | Surface tags where traction forces are applied                              | `[4, 5]`                         |
| `traction_values` | list of tuples      | Traction vectors (x,y,z) in Pa for corresponding tags                      | `[(1e6,0,0), (-1e6,0,0)]`        |

## Outputs

| Output            | Type    | Description                                                                 |
|-------------------|---------|-----------------------------------------------------------------------------|
| Return value      | float   | Computed Factor of Safety (FOS)                                            |

