# Stock Cube Parameters
stock_min_x = 50.0 
stock_min_y = 50.0 
stock_min_z = 50.0 

stock_max_x = 100.0 
stock_max_y = 100.0 
stock_max_z = 100.0 

stock_dim_x = None
stock_dim_y = None
stock_dim_z = None

# General Feature Parameters
min_len = 2.0 #2
clearance = 2 #1
inner_bounds_clearance = 5

# Round Parameters
round_radius_min = 0.5
round_radius_max = 20  #5.0

# Chamfer Parameters
chamfer_depth_min = 0.1# 1
chamfer_depth_max = 20.0 #4

# Radii
radii_min = 0.1
radii_max = 2.5

# Possible Manufacturing Features
feat_names = ['chamfer', #0
              'through_hole', #1
              'triangular_passage', #2
              'rectangular_passage', #3
              'six_sides_passage', #4
              'triangular_through_slot', #5
              'rectangular_through_slot', #6
              'circular_through_slot', #7
              'rectangular_through_step', #8
              '2sides_through_step', #9
              'slanted_through_step', #10
              'Oring', #11
              'blind_hole', #12
              'triangular_pocket', #13
              'rectangular_pocket', #14
              'six_sides_pocket', #15
              'circular_end_pocket', #16
              'rectangular_blind_slot', #17
              'v_circular_end_blind_slot', #18
              'h_circular_end_blind_slot', #19
              'triangular_blind_step', #20
              'circular_blind_step', #21
              'rectangular_blind_step', #22
              'round', #23
              'extrude_cylinder',#24
              'extrude_rectangle', #25
              'extrude_triangle', #26
              'extrude_hexagon', #27
              'extrude_pentagon', #28
              'eblind_hole', #29
              'ethrough_hole', #30
              'slot_hole', #31
              'obround_boss', #32
              'five_sides_passage', #33
              'five_sides_pocket', #34
              'cylinder_with_hole', #35
              'rounded_triangular_passage', #36
              'rounded_rectangular_passage', #37
              "rounded_six_sides_passage", #38
              "rounded_triangular_through_slot", #39
              "rounded_triangular_pocket", #40
              "rounded_rectangular_pocket", #41
              "rounded_six_sides_pocket", #42
              'stock'] #43