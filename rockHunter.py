import os
import geopy.distance
from pathlib import Path
from dted import LatLon, Tile

# Represents the step increments that in feet
# Example: 50 = 50 feet, the program will check lat long every 50 feet
step = 50
# Represents the minimum distance in feet between cliffs for it to be counted as a new cliff
# setting to 0 will record all lat long points with slope no matter distance
min_distance = 1000
# Target heigh is the vertical change in meters required for a elevation change to be considered a cliff
# slope = step / target_height
target_height = 30

# Turns a dted file into a lat long corner point
def pharse_dted_name(file_title):
    parts = file_title.split("_")

    lat = int(parts[0].replace("n", ""))
    long = int(parts[1].replace("w", "")) * -1

    return lat, long

# Checks the neighbor cords to detect a cliff
def check_neighbor_cords(lat, long):
    # gets target elevation
    target_ele = tile.get_elevation(LatLon(latitude=lat, longitude=long))

    neighbors = []

    # tries to detect upper right neighbor
    try:
        cord = lat + cal_step_lat, long + cal_step_long
        neighbors.append((cord, tile.get_elevation(LatLon(latitude=cord[0], longitude=cord[1]))))
    except:
        pass

    # tries to detect right neighbor
    try:
        cord = lat, long - cal_step_long
        neighbors.append((cord, tile.get_elevation(LatLon(latitude=cord[0], longitude=cord[1]))))
    except:
        pass

    # tries to detect lower right neighbor
    try:
        cord = lat - cal_step_lat, long + cal_step_long
        neighbors.append((cord, tile.get_elevation(LatLon(latitude=cord[0], longitude=cord[1]))))
    except:
        pass

    # tries to detect lower neighbor
    try:
        cord = lat - cal_step_lat, long
        neighbors.append((cord, tile.get_elevation(LatLon(latitude=cord[0], longitude=cord[1]))))
    except:
        pass


    cliff = False
    drop = 0

    # goes through the neighbors that were detected to see if any can be considerd a cliff
    for neighbor in neighbors:
        change = abs(neighbor[1] - target_ele)
        if change >= target_height:
            cliff = True

            if (drop < change):
                drop = change

    return cliff, drop


files = os.listdir("dted")

# loops through if there are multiple files
for file_name in files:
    lat, long = pharse_dted_name(file_name)

    # sets up x and y range and converts step to step degree increments
    x_range = [long, long + 1]
    y_range = [lat, lat + 1]
    distance_long = geopy.distance.geodesic((y_range[0], x_range[0]), (y_range[0], x_range[1])).feet
    distance_lat = geopy.distance.geodesic((y_range[0], x_range[0]), (y_range[1], x_range[0])).feet
    cal_step_lat = 1 / (distance_lat / step)
    cal_step_long = 1 / (distance_long / step)

    # opens the first dted file as a tile
    dted_file = Path(f"dted/{file_name}")
    tile = Tile(dted_file, in_memory=True)
    tile.load_data(perform_checksum=False)

    current_lat_step = 0
    current_long_step = 0
    in_lat_range = True
    in_long_range = True
    targets = []
    tot_rows = distance_long / step
    current_row = 0

    # loops through lat and long range and checks neighbors for cliffs
    while (in_long_range):
        current_row += 1
        current_lat_step = 0
        in_lat_range = True
        print(f"On row {current_row} / {tot_rows} for file {file_name}")

        while (in_lat_range):
            if not (current_lat_step >= 1):
                this_lat, this_long = lat + current_lat_step, long + current_long_step
                cliff, drop = check_neighbor_cords(this_lat, this_long)
                add_cliff = True
                for cliff_found in targets:

                    # checks if cliff found is within 1000 feet of another cliff
                    if (geopy.distance.geodesic((cliff_found[0][0],cliff_found[0][1]), (this_lat, this_long)).feet < 1000):
                        add_cliff = False
                        break

                # adds cliff to target if meets requirements
                if cliff and add_cliff:
                    targets.append(([this_lat, this_long], drop))
                    with open("results.txt", "a") as file:
                        file.write(f"{this_lat, this_long} | {drop} meters\n")
                    file.close()
                    print(f"Found a cliff! {this_lat, this_long} with drop {drop}")

                current_lat_step += cal_step_lat
            else:
                in_lat_range = False

        current_long_step += cal_step_long
        in_long_range = not (current_long_step >= 1)

    print(targets)
