"""
AutoBolt: An automated bolt selection and analysis tool.
"""

from .combined import calculate_fos
from .fea_solver import _calculate_fos_from_build123d
from .parametric_cad_solver import create_two_plate_assembly
