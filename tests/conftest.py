"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """Clear Streamlit cache before and after each test."""
    try:
        import streamlit as st
        st.cache_data.clear()
        st.cache_resource.clear()
    except:
        pass
    yield
    try:
        import streamlit as st
        st.cache_data.clear()
        st.cache_resource.clear()
    except:
        pass


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('core.database.supabase') as mock:
        # Configure mock responses
        mock.table.return_value.select.return_value.execute.return_value.data = []
        mock.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock.table.return_value.update.return_value.execute.return_value = MagicMock()
        yield mock


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 1,
        'username': 'testuser',
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'user',
        'plan': 'free',
        'current_level': 'A1',
        'current_streak': 5,
        'coins': 100,
        'created_at': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_vocab_data():
    """Sample vocabulary data for testing."""
    return [
        {
            'id': 1,
            'word': 'hello',
            'type': 'greeting',
            'pronunciation': '/həˈloʊ/',
            'meaning': {'vietnamese': 'xin chào'},
            'level': 'A1',
            'example': 'Hello, how are you?',
            'example_translation': 'Xin chào, bạn khỏe không?',
            'topic': 'Greetings'
        },
        {
            'id': 2,
            'word': 'goodbye',
            'type': 'greeting',
            'pronunciation': '/ɡʊdˈbaɪ/',
            'meaning': {'vietnamese': 'tạm biệt'},
            'level': 'A1',
            'example': 'Goodbye, see you later!',
            'example_translation': 'Tạm biệt, hẹn gặp lại!',
            'topic': 'Greetings'
        }
    ]


@pytest.fixture
def sample_stats_data():
    """Sample user stats data for testing."""
    return {
        'streak': 5,
        'words_learned': 50,
        'words_today': 10,
        'coins': 100,
        'latest_test_score': '8.5/10 (B1)'
    }

