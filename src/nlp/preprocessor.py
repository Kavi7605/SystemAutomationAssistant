import logging
from typing import List, Dict
from src.nlp.base_normalizer import BaseNormalizer
from src.nlp.grammar_normalizer import GrammarNormalizer
from src.nlp.number_normalizer import NumberNormalizer
from src.nlp.application_normalizer import ApplicationNormalizer
from src.nlp.intent_normalizer import IntentNormalizer
from src.nlp.reference_normalizer import ReferenceNormalizer
from src.nlp.canonicalizer import Canonicalizer
from src.nlp.politeness_normalizer import PolitenessNormalizer
from src.nlp.noise_normalizer import NoiseNormalizer
from src.nlp.simplification_normalizer import SimplificationNormalizer

logger = logging.getLogger(__name__)

class NLPPreprocessor:
    """
    Coordinates the NLP preprocessing pipeline.
    Takes a natural language input and runs it through a series of normalizers.
    """
    def __init__(self, pipeline: List[BaseNormalizer] = None):
        # Default pipeline order as specified
        if pipeline is None:
            self.pipeline = [
                PolitenessNormalizer(),
                NoiseNormalizer(),
                SimplificationNormalizer(),
                GrammarNormalizer(),
                ReferenceNormalizer(),
                NumberNormalizer(),
                ApplicationNormalizer(),
                IntentNormalizer(),
                Canonicalizer(),
            ]
        else:
            self.pipeline = pipeline

    def process(self, text: str) -> str:
        """
        Runs the text through the NLP pipeline and returns the normalized string.
        Logs structured debugging information.
        """
        current_text = text
        
        # Structured debugging information
        debug_info: Dict[str, str] = {
            "Original": current_text
        }
        
        for normalizer in self.pipeline:
            name = normalizer.__class__.__name__.replace("Normalizer", "")
            if name == "Canonicalizer":
                name = "Canonical"
                
            current_text = normalizer.normalize(current_text)
            debug_info[name] = current_text
            
        # Log the pipeline steps
        logger.info("--- NLP Pipeline ---")
        for step, value in debug_info.items():
            logger.info(f"{step}:\n{value}")
        logger.info("--------------------")
            
        return current_text
