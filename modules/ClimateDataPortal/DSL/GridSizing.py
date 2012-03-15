# -*- coding: utf-8 -*-

# Grid sizes vary for the different projections.
# it's important that the grid sizes match, otherwise there will be no data
# Projections can be used with other projections on the same grid.
# Projections can be used with grids, in this case the right grid must be picked.
# Grids can be used with other grids of the same grid size.
# Observed data is not on a grid but at points.
# Each node has a set of possible grid sizes.


from . import Method
grid_sizes = Method("grid_sizes")

class MismatchedGridSize(Exception):
    pass

from . import Addition, Subtraction, Multiplication, Division
@grid_sizes.implementation(Addition, Subtraction, Multiplication, Division)
def operation_grid_sizes(binop):
    left_grid_sizes = grid_sizes(binop.left)
    right_grid_sizes = grid_sizes(binop.right)
    binop.grid_sizes = best_grid_sizes = left_grid_sizes.intersection(right_grid_sizes)
    if len(best_grid_sizes) == 0:
        binop.grid_size_error = MismatchedGridSize(
            (binop, left_grid_sizes, right_grid_sizes)
        )
    return binop.grid_sizes

from . import Pow
@grid_sizes.implementation(Pow)
def power_grid_sizes(pow):
    pow.grid_sizes = grid_sizes(pow.left)
    return pow.grid_sizes

from . import aggregations
@grid_sizes.implementation(*aggregations)
def aggregation_grid_sizes(aggregation):
    return set((aggregation.sample_table.grid_size,))

from . import Number
@grid_sizes.implementation(Number, int, float)
def number_grid_sizes(number):
    return set((0, 10, 12, 20, 25))



apply_grid_size = Method("grid_size")

@apply_grid_size.implementation(Addition, Subtraction, Multiplication, Division)
def apply_operation_grid_size(binop, grid_size):
    apply_grid_size(binop.left, grid_size)
    apply_grid_size(binop.right, grid_size)

@apply_grid_size.implementation(Pow)
def apply_power_grid_size(pow, grid_size):
    apply_grid_size(pow.left, grid_size)

@apply_grid_size.implementation(*aggregations)
def apply_aggregation_grid_size(aggregation, grid_size):
    aggregation.grid_size = grid_size

@apply_grid_size.implementation(Number, int, float)
def apply_number_grid_size(number):
    pass
