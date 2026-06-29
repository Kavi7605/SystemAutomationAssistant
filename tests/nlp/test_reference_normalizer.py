import pytest
from src.nlp.reference_normalizer import ReferenceNormalizer

def test_reference_normalizer_plurals():
    normalizer = ReferenceNormalizer()
    
    assert normalizer.normalize("close both of them") == "close both"
    assert normalizer.normalize("close all of them") == "close all"
    assert normalizer.normalize("close both apps") == "close both"
    assert normalizer.normalize("close both applications") == "close both"
    assert normalizer.normalize("close these apps") == "close all"
    assert normalizer.normalize("close those apps") == "close all"
    assert normalizer.normalize("close them") == "close all"

def test_reference_normalizer_case_insensitivity():
    normalizer = ReferenceNormalizer()
    assert normalizer.normalize("CLOSE BOTH OF THEM") == "CLOSE both"
    assert normalizer.normalize("Close Them") == "Close all"

def test_reference_normalizer_boundaries():
    normalizer = ReferenceNormalizer()
    # "theme" should not be replaced by "all"
    assert normalizer.normalize("change the theme") == "change the theme"
