from src.nlp.politeness_normalizer import PolitenessNormalizer
from src.nlp.noise_normalizer import NoiseNormalizer
from src.nlp.simplification_normalizer import SimplificationNormalizer

def test_politeness_normalizer():
    normalizer = PolitenessNormalizer()
    
    # Feature 19 Examples
    assert normalizer.normalize("Could you open Steam") == "open Steam"
    assert normalizer.normalize("Please open Steam") == "open Steam"
    assert normalizer.normalize("Can you close Discord") == "close Discord"
    assert normalizer.normalize("Would you mind opening Chrome") == "opening Chrome"
    assert normalizer.normalize("Hey assistant open Steam") == "open Steam"
    assert normalizer.normalize("Actually close Discord") == "Actually close Discord" # Left for NoiseNormalizer
    assert normalizer.normalize("Just maximize it") == "maximize it"

def test_noise_normalizer():
    normalizer = NoiseNormalizer()
    
    # Feature 20 Examples
    assert normalizer.normalize("I think open Steam") == "open Steam"
    assert normalizer.normalize("Actually maximize Discord") == "maximize Discord"
    assert normalizer.normalize("Maybe close it") == "close it"
    assert normalizer.normalize("Well focus Chrome") == "focus Chrome"
    assert normalizer.normalize("Basically do this") == "do this"
    assert normalizer.normalize("Kind of open it") == "open it"
    assert normalizer.normalize("Sort of close it") == "close it"
    assert normalizer.normalize("Probably maximize it") == "maximize it"
    assert normalizer.normalize("You know open Steam") == "open Steam"

def test_simplification_normalizer():
    normalizer = SimplificationNormalizer()
    
    # Feature 21 Examples
    assert normalizer.normalize("I want you to open Steam") == "open Steam"
    assert normalizer.normalize("I'd like to open Discord") == "open Discord"
    assert normalizer.normalize("Open Steam for me") == "Open Steam"
    assert normalizer.normalize("Can you focus Chrome for me") == "Can you focus Chrome" # Politeness does the rest
    assert normalizer.normalize("Please try opening WhatsApp") == "Please open WhatsApp" # Politeness handles please
