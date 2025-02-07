from enum import Enum

# Map "spatial_resolution" above with the prefix to use
spatial_resolution_prefix_map = {
    'state': '040US',
    'county': '050US',
    'tract': '140US',
    'bg': '150US',
    'zcta': '860US',
}

# Enum for spatial_reolution
class SpatialResolution(str, Enum):
    state = 'state'
    county = 'county'
    tract = 'tract'
    blockgroup = 'blockgroup'
    zcta = 'zcta'

    def __str__(self) -> str:
        return self.value

    # Constant prefixes based on spatial resolution
    def to_prefix(self):
        return spatial_resolution_prefix_map[self.value]


