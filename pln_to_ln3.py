import sys
from math import sin, cos, sqrt, atan2


#
# Convert a PLN flight plan to a LN3 waypoint file for TF-104G from SimSkunkWorks
#


# Convert from Degree|Minutes|Seconds (e.g. 52° 08' 32") to Degree.Decimal (e.g. 52.531913°)
def degree_to_decimal(coord: str) -> float:
    detail_coord = float(coord[1:coord.index('°')])
    detail_coord += float(coord[coord.index('°')+2:coord.rindex('\'')]) / 60
    detail_coord += float(coord[coord.index('\'') + 2:-1]) / 3600
    if coord[0] == 'S' or coord[0] == 'W':
        detail_coord = -detail_coord
    return detail_coord


# Strip altitude
def convert_altitude(height: str) -> int:
    return int(height[:height.rindex('.')])


def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6373.0
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (sin(delta_lat/2))**2 + cos(lat1) * cos(lat2) * (sin(delta_lon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return radius * c


# MAIN
if len(sys.argv) != 3:
    exit(-1)

filename = sys.argv[1]
output_dir = sys.argv[2]
waypoints = []
with open(filename, mode="r", encoding="utf-8") as file:
    for line in file.readlines():
        if "<ATCWaypoint id=" in line:
            name = line[line.index('"')+1:line.rindex('"')]
        elif "<WorldPosition>" in line:
            lat, long, alt = line[line.index('>')+1:line.rindex('<')].split(',')
            waypoints.append((name, degree_to_decimal(lat), degree_to_decimal(long), convert_altitude(alt)))

title = filename[filename.rindex("\\")+1:filename.rindex(".")]
wp_filename = output_dir + "\\" + title + ".ln3"

if len(waypoints) > 12:
    # print(f'Too many waypoints: {len(waypoints)}, max 12')
    start_wp = waypoints[0]
    end_wp = waypoints[-1]
    del waypoints[0]
    del waypoints[-1]
    while len(waypoints) > 10:
        distances = []
        for i in range(len(waypoints)-1):
            distances.append(distance(waypoints[i][1], waypoints[i][2], waypoints[i+1][1], waypoints[i+1][2]))

        shortest_leg = 0
        min_dist = distances[0]
        for i in range(len(distances)):
            if distances[i] < min_dist:
                min_dist = distances[i]
                shortest_leg = i
        # print(f'Removing {waypoints[shortest_leg+1][0]} dist={min_dist:.2f}')
        del waypoints[shortest_leg+1]
    waypoints.insert(0, start_wp)
    waypoints.append(end_wp)

wp_plan: [str] = [f'# {title}', '']
for i in range(len(waypoints)):
    wp_plan.append(f'[STATION{i + 1}]')
    wp_plan.append('{')
    wp_plan.append(f'LAT: {waypoints[i][1]:.6f};')
    wp_plan.append(f'LON: {waypoints[i][2]:.6f};')
    wp_plan.append(f'NAME: "{waypoints[i][0]}";')
    wp_plan.append(f'ALT: {waypoints[i][3]};')
    wp_plan.append('}')
    wp_plan.append('')

# [print(wp) for wp in wp_plan]

with open(wp_filename, mode="w", encoding="utf-8") as out_file:
    out_file.writelines(wp + '\n' for wp in wp_plan)
