"""Language detection and translation module for SocioGraph retriever."""

from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer
from backend.app.core.singletons import get_logger
from backend.app.core.config import get_config

_tok, _model = None, None
_config = get_config()

def _load_helsinki():
    """Load Helsinki-NLP translation model with caching support."""
    global _tok, _model
    if _tok is None:
        try:
            # Get HuggingFace token from config
            hf_token = _config.HUGGINGFACE_TOKEN
            use_auth = hf_token is not None and len(str(hf_token).strip()) > 0
            
            # Set up cache directory from config
            cache_dir = str(_config.TRANSFORMERS_CACHE_DIR)
            
            # Try to load the model, but handle potential errors
            get_logger().info(f"Loading Helsinki-NLP translation model (with auth: {use_auth})")
            get_logger().info(f"Using cache directory: {cache_dir}")
            
            if use_auth:
                _tok = MarianTokenizer.from_pretrained(
                    "Helsinki-NLP/opus-mt-tc-big-ar-en", 
                    token=hf_token,
                    cache_dir=cache_dir
                )
                _model = MarianMTModel.from_pretrained(
                    "Helsinki-NLP/opus-mt-tc-big-ar-en", 
                    token=hf_token,
                    cache_dir=cache_dir
                )
            else:
                # Try without token for publicly available models
                _tok = MarianTokenizer.from_pretrained(
                    "Helsinki-NLP/opus-mt-tc-big-ar-en",
                    cache_dir=cache_dir
                )
                _model = MarianMTModel.from_pretrained(
                    "Helsinki-NLP/opus-mt-tc-big-ar-en",
                    cache_dir=cache_dir
                )                
            get_logger().info("Successfully loaded translation model from cache")
            return True
        except Exception as e:
            # Log the error but continue execution
            get_logger().error(f"Error loading translation model: {e}")
            
            # Try loading a smaller model as fallback
            try:
                get_logger().info("Attempting to load smaller translation model as fallback")
                cache_dir = str(_config.TRANSFORMERS_CACHE_DIR)
                
                if use_auth:
                    _tok = MarianTokenizer.from_pretrained(
                        "Helsinki-NLP/opus-mt-ar-en", 
                        token=hf_token,
                        cache_dir=cache_dir
                    )
                    _model = MarianMTModel.from_pretrained(
                        "Helsinki-NLP/opus-mt-ar-en", 
                        token=hf_token,
                        cache_dir=cache_dir
                    )
                else:
                    _tok = MarianTokenizer.from_pretrained(
                        "Helsinki-NLP/opus-mt-ar-en",
                        cache_dir=cache_dir
                    )
                    _model = MarianMTModel.from_pretrained(
                        "Helsinki-NLP/opus-mt-ar-en",
                        cache_dir=cache_dir
                    )
                get_logger().info("Successfully loaded fallback translation model from cache")
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

async def translate_with_llm(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using the LLM.
    
    Args:
        text: The text to translate
        source_lang: The source language code (e.g., 'en', 'ar')
        target_lang: The target language code (e.g., 'en', 'ar')
        
    Returns:
        The translated text
    """    
    logger = get_logger()
    logger.info(f"Translating text with LLM from {source_lang} to {target_lang}")
    
    # Skip translation if source and target are the same
    if source_lang == target_lang:
        return text
    
    # Get LLM client
    from backend.app.core.singletons import LLMClientSingleton
    client = LLMClientSingleton()
    
    # Prepare messages
    system_prompt = f"You are a professional translator. Translate the text from {source_lang} to {target_lang} accurately."
    user_prompt = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Translate using LLM
    try:
        translation = ""
        async for token in client.create_translation_chat(messages=messages):
            translation += token
        
        logger.info(f"Translation completed successfully")
        return translation
    except Exception as e:
        logger.error(f"Translation error: {e}")
        # Return original text if translation fails
        return text
