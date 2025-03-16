import pytest
import numpy as np
from src.pointing_conversion import ENU

@pytest.fixture
def enu():
    """Fixture to create an ENU object for testing."""
    return ENU()

@pytest.mark.parametrize("azel,xy", [((0, 0), (0,90)), ((90, 45), (45, 0)), ((180, 45), (0, -45)), ((270, 45), (-45,0)), ((0, 45), (0,45)), ((0, 90), (0,0))])
def test_init_with_azel(enu, azel, xy):
    """Test initialization with AZEL values."""
    enu = ENU(azel=azel)
    az, el = azel
    x, y = xy
    assert np.isclose(enu.az, az)
    assert np.isclose(enu.el, el)
    assert np.isclose(enu.x, x)
    assert np.isclose(enu.y, y)

@pytest.mark.parametrize("azel,xy", [((0, 0), (0,90)), ((90, 45), (45, 0)), ((180, 45), (0, -45)), ((270, 45), (-45,0)), ((0, 45), (0,45)), ((0, 90), (0,0))])
def test_init_with_xy(enu, azel, xy):
    """Test initialization with AZEL values."""
    enu = ENU(xy=xy)
    az, el = azel
    x, y = xy
    assert np.isclose(enu.az, az)
    assert np.isclose(enu.el, el)
    assert np.isclose(enu.x, x)
    assert np.isclose(enu.y, y)

def test_init_with_none(enu):
    """Test initialization with default values."""
    assert np.allclose(enu.vector, [0, 1, 0])
    assert np.isclose(enu.az, 0.0)
    assert np.isclose(enu.el, 0.0)

def test_unit_vector(enu):
    """Test the unit vector calculation."""
    vector = np.array([1, 2, 3])
    unit_vector = enu.unit_vector(vector)
    assert np.allclose(np.linalg.norm(vector/np.linalg.norm(vector)), np.linalg.norm(unit_vector))
    assert np.isclose(np.linalg.norm(unit_vector), 1.0)

def test_angle_between(enu):
    """Test the angle between two vectors."""
    v1 = np.array([1, 0, 0])
    v2 = np.array([0,1,0])
    angle = enu.angle_between(v1, v2)
    assert np.isclose(np.degrees(angle), 90.0)

def test_r_east(enu):
    """Test the R_east calculation."""
    enu.vector = np.array([1, 0, 0])
    enu.R_east(0)
    assert np.allclose(enu.vector, np.array([1.0, 0.0, 0.0]))

def test_r_north(enu):
    """Test the R_north calculation."""
    enu.vector = np.array([0, 1, 0])
    enu.R_north(0)
    assert np.allclose(enu.vector, np.array([0.0, 1.0, 0.0]))

def test_r_up(enu):
    """Test the R_up calculation."""
    enu.vector = np.array([0, 0, 1])
    enu.R_up(0)
    assert np.allclose(enu.vector, np.array([0.0, 0.0, 1.0]))

def test_r_rpy(enu):
    """Test the R_rpy calculation."""
    enu.vector = np.array([1, 0, 0])
    enu.R_rpy(0, 0, 0)
    assert np.allclose(enu.vector, np.array([1.0, 0.0, 0.0]))

def test_update_state(enu):
    """Test the update_state method."""
    enu.vector = np.array([1, 1, 1])
    enu.update_state()
    assert np.isclose(enu.east, 1.0)
    assert np.isclose(enu.north, 1.0)
    assert np.isclose(enu.up, 1.0)
    assert np.isclose(enu.az, 45.0)
    assert np.isclose(enu.el, 90.0)
    assert np.isclose(enu.rng, np.sqrt(3.0))
    assert np.isclose(enu.x, 45.0)
    assert np.isclose(enu.y, 90.0)
    assert np.isclose(enu.z, 45.0)

def test_string():
    enu = ENU(azel=(90.0, 45.0))
    assert str(enu) == "azel:(90.000, 45.000), xy:(45.000, 0.000), vect:[0.707, 0.000, 0.707]"

def test_repr():
    enu = ENU(azel=(45.0, 90.0))
    assert repr(enu) == "ENU(azel=(45.0, 90.0))"

if __name__ == "__main__":
    pytest.main([__file__])