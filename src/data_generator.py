from typing import Tuple
from pointing_conversion import ENU
import math
# 26M limit lines cirica 1980, with corners estimated at:
# (86, 61), (77, 61), (77, 71), (57, 71), (57, 74), (-57, 74), (-57, 71), (-77, 71), (-77, 61), (-86, 61), (-86, -64), (-71, -64), (-71, -71), (71, -71), (71, -64), (86, -64)

class DataGen():
    """
    Given the minimum and maximum values for both x and y axis, generate a dataset of the resulting azimuth and elevation values for every degree of azimuth.
    """
    
    def __init__(self, xy: Tuple[Tuple[float, float], Tuple[float, float]] = ((-86.0, 86.0), (-76.0, 76.0))):
        """
        Processes limit data

        Args: a tuple of two tuples of two floats representing the x and y minimum and maximum values. Defaults to ((-86,86), (-76,76)) the legacy 26M antenna limits.
        """
        self.tolerance = 0.05
        self.x, self.y = xy
        self.enu = ENU(xy=(0.0, 0.0))

        self.legacy_lims = [(86, 61), (77, 61), (77, 71), (57, 71), (57, 74), (-57, 74), (-57, 71), (-77, 71), (-77, 61), (-86, 61), (-86, -64), (-71, -64), (-71, -71), (71, -71), (71, -64), (86, -64)]

    def find_limits(self):
        """
        Using ENU.from_azel check determine the azimuth and elvation of the xy limits. 
        """
        self.limit_list = []
        for azimuth in range(0, 360):
            el_min = 0.0 + 1e-9
            el_max = 89.99
            elevation = self.recursive_find_el(azimuth, el_min, el_max)
            self.limit_list.append((azimuth, elevation))
            #print(f"azimuth: {azimuth}, elevation: {round(elevation, 3)}")

    def find_from_point(self):
        """
        Using ENU.from_azel check determine the azimuth and elvation of the xy limits. 
        """
        self.limit_list = []
        for azimuth in range(0, 360):
            el_min = 0.0 + 1e-9
            el_max = 89.99
            elevation = self.recursive_point_resolve(azimuth, el_min, el_max)
            self.limit_list.append((azimuth, elevation))
            #print(f"azimuth: {azimuth}, elevation: {round(elevation, 3)}")

    def recursive_find_el(self, azimuth: float, el_min: float, el_max: float) -> float:
        """
        A recursive function to find the minimum elevation that is above the x,y limits.

        Args: the azimuth angle in degrees, the minimum elevation search limit, the maximum elevation search limit.

        Returns: the minimum elevation in degrees that respcts the limit.

        """
        if el_max >= el_min:
            mid = (el_max + el_min) / 2.0
            self.enu.from_azel(azimuth, mid)
            if all(self.test_limits(self.enu.xy)):
                # this point is inside all limits and within the absolute tolorance of 0.05 degrees
                return mid
            elif any(self.test_limits(self.enu.xy)):
                # inside the limits but not close to our edge, reduce the value; make the mid the max before the next divide.
                return self.recursive_find_el(azimuth, el_min, mid)
            else:
                # this point is outside the limits, make the mid the min before the next divide.
                #print(f"{azimuth}, {el_min}, {mid}")
                return self.recursive_find_el(azimuth, mid, el_max)

    def test_limits(self, xy: Tuple[float, float]) -> Tuple[bool, bool]:
        """
        Given an x,y set, check if they are inside the limit values.

        Args: A tuple of two floats, the x and y position.

        Returns: A tuple of two booleans, False for outside the respective x or y limit

        """
        x, y = xy
        if not(self.x[0] <= round(x, 4) <= self.x[1]):
            # outside the x limits
            return (False, False)
        if not(self.y[0] <= round(y, 4) <= self.y[1]):
            # outside the y limits
            return (False, False)
        # inside the limits by how much? I think this is fragile in the corners. X and Y could both be close
        x_lim = math.isclose(x, self.x[0], abs_tol=0.05) or math.isclose(x, self.x[1], abs_tol=0.05)
        y_lim = math.isclose(y, self.y[0], abs_tol=0.05) or math.isclose(y, self.y[1], abs_tol=0.05)
        if x_lim or y_lim:
            # I think we found our limit
            #print(f"x:{xy[0]:.3f}-{x_lim}, y:{xy[1]:.3f}-{y_lim}-{self.y[1]}")
            return (True, True)
        # inside the limits but not close
        return (True, False)

    def recursive_point_resolve(self, azimuth, el_min, el_max) -> float:
        """
        Recursivlely reduce the elevation until we are very near the edge. Then return the elevation value.
 
        Args: the azimuth angle in degrees, the minimum elevation search limit, the maximum elevation search limit.

        Returns: the minimum elevation in degrees that respcts the limit.

        """
        if el_max >= el_min:
            mid = (el_max + el_min) / 2.0
            self.enu.from_azel(azimuth, mid)
            inside, distance = self.point_in_polygon(self.enu.xy)
            if inside and distance < self.tolerance:
                # this point is inside all limits and within the absolute tolorance of 0.05 degrees
                return mid
            elif inside and distance > self.tolerance:
                # inside the limits but not close to our edge, reduce the value; make the mid the max before the next divide.
                return self.recursive_point_resolve(azimuth, el_min, mid)
            else:
                # this point is outside the limits, make the mid the min before the next divide.
                #print(f"{azimuth}, {el_min}, {mid}")
                return self.recursive_point_resolve(azimuth, mid, el_max)

    def point_in_polygon(self, point: Tuple[float, float])  -> Tuple[bool, float]:
        """
        Check if a point is inside an arbitrary polygon and calculate the distance  to the closest edge.

        Args:
            point (Tuple[float, float]): The point (x, y) to test.
            self.legacy_lims must be set (np.ndarray): Polygon vertices as a 2D array of shape  (N, 2), where N is the number of vertices.

        Returns:
            Tuple[bool, float]: A tuple containing a boolean indicating if the  point is inside the polygon and the distance to the closest edge.
        """
        x, y = point

        # Initialize variables for Ray Casting algorithm
        inside = False

        # Iterate through each polygon edge
        x, y = point
        inside = False
        min_distance = float('inf')

        for i in range(len(self.legacy_lims)):
            x1, y1 = self.legacy_lims[i]
            x2, y2 = self.legacy_lims[(i + 1) % len(self.legacy_lims)]

            # Ray casting algorithm to determine if the point is inside
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside

            # Calculate distance to the current edge
            distance = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)) / math.sqrt ((x2 - x1)**2 + (y2 - y1)**2)

            # Check if the point is on the edge
            if distance < 1e-9 and min(x1, x2) <= x <= max(x1, x2) and min(y1, y2)  <= y <= max(y1, y2):
                return True, 0  # Point is on the edge

            min_distance = min(min_distance, distance)

        if inside:
            return True, min_distance
        else:
            return False, None


if __name__ == '__main__':
    test = DataGen()
    test.find_limits()