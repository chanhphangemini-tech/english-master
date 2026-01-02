"""
Wrapper script to generate vocabulary details for ALL levels (A1-C2) sequentially.
This script processes each level one by one to avoid overwhelming the AI API.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
from generate_vocabulary_details import process_vocabulary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def generate_all_levels(only_missing: bool = True, delay_between_levels: int = 5):
    """Generate vocabulary details for all levels sequentially.
    
    Args:
        only_missing: Only process words that don't have details yet
        delay_between_levels: Delay in seconds between levels (to avoid rate limiting)
    """
    logger.info("="*70)
    logger.info("🚀 Starting vocabulary details generation for ALL LEVELS (A1-C2)")
    logger.info("="*70)
    
    total_start_time = time.time()
    
    for idx, level in enumerate(LEVELS, 1):
        logger.info("\n" + "="*70)
        logger.info(f"📚 Processing Level {level} ({idx}/{len(LEVELS)})")
        logger.info("="*70)
        
        level_start_time = time.time()
        
        try:
            process_vocabulary(
                level=level,
                limit=None,  # Process all words in this level
                start_from=0,
                only_missing=only_missing
            )
            
            level_duration = time.time() - level_start_time
            logger.info(f"\n✅ Level {level} completed in {level_duration:.1f} seconds")
            
        except Exception as e:
            logger.error(f"\n❌ Error processing level {level}: {e}")
            logger.info("Continuing with next level...")
            continue
        
        # Delay between levels (except for the last one)
        if idx < len(LEVELS):
            logger.info(f"\n⏳ Waiting {delay_between_levels} seconds before next level...")
            time.sleep(delay_between_levels)
    
    total_duration = time.time() - total_start_time
    logger.info("\n" + "="*70)
    logger.info(f"🎉 ALL LEVELS COMPLETED!")
    logger.info(f"⏱️  Total time: {total_duration/60:.1f} minutes ({total_duration:.1f} seconds)")
    logger.info("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate vocabulary details for ALL levels (A1-C2) sequentially",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script processes each level (A1, A2, B1, B2, C1, C2) one by one.
It's safer for large datasets as it avoids overwhelming the AI API.

Examples:
  # Process all levels (only words without details)
  python scripts/generate_all_levels_vocab_details.py
  
  # Process all levels (including words with details - regenerate all)
  python scripts/generate_all_levels_vocab_details.py --all
  
  # Custom delay between levels (default: 5 seconds)
  python scripts/generate_all_levels_vocab_details.py --delay 10
        """
    )
    parser.add_argument("--all", action="store_true",
                       help="Process all words including those with details (default: skip words with details)")
    parser.add_argument("--delay", type=int, default=5,
                       help="Delay in seconds between levels (default: 5)")
    
    args = parser.parse_args()
    
    generate_all_levels(
        only_missing=not args.all,
        delay_between_levels=args.delay
    )
