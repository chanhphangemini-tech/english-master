"""Unit tests for user_service module."""
import pytest
from unittest.mock import patch, MagicMock
from services.user_service import (
    get_user_stats,
    log_activity,
    add_coins,
    process_daily_streak
)


class TestGetUserStats:
    """Tests for get_user_stats function."""
    
    def test_get_user_stats_success(self, mock_supabase, sample_stats_data):
        """Test successful retrieval of user stats."""
        # Arrange
        mock_supabase.rpc.return_value.execute.return_value.data = [sample_stats_data]
        
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            result = get_user_stats(1)
        
        # Assert
        assert result['streak'] == 5
        assert result['words_learned'] == 50
        assert result['coins'] == 100
    
    def test_get_user_stats_no_data(self, mock_supabase):
        """Test get_user_stats with no data returned."""
        # Arrange - Mock RPC call trả về empty data
        mock_supabase.rpc.return_value.execute.return_value.data = []
        
        # Mock .from().select().eq().single().execute() chain cho user query
        mock_supabase.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            with patch('services.user_service.st'):  # Mock streamlit to disable caching
                result = get_user_stats(1)
        
        # Assert - Khi không có data, function trả về default values
        assert result['streak'] == 0
        assert result['words_learned'] == 0
        assert result['coins'] == 0
    
    def test_get_user_stats_invalid_user_id(self, mock_supabase):
        """Test get_user_stats with invalid user ID."""
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            result = get_user_stats(None)
        
        # Assert
        assert result['streak'] == 0


class TestLogActivity:
    """Tests for log_activity function."""
    
    def test_log_activity_success(self, mock_supabase):
        """Test successful activity logging."""
        # Arrange
        mock_insert = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert
        
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            log_activity(1, 'quiz_complete', 10)
        
        # Assert
        mock_supabase.table.assert_called_with('ActivityLog')
    
    def test_log_activity_with_zero_value(self, mock_supabase):
        """Test logging activity with zero value."""
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            log_activity(1, 'login', 0)
        
        # Assert - should not raise exception
        assert True


class TestAddCoins:
    """Tests for add_coins function."""
    
    def test_add_coins_success(self, mock_supabase):
        """Test successful coin addition."""
        # Arrange
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            add_coins(1, 50)
        
        # Assert
        mock_supabase.rpc.assert_called_with('increment_coins', {'p_user_id': 1, 'p_amount': 50})
    
    def test_add_coins_zero_amount(self, mock_supabase):
        """Test add_coins with zero amount (should not call RPC)."""
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            add_coins(1, 0)
        
        # Assert
        mock_supabase.rpc.assert_not_called()


class TestProcessDailyStreak:
    """Tests for process_daily_streak function."""
    
    def test_process_daily_streak_success(self, mock_supabase):
        """Test successful streak processing."""
        # Arrange
        streak_data = {'current_streak': 6, 'status': 'incremented', 'message': 'Streak increased!'}
        mock_supabase.rpc.return_value.execute.return_value.data = streak_data
        
        # Act
        with patch('services.user_service.supabase', mock_supabase):
            result = process_daily_streak(1)
        
        # Assert
        assert result['current_streak'] == 6
        assert result['status'] == 'incremented'

