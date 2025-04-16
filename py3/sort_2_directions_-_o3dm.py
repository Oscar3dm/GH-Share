# @GHInput: points_to_sort (Point3d) [Access=Tree]
# @GHInput: direction_1 (Vector3d) 
# @GHInput: tolerance_1 (float) 
# @GHInput: direction_2 (object) 
# @GHInput: data_to_sort (object) [Access=Tree]
# @GHOutput: indices_out (object) 
# @GHOutput: points_out (object) 
# @GHOutput: data_out (object) 

import Grasshopper as gh
import Rhino as rc

def sort_points_along_vector(point_index_tuples, vector):
    origin_point = rc.Geometry.Point3d(0,0,0)
    sort_line = rc.Geometry.Line(origin_point, vector)
    sort_points = []
    for point, index in point_index_tuples:
        closest_point = sort_line.ClosestPoint(point, False)
        closest_t = sort_line.ClosestParameter(point)
        sort_points.append((closest_point, closest_t, point, index))
    sort_points.sort(key=lambda x: x[1])
    return sort_points

def group_points(sorted_points, tolerance):
    grouped_points = []
    current_group = []

    for i, (closest_point, closest_t, point, index) in enumerate(sorted_points):
        current_group.append((point, index))  # Store point and index

        # Check if we are at the end of the list
        if i >= len(sorted_points) - 1:
            grouped_points.append(current_group)
            current_group = []
            continue

        # Check the distance to the next closest point
        next_closest_point = sorted_points[i + 1][0]
        distance = closest_point.DistanceTo(next_closest_point)
        if distance > tolerance:
            grouped_points.append(current_group)
            current_group = []  # Start a new group

    return grouped_points

point_paths = points_to_sort.Paths

points_out = gh.DataTree[object]()
indices_out = gh.DataTree[object]()

# Data tree for the second set of items, sorted in parallel:
data_out = gh.DataTree[object]()

for point_path in points_to_sort.Paths:
    # --- Get the relevant branches ---
    branch_points = points_to_sort.Branch(point_path)
    branch_data = data_to_sort.Branch(point_path)  # <--- second data tree branch

    # --- Create (point, index) list for sorting ---
    indexed_branch_points = [(p,i) for i,p in enumerate(branch_points)]

    # --- First sort along direction_1 ---
    sorted_points_1 = sort_points_along_vector(indexed_branch_points, direction_1)

    # --- Group by tolerance_1 ---
    grouped_points_1 = group_points(sorted_points_1, tolerance_1)

    # --- Sort each group along direction_2 ---
    for list_i, point_index_list in enumerate(grouped_points_1):
        # Sort that group
        sorted_points_tuple_2 = sort_points_along_vector(point_index_list, direction_2)
        # Each entry is (closest_point, closest_t, original_point, original_index)
        sorted_points_2_with_index = [(pt_tuple[2], pt_tuple[3]) for pt_tuple in sorted_points_tuple_2]

        # Create a sub-path for these items
        new_path = point_path.AppendElement(list_i)

        # Collect final points and corresponding indices
        point_list_to_add = []
        index_list_to_add = []
        data_list_to_add = []  # <--- parallel data

        for (final_point, final_index) in sorted_points_2_with_index:
            point_list_to_add.append(final_point)
            index_list_to_add.append(final_index)

            # Grab the parallel data item by the same index
            # (assuming data_to_sort has 1:1 items per point)
            data_item = branch_data[final_index]
            data_list_to_add.append(data_item)

        # --- Populate all outputs ---
        points_out.AddRange(point_list_to_add, new_path)
        indices_out.AddRange(index_list_to_add, new_path)
        data_out.AddRange(data_list_to_add, new_path)