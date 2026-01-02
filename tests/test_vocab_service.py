"""Unit tests for vocab_service module."""
import pytest
from unittest.mock import patch, MagicMock
from services.vocab_service import (
    load_vocab_data,
    load_progress,
    get_due_vocabulary,
    update_srs_stats,
    add_word_to_srs
)


class TestLoadVocabData:
    """Tests for load_vocab_data function."""
    
    def test_load_vocab_data_success(self, mock_supabase, sample_vocab_data):
        """Test successful vocabulary data loading."""
        # Arrange - Add .order() to mock chain
        mock_execute = MagicMock()
        mock_execute.data = sample_vocab_data
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_execute
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            result = load_vocab_data('A1')
        
        # Assert
        assert len(result) == 2
        assert result[0]['word'] == 'hello'
        assert result[1]['word'] == 'goodbye'
    
    def test_load_vocab_data_empty_level(self, mock_supabase):
        """Test loading vocabulary with no data."""
        # Arrange - Add .order() to mock chain
        mock_execute = MagicMock()
        mock_execute.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_execute
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            result = load_vocab_data('C2')
        
        # Assert
        assert result == []


class TestLoadProgress:
    """Tests for load_progress function."""
    
    def test_load_progress_success(self, mock_supabase):
        """Test successful progress loading."""
        # Arrange
        progress_data = [
            {'user_id': 1, 'vocab_id': 1, 'status': 'learning', 'streak': 2},
            {'user_id': 1, 'vocab_id': 2, 'status': 'mastered', 'streak': 10}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = progress_data
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            result = load_progress(1)
        
        # Assert
        assert len(result) == 2
        assert result[0]['status'] == 'learning'
        assert result[1]['status'] == 'mastered'


class TestUpdateSRSStats:
    """Tests for update_srs_stats function."""
    
    def test_update_srs_stats_success(self, mock_supabase):
        """Test successful SRS stats update."""
        # Arrange
        current_data = {
            'id': 1,
            'user_id': 1,
            'vocab_id': 1,
            'interval': 1,
            'ease_factor': 2.5,
            'streak': 0
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = current_data
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            with patch('services.vocab_service.calculate_review_schedule') as mock_calc:
                mock_calc.return_value = {
                    'next_review': MagicMock(isoformat=lambda: '2024-01-01'),
                    'interval': 2,
                    'ease_factor': 2.6,
                    'streak': 1,
                    'status': 'learning'
                }
                result = update_srs_stats(1, 1, 5)
        
        # Assert
        assert result is True


class TestAddWordToSRS:
    """Tests for add_word_to_srs function."""
    
    def test_add_word_to_srs_new_word(self, mock_supabase):
        """Test adding a new word to SRS."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            result = add_word_to_srs(1, 1)
        
        # Assert
        assert result is True
    
    def test_add_word_to_srs_existing_word(self, mock_supabase):
        """Test adding an existing word to SRS."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{'id': 1}]
        
        # Act
        with patch('services.vocab_service.supabase', mock_supabase):
            result = add_word_to_srs(1, 1)
        
        # Assert
        assert result is True  # Already exists, return True

