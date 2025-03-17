import numpy as np


class ENU():
    ''' Azimuth-Elevation-Range to East-North-Up frame
    '''
    def __init__(self, azel: tuple = None, xy: tuple = None, xyoffset: float = 0.0):
        self.vector = None
        self.east_vect = np.array([1,0,0])
        self.north_vect = np.array([0,1,0])
        self.up_vect = np.array([0,0,1])
        self.null_vect = np.array([0,0,0])
        # TODO: perhaps implment offset axes; Does this change the result much?
        self.offset = np.array([0, 0, xyoffset])    # the y axis offset in meters from the x axis along the z axis
        if azel is not None and xy is None:
            # azel antenna rotates from az=0, el=0
            self.vector = self.north_vect
            self.from_azel(*azel)
        elif xy is not None and azel is None:
            # xy antenna rotates from zenith
            self.vector = self.up_vect
            self.from_xy(*xy)
        else:
            # default is azel start point
            self.from_enu(*[0,1,0])

    def from_azel(self, az:float, el:float):
        ''' Calculate the ENU vector from an Azimuth, Elevation and Range
        '''
        self.az = az if az != 0 else 1e-6
        self.el = el if el != 0 else 1e-6
        self.vector = ((self.R_up(-az)) @ (self.R_east(el)) @ self.north_vect)
        self.vector = self.unit_vector(self.vector)
        self.update_state()

    def from_xy(self, x:float, y:float):
        ''' Create an ENU vector from an antenna X and Y value.
                used to convert between xy -> azel pointing angles
        '''
        self.x = x if x != 0 else 1e-6
        self.y = y if y != 0 else 1e-6
        self.vector = ((self.R_north(x)) @ (self.R_east(-y)) @ self.up_vect)
        self.vector = self.unit_vector(self.vector)
        self.update_state()

    def from_enu(self, e:float, n:float, u:float):
        ''' Build the vector and az el from the provided values
        '''
        if (e+n+u) != 0:
            self.vector = self.unit_vector(np.array([e, n, u]))
        else:
            self.vector = np.array([e, n, u])
        self.update_state()

    def update_state(self):
        ''' update the state of this object, self.vector must be defined
        '''
        self.east = self.vector[0]
        self.north = self.vector[1]
        self.up = self.vector[2]
        self.az = (np.degrees(np.arctan2(self.east, self.north)) + 360) % 360
        self.el = np.degrees(np.arcsin(self.up))
        self.rng = np.sqrt(self.east**2+self.north**2+self.up**2)
        self.x = (np.degrees(np.arctan2(self.east, self.up)))
        self.y = (np.degrees(np.arcsin(self.north)))
        self.z = (np.degrees(np.arctan2(self.east, self.north)))
        self.azel = (self.az, self.el)
        self.xy = (self.x, self.y)
#        print(f"state x,y,z is {round(self.x, 3),round(self.y, 3),round(self.z,3)} -- az/el is {round(self.az, 3),round(self.el, 3)}")

    def __str__(self) -> str:
        azel = (f"({self.az:.3f}, {self.el:.3f})")
        xy = (f"({self.x:.3f}, {self.y:.3f})")
        vect = (f"[{self.vector[0]:.3f}, {self.vector[1]:.3f}, {self.vector[2]:.3f}]")
        return f"azel:{azel}, xy:{xy}, vect:{vect}"
    
    def __repr__(self) -> str:
        return f"ENU(azel=({self.az}, {self.el}))"

    def unit_vector(self, vector:np.array) -> np.array:
        ''' returns the unit vector of the vector
        '''
        return vector / np.linalg.norm(vector)

    def angle_between(self, v1:np.array, v2:np.array) -> float:
        ''' Return the angle in radians between vectors v1 adn v2
        '''
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    def R_east(self, theta:float) -> np.array:
        ''' Rotate around the east axis
        '''
        rads = np.radians(theta, dtype=np.double)
        matrix = np.array([[1, 0, 0],
                           [0, np.cos(rads, dtype=np.double), -np.sin(rads, dtype=np.double)],
                           [0, np.sin(rads, dtype=np.double), np.cos(rads, dtype=np.double)]], dtype=np.double)
        if self.vector is None:
            return matrix
        self.vector = (matrix @ self.vector).T
        self.update_state()
        return matrix

    def R_north(self, theta:float) -> np.array:
        ''' Rotate around the north axis
        '''
        rads = np.radians(theta, dtype=np.double)
        matrix = np.array([[np.cos(rads, dtype=np.double), 0, np.sin(rads, dtype=np.double)],
                           [0, 1, 0],
                           [-np.sin(rads, dtype=np.double), 0, np.cos(rads, dtype=np.double)]], dtype=np.double)
        if self.vector is None:
            return matrix
        self.vector = (self.vector @ matrix).T
        self.update_state()
        return matrix

    def R_up(self, theta:float) -> np.array:
        ''' Rotate around the up axis
        '''
        rads = np.radians(theta, dtype=np.double)
        matrix = np.array([[np.cos(rads, dtype=np.double), -np.sin(rads, dtype=np.double), 0],
                           [np.sin(rads, dtype=np.double), np.cos(rads, dtype=np.double), 0],
                           [0, 0, 1]], dtype=np.double)
        if self.vector is None:
            return matrix
        self.vector = (self.vector @ matrix).T
        self.update_state()
        return matrix

    def R_rpy(self, psi:float, phi:float, theta:float) -> np.array:
        ''' Rotate around roll (psi), pitch (phi), yaw (theta), all in one go.
        '''
        psi = np.radians(psi, dtype=np.double)
        phi = np.radians(phi, dtype=np.double)
        theta = np.radians(theta, dtype=np.double)
        matrix = np.array([[np.cos(theta)*np.cos(psi)-np.sin(theta)*np.sin(phi)*np.sin(psi), -np.sin(theta)*np.cos(phi), -np.cos(theta)*np.sin(psi)-np.sin(theta)*np.sin(phi)*np.cos(psi)],
                           [-np.sin(theta)*np.cos(phi), np.cos(theta)*np.cos(phi), -np.sin(phi)],
                           [-np.cos(theta)*np.sin(psi)-np.sin(theta)*np.sin(phi)*np.cos(psi), -np.sin(theta)*np.sin(psi)+np.cos(theta)*np.sin(phi)*np.cos(psi), np.cos(phi)*np.cos(psi)]])
        self.vector = (self.vector @ matrix).T
        self.update_state()
        return matrix