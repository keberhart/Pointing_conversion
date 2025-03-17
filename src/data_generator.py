from typing import Tuple
from pointing_conversion import ENU
import math


class DataGen():
    """
    Given the minimum and maximum values for both x and y axis, generate a dataset of the resulting azimuth and elevation values for every degree of azimuth.
    
    """
    
    def __init__(self, xy: Tuple[Tuple[float, float], Tuple[float, float]] = ((-86.0, 86.0), (-76.0, 76.0))):
        """
        Processes limit data

        Args: a tuple of two tuples of two floats representing the x and y minimu and maximum values. Defaults to ((-86,86), (-76,76)) the legacy 26M antenna limits.

        """
        self.x, self.y = xy
        self.enu = ENU(xy=(0.0, 0.0))
        self.find_limits()

    def find_limits(self):
        """
        Using ENU.from_azel check determine the azimuth and elvation of the xy limits. 
        """
        self.limit_list = []
        for azimuth in range(0, 359):
            el_min = 1
            el_max = 90
            elevation = self.recursive_find_el(azimuth, el_min, el_max)
            self.limit_list.append((azimuth, elevation))
            #print(f"azimuth: {azimuth}, elevation: {round(elevation, 3)}")

    def recursive_find_el(self, azimuth: float, el_min: float, el_max: float) -> float:
        """
        A recursive function to find the minimum elevation that is above the x,y limits.

        Args: the azimuth angle in degrees, the minimum elevation search limit, the maximum elevation search limit.

        Returns: the minimum elevation in degrees that respcts the limit.

        """
        #TODO: this has problems! our the search needs to know which way to go. Sometimes the limit is on the low side sometimes on the high side. The azimuth value will give us the hint for which limits to test on each axis.
        if el_max >= el_min:
            mid = (el_max + el_min) / 2.05
            self.enu.from_azel(azimuth, mid)
            if all(self.test_limits(self.enu.xy)):
                # this point is inside all limits and within the tolorance of 0.05 degrees
                return mid
            elif any(self.test_limits(self.enu.xy)):
                # inside the limits but not close to our edge, reduce the value.
                return self.recursive_find_el(azimuth, el_min, mid)
            else:
                # this point is below the limits, increase the mid value for the next loop and rais our floor
                #print(f"{azimuth}, {el_min}, {mid}")
                return self.recursive_find_el(azimuth, mid, el_max)

    def test_limits(self, xy: Tuple[float, float]) -> Tuple[bool, bool]:
        """
        Given an x,y set, check if they are inside the limit values.

        Args: A tuple of two floats, the x and y position.

        Returns: A tuple of two booleans, False for outside the respective x or y limit

        """
        x, y = xy
        if not(self.x[0] <= round(x, 2) <= self.x[1]):
            # outside the x limits
            return (False, False)
        if not(self.y[0] <= round(y, 2) <= self.y[1]):
            # outside the y limits
            return (False, False)
        # inside the limits by how much? I think this is fragile in the corners. X and Y could both be close
        x_lim = math.isclose(x, self.x[0], rel_tol=0.05) or math.isclose(x, self.x[1], rel_tol=0.05)
        y_lim = math.isclose(y, self.y[0], rel_tol=0.05) or math.isclose(y, self.y[1], rel_tol=0.05)
        if x_lim or y_lim:
            # I think we found our limit
            print(xy)
            return (True, True)
        # inside the limits but not close
        return (True, False)


if __name__ == '__main__':
    test = DataGen()
    test.find_limits()