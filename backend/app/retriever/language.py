"""Language detection and translation module for SocioGraph retriever."""

from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer
from backend.app.core.singletons import get_logger

_tok, _model = None, None

def _load_helsinki():
    """Load Helsinki-NLP translation model."""
    global _tok, _model
    if _tok is None:
        try:
            # Try to load the model, but handle potential errors
            get_logger().info("Loading Helsinki-NLP translation model")
            _tok = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tc-big-ar-en")
            _model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-tc-big-ar-en")
            get_logger().info("Successfully loaded translation model")
            return True
        except Exception as e:
            # Log the error but continue execution
            get_logger().error(f"Error loading translation model: {e}")
            
            # Try loading a smaller model as fallback
            try:
                get_logger().info("Attempting to load smaller translation model as fallback")
                _tok = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ar-en")
                _model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ar-en")
                get_logger().info("Successfully loaded fallback translation model")
                return True
            except Exception as e2:
                get_logger().error(f"Error loading fallback translation model: {e2}")
                return False
    return True

def normalize_query(text: str) -> tuple[str, str]:
    """Detect language and translate if Arabic.
    
    Args:
        text: The input query text
        
    Returns:
        A tuple of (language code, english text)
    """
    logger = get_logger()
    
    # Require at least 4 tokens before attempting detection
    if len(text.split()) < 4:
        logger.info("Text too short for reliable detection, assuming English")
        return "en", text
        
    try:
        lang = detect(text)
        logger.info(f"Detected language: {lang}")
        
        if lang == "ar":
            # Try to translate Arabic to English
            if _load_helsinki() and _tok is not None and _model is not None:
                inputs = _tok(text, return_tensors="pt")
                output = _model.generate(**inputs, max_length=256, num_beams=4, early_stopping=True)
                text_en = _tok.decode(output[0], skip_special_tokens=True)
                logger.info("Translated AR → EN: %s", text_en)
                return "ar", text_en
            else:
                # Translation model not available, use original text
                logger.warning("Arabic translation model not available, using original text")
                return "ar", text
        return "en", text
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return "en", text  # Default to English on error
