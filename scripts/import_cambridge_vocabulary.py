"""
Script để import từ vựng Cambridge từ file CSV/JSON vào database.
Chỉ thêm các từ chưa tồn tại (theo unique constraint trên 'word').
"""
import sys
import os
import csv
import json
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import supabase
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
VALID_TYPES = ['noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction', 'interjection', 'determiner']

def check_word_exists(word: str) -> bool:
    """Kiểm tra từ đã tồn tại chưa (toàn database, không phân biệt level)."""
    if not supabase:
        return False
    try:
        result = supabase.table("Vocabulary").select("id").ilike("word", word).limit(1).execute()
        return len(result.data or []) > 0
    except Exception as e:
        logger.error(f"Error checking word {word}: {e}")
        return False

def validate_word_data(word_data: dict) -> tuple[bool, str]:
    """Validate dữ liệu từ vựng. Returns (is_valid, error_message)."""
    word = word_data.get('word', '').strip()
    level = word_data.get('level', '').strip().upper()
    
    if not word:
        return False, "Word cannot be empty"
    
    if level not in VALID_LEVELS:
        return False, f"Invalid level: {level}. Must be one of {VALID_LEVELS}"
    
    word_type = word_data.get('type', '').strip().lower()
    if word_type and word_type not in VALID_TYPES:
        # Warning but not error - type is optional
        logger.warning(f"Unknown word type '{word_type}' for word '{word}', will use as-is")
    
    return True, ""

def import_from_csv(file_path: str, dry_run: bool = False) -> dict:
    """Import từ vựng từ file CSV."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {'success': False, 'error': 'File not found'}
    
    stats = {
        'total': 0,
        'added': 0,
        'skipped': 0,
        'errors': 0,
        'error_details': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                stats['total'] += 1
                
                try:
                    # Normalize keys (strip whitespace, lowercase)
                    word_data = {k.strip().lower(): v.strip() if isinstance(v, str) else v 
                                for k, v in row.items() if v and str(v).strip()}
                    
                    # Map common column names
                    word = word_data.get('word', '').strip()
                    if not word:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {row_num}: Missing word")
                        continue
                    
                    # Validate
                    is_valid, error_msg = validate_word_data(word_data)
                    if not is_valid:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Row {row_num} ({word}): {error_msg}")
                        continue
                    
                    # Check if word already exists
                    if check_word_exists(word):
                        stats['skipped'] += 1
                        logger.debug(f"  Skipped: {word} (already exists)")
                        continue
                    
                    # Prepare insert data
                    insert_data = {
                        "word": word,
                        "level": word_data.get('level', '').strip().upper(),
                        "pronunciation": word_data.get('pronunciation', ''),
                        "meaning": word_data.get('meaning', ''),
                        "type": word_data.get('type', 'noun'),
                        "topic": word_data.get('topic'),
                        "example": word_data.get('example', ''),
                        "example_translation": word_data.get('example_translation', '')
                    }
                    
                    # Remove None values
                    insert_data = {k: v for k, v in insert_data.items() if v is not None and str(v).strip()}
                    
                    if not dry_run:
                        # Insert
                        result = supabase.table("Vocabulary").insert(insert_data).execute()
                        
                        if result.data:
                            stats['added'] += 1
                            logger.info(f"  Added: {word} ({insert_data['level']})")
                        else:
                            stats['errors'] += 1
                            stats['error_details'].append(f"Row {row_num} ({word}): Insert failed")
                    else:
                        stats['added'] += 1
                        logger.info(f"  [DRY RUN] Would add: {word} ({insert_data['level']})")
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Row {row_num}: {str(e)}")
                    logger.error(f"  Error processing row {row_num}: {e}")
    
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return {'success': False, 'error': str(e)}
    
    return {'success': True, 'stats': stats}

def import_from_json(file_path: str, dry_run: bool = False) -> dict:
    """Import từ vựng từ file JSON."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {'success': False, 'error': 'File not found'}
    
    stats = {
        'total': 0,
        'added': 0,
        'skipped': 0,
        'errors': 0,
        'error_details': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, dict):
                words = data.get('words', data.get('vocabulary', []))
            elif isinstance(data, list):
                words = data
            else:
                return {'success': False, 'error': 'Invalid JSON format'}
            
            for idx, word_data in enumerate(words, start=1):
                stats['total'] += 1
                
                try:
                    word = word_data.get('word', '').strip()
                    if not word:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Item {idx}: Missing word")
                        continue
                    
                    # Validate
                    is_valid, error_msg = validate_word_data(word_data)
                    if not is_valid:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Item {idx} ({word}): {error_msg}")
                        continue
                    
                    # Check if word already exists
                    if check_word_exists(word):
                        stats['skipped'] += 1
                        logger.debug(f"  Skipped: {word} (already exists)")
                        continue
                    
                    # Prepare insert data
                    insert_data = {
                        "word": word,
                        "level": word_data.get('level', '').strip().upper(),
                        "pronunciation": word_data.get('pronunciation', ''),
                        "meaning": word_data.get('meaning', ''),
                        "type": word_data.get('type', 'noun'),
                        "topic": word_data.get('topic'),
                        "example": word_data.get('example', ''),
                        "example_translation": word_data.get('example_translation', '')
                    }
                    
                    # Remove None values
                    insert_data = {k: v for k, v in insert_data.items() if v is not None and str(v).strip()}
                    
                    if not dry_run:
                        # Insert
                        result = supabase.table("Vocabulary").insert(insert_data).execute()
                        
                        if result.data:
                            stats['added'] += 1
                            logger.info(f"  Added: {word} ({insert_data['level']})")
                        else:
                            stats['errors'] += 1
                            stats['error_details'].append(f"Item {idx} ({word}): Insert failed")
                    else:
                        stats['added'] += 1
                        logger.info(f"  [DRY RUN] Would add: {word} ({insert_data['level']})")
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Item {idx}: {str(e)}")
                    logger.error(f"  Error processing item {idx}: {e}")
    
    except Exception as e:
        logger.error(f"Error reading JSON file: {e}")
        return {'success': False, 'error': str(e)}
    
    return {'success': True, 'stats': stats}

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Import Cambridge vocabulary from CSV/JSON file')
    parser.add_argument('--file', required=True, help='Path to CSV or JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no database changes)')
    args = parser.parse_args()
    
    file_path = args.file
    dry_run = args.dry_run
    
    logger.info("=" * 60)
    logger.info("Cambridge Vocabulary Import Script")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("\n*** DRY RUN MODE - No changes will be made to database ***\n")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        logger.info(f"Importing from CSV file: {file_path}\n")
        result = import_from_csv(file_path, dry_run)
    elif file_ext == '.json':
        logger.info(f"Importing from JSON file: {file_path}\n")
        result = import_from_json(file_path, dry_run)
    else:
        logger.error(f"Unsupported file format: {file_ext}. Please use .csv or .json")
        return
    
    if not result.get('success'):
        logger.error(f"\nImport failed: {result.get('error')}")
        return
    
    stats = result.get('stats', {})
    
    logger.info("\n" + "=" * 60)
    logger.info("Import Summary")
    logger.info("=" * 60)
    logger.info(f"Total words processed: {stats['total']}")
    logger.info(f"Added: {stats['added']}")
    logger.info(f"Skipped (already exists): {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    
    if stats['error_details']:
        logger.info("\nError Details:")
        for error in stats['error_details'][:10]:  # Show first 10 errors
            logger.warning(f"  - {error}")
        if len(stats['error_details']) > 10:
            logger.warning(f"  ... and {len(stats['error_details']) - 10} more errors")
    
    logger.info("\n" + "=" * 60)
    if dry_run:
        logger.info("DRY RUN completed. No changes were made.")
    else:
        logger.info("Import completed!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
