"""
Script to generate vocabulary details (collocations, word_forms, synonyms, usage_notes) for all vocabulary words.
Works for all levels A1-C2.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.database import supabase
from core.llm import generate_response_with_fallback, parse_json_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_vocab_details(word: str, meaning: str, level: str, example: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Generate vocabulary details using AI.
    
    Returns:
        Dict with keys: collocations, phrasal_verbs, word_forms, synonyms, usage_notes
    """
    example_text = f"\nExample: {example}" if example else ""
    
    prompt = f"""Generate detailed vocabulary information for the English word: "{word}"

Word: {word}
Level: {level}
Meaning: {meaning}
{example_text}

Please provide the following information in JSON format:
{{
    "collocations": ["common phrase 1", "common phrase 2", ...],  // Max 5 common collocations
    "phrasal_verbs": "phrasal verb form if applicable, or empty string",  // Only if word has phrasal verb form
    "word_forms": {{
        "noun": "noun form if exists",
        "verb": "verb form if exists",
        "adjective": "adjective form if exists",
        "adverb": "adverb form if exists"
    }},
    "synonyms": ["synonym1", "synonym2", ...],  // Max 5 synonyms (only for level B1 and above, empty for A1-A2)
    "usage_notes": "Brief usage note in Vietnamese: formal/informal, context, common mistakes (max 100 words, MUST be in Vietnamese)"
}}

Rules:
- For A1-A2 levels: synonyms can be empty or very simple
- For B1-C2: include relevant synonyms
- Collocations should be practical and commonly used
- Word forms: only include if they exist and are commonly used
- Usage notes: MUST be in Vietnamese, keep brief and practical (100 words max)
- Return valid JSON only, no markdown code blocks"""

    try:
        response = generate_response_with_fallback(prompt, ["ERROR"])
        if not response or response == "ERROR":
            logger.warning(f"Failed to generate details for {word}")
            return None
        
        # Parse JSON response
        data = parse_json_response(response)
        if not data:
            logger.warning(f"Failed to parse JSON for {word}")
            return None
        
        # Validate structure
        result = {
            "collocations": data.get("collocations", []),
            "phrasal_verbs": data.get("phrasal_verbs", ""),
            "word_forms": data.get("word_forms", {}),
            "synonyms": data.get("synonyms", []),
            "usage_notes": data.get("usage_notes", "")
        }
        
        # Clean empty values
        if not result["phrasal_verbs"]:
            result["phrasal_verbs"] = None
        if not result["word_forms"] or all(not v for v in result["word_forms"].values()):
            result["word_forms"] = None
        if not result["synonyms"]:
            result["synonyms"] = None
        if not result["usage_notes"]:
            result["usage_notes"] = None
        if not result["collocations"]:
            result["collocations"] = None
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating details for {word}: {e}")
        return None


def update_vocab_details(vocab_id: int, details: Dict[str, Any]) -> bool:
    """Update vocabulary record with generated details."""
    try:
        update_data = {}
        
        if details.get("collocations"):
            update_data["collocations"] = details["collocations"]
        if details.get("phrasal_verbs"):
            update_data["phrasal_verbs"] = details["phrasal_verbs"]
        if details.get("word_forms"):
            update_data["word_forms"] = details["word_forms"]
        if details.get("synonyms"):
            update_data["synonyms"] = details["synonyms"]
        if details.get("usage_notes"):
            update_data["usage_notes"] = details["usage_notes"]
        
        if not update_data:
            return False
        
        result = supabase.table("Vocabulary").update(update_data).eq("id", vocab_id).execute()
        return bool(result.data)
        
    except Exception as e:
        logger.error(f"Error updating vocab {vocab_id}: {e}")
        return False


def process_vocabulary(level: Optional[str] = None, limit: Optional[int] = None, start_from: int = 0, 
                      only_missing: bool = True) -> None:
    """Process vocabulary words and generate details.
    
    Args:
        level: Process only this level (A1, A2, B1, B2, C1, C2) or None for all levels
        limit: Maximum number of words to process (None = all)
        start_from: Start from this index (for resumable processing)
        only_missing: Only process words that don't have details yet
    """
    try:
        # Build query - MUST include detail fields to check if already exists
        query = supabase.table("Vocabulary").select("id, word, meaning, level, example, collocations, phrasal_verbs, word_forms, synonyms, usage_notes")
        
        if level:
            query = query.eq("level", level)
        
        # Get all words (or a batch)
        if limit:
            query = query.range(start_from, start_from + limit - 1)
        
        result = query.execute()
        
        if not result.data:
            logger.info("No vocabulary words found")
            return
        
        words = result.data
        total = len(words)
        logger.info(f"Processing {total} vocabulary words (start_from={start_from})")
        
        processed = 0
        updated = 0
        skipped = 0
        errors = 0
        
        for idx, word_data in enumerate(words):
            vocab_id = word_data["id"]
            word = word_data["word"]
            level_val = word_data["level"]
            
            # Check if already has details (if only_missing is True)
            if only_missing:
                has_details = (
                    (word_data.get("collocations") and len(word_data.get("collocations", [])) > 0) or
                    (word_data.get("phrasal_verbs") and word_data.get("phrasal_verbs", "").strip()) or
                    (word_data.get("word_forms") and word_data.get("word_forms")) or
                    (word_data.get("synonyms") and len(word_data.get("synonyms", [])) > 0) or
                    (word_data.get("usage_notes") and word_data.get("usage_notes", "").strip())
                )
                if has_details:
                    skipped += 1
                    logger.debug(f"[{idx+1}/{total}] SKIP {word} (level {level_val}) - already has details")
                    continue
            
            processed += 1
            logger.info(f"[{idx+1}/{total}] Processing {word} (level {level_val})...")
            
            # Generate details
            details = generate_vocab_details(
                word=word,
                meaning=word_data.get("meaning", ""),
                level=level_val,
                example=word_data.get("example")
            )
            
            if not details:
                errors += 1
                logger.warning(f"  -> Failed to generate details")
                continue
            
            # Update database
            success = update_vocab_details(vocab_id, details)
            if success:
                updated += 1
                logger.info(f"  -> Updated successfully")
            else:
                errors += 1
                logger.warning(f"  -> Failed to update database")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Summary:")
        logger.info(f"  Total words: {total}")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Updated: {updated}")
        logger.info(f"  Skipped (already has details): {skipped}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error processing vocabulary: {e}", exc_info=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate vocabulary details for all words (A1-C2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all levels (A1-C2) - only words without details
  python scripts/generate_vocabulary_details.py
  
  # Process specific level only
  python scripts/generate_vocabulary_details.py --level B2
  
  # Process all levels with limit (for testing)
  python scripts/generate_vocabulary_details.py --limit 50
  
  # Process all levels, including words that already have details
  python scripts/generate_vocabulary_details.py --all
  
  # Process all levels starting from index 100
  python scripts/generate_vocabulary_details.py --start 100
        """
    )
    parser.add_argument("--level", type=str, choices=["A1", "A2", "B1", "B2", "C1", "C2"], 
                       help="Process only this level (default: all levels A1-C2)")
    parser.add_argument("--limit", type=int, help="Maximum number of words to process (default: all)")
    parser.add_argument("--start", type=int, default=0, help="Start from this index (default: 0)")
    parser.add_argument("--all", action="store_true", 
                       help="Process all words including those with details (default: skip words with details)")
    
    args = parser.parse_args()
    
    if args.level:
        print(f"🚀 Processing level {args.level} only...")
    else:
        print("🚀 Processing ALL levels (A1, A2, B1, B2, C1, C2)...")
    
    process_vocabulary(
        level=args.level,
        limit=args.limit,
        start_from=args.start,
        only_missing=not args.all
    )
