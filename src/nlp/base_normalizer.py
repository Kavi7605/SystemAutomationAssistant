class BaseNormalizer:
    """
    Base class for all NLP normalization components.
    Enforces a common interface for the pipeline.
    """
    def normalize(self, text: str) -> str:
        """
        Takes a string and applies specific normalization logic, returning the modified string.
        """
        raise NotImplementedError("Each normalizer must implement the normalize method.")
