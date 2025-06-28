class FeatureException(Exception):
    """Custom exception for feature failures."""
    def __init__(self, message=None):
        if message is None:
            message = "Feature failed"
        super().__init__(message)
