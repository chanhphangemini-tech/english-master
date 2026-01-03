"""
Learning Insights Service - AI-Powered Learning Recommendations
Phân tích điểm mạnh/yếu và đưa ra recommendations dựa trên dữ liệu học tập
"""
import streamlit as st
from core.database import supabase
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from core.timezone_utils import get_vn_now_utc, get_vn_start_of_day_utc
from core.llm import generate_response_with_fallback

logger = logging.getLogger(__name__)


def analyze_user_weaknesses(user_id: int, days: int = 30) -> Dict:
    """
    Phân tích điểm yếu của người dùng.
    
    Args:
        user_id: User ID
        days: Số ngày để phân tích (default: 30)
    
    Returns:
        Dict với keys:
        - vocabulary_weaknesses: List of words frequently forgotten
        - grammar_weaknesses: List of grammar topics with low completion
        - skill_weaknesses: Dict với skill types và accuracy
        - topic_weaknesses: List of vocabulary topics with low mastery
    """
    if not supabase or not user_id:
        return {
            "vocabulary_weaknesses": [],
            "grammar_weaknesses": [],
            "skill_weaknesses": {},
            "topic_weaknesses": []
        }
    
    try:
        # 1. Vocabulary Weaknesses - Words frequently forgotten (quality < 3)
        start_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
        
        vocab_weaknesses = []
        try:
            # Get ReviewLogs for this user in the time period
            review_res = supabase.table("ReviewLogs")\
                .select("vocab_id, rating, Vocabulary(word, meaning, topic, level)")\
                .eq("user_id", user_id)\
                .gte("reviewed_at", start_date)\
                .lt("rating", 3)\
                .execute()
            
            # Count mistakes per word
            word_mistakes = {}
            if review_res.data:
                for review in review_res.data:
                    vocab_data = review.get('Vocabulary', {})
                    if isinstance(vocab_data, dict):
                        vocab_id = review.get('vocab_id')
                        if vocab_id:
                            if vocab_id not in word_mistakes:
                                word_mistakes[vocab_id] = {
                                    'vocab_id': vocab_id,
                                    'word': vocab_data.get('word', ''),
                                    'meaning': vocab_data.get('meaning', ''),
                                    'topic': vocab_data.get('topic', ''),
                                    'level': vocab_data.get('level', 'A1'),
                                    'mistake_count': 0
                                }
                            word_mistakes[vocab_id]['mistake_count'] += 1
            
            # Sort by mistake count and get top 10
            vocab_weaknesses = sorted(word_mistakes.values(), key=lambda x: x['mistake_count'], reverse=True)[:10]
        except Exception as e:
            logger.warning(f"Error analyzing vocabulary weaknesses: {e}")
        
        # 2. Grammar Weaknesses - Topics with low completion or low scores
        grammar_weaknesses = []
        try:
            grammar_res = supabase.table("UserGrammarProgress")\
                .select("lesson_id, test_score, attempts, GrammarLessons(topic, level, title)")\
                .eq("user_id", user_id)\
                .execute()
            
            topic_scores = {}
            if grammar_res.data:
                for progress in grammar_res.data:
                    lesson_data = progress.get('GrammarLessons', {})
                    if isinstance(lesson_data, dict):
                        topic = lesson_data.get('topic', 'Other')
                        test_score = progress.get('test_score')
                        attempts = progress.get('attempts', 0)
                        
                        if topic not in topic_scores:
                            topic_scores[topic] = {
                                'topic': topic,
                                'total_score': 0,
                                'count': 0,
                                'total_attempts': 0
                            }
                        
                        if test_score is not None:
                            topic_scores[topic]['total_score'] += test_score
                            topic_scores[topic]['count'] += 1
                        topic_scores[topic]['total_attempts'] += attempts
            
            # Calculate average scores and identify weaknesses (avg < 7 or high attempts)
            for topic, data in topic_scores.items():
                avg_score = data['total_score'] / data['count'] if data['count'] > 0 else 0
                avg_attempts = data['total_attempts'] / max(data['count'], 1)
                
                if avg_score < 7 or avg_attempts > 2:
                    grammar_weaknesses.append({
                        'topic': topic,
                        'avg_score': round(avg_score, 1),
                        'avg_attempts': round(avg_attempts, 1)
                    })
            
            grammar_weaknesses.sort(key=lambda x: (x['avg_score'], -x['avg_attempts']))
            grammar_weaknesses = grammar_weaknesses[:5]
        except Exception as e:
            logger.warning(f"Error analyzing grammar weaknesses: {e}")
        
        # 3. Skill Weaknesses - Skills with low accuracy
        skill_weaknesses = {
            "listening": 0,
            "speaking": 0,
            "reading": 0,
            "writing": 0
        }
        try:
            skill_res = supabase.table("SkillProgress")\
                .select("skill_type, progress_percent")\
                .eq("user_id", user_id)\
                .execute()
            
            if skill_res.data:
                for skill in skill_res.data:
                    skill_type = skill.get('skill_type', '').lower()
                    progress = skill.get('progress_percent', 0) or 0
                    if skill_type in skill_weaknesses:
                        skill_weaknesses[skill_type] = progress
        except Exception as e:
            logger.warning(f"Error analyzing skill weaknesses: {e}")
        
        # 4. Topic Weaknesses - Vocabulary topics with low mastery
        topic_weaknesses = []
        try:
            # Get vocabulary progress by topic
            vocab_progress_res = supabase.table("UserVocabulary")\
                .select("vocab_id, Vocabulary(topic, level)")\
                .eq("user_id", user_id)\
                .execute()
            
            topic_counts = {}
            if vocab_progress_res.data:
                for item in vocab_progress_res.data:
                    vocab_data = item.get('Vocabulary', {})
                    if isinstance(vocab_data, dict):
                        topic = vocab_data.get('topic', 'Other') or 'Other'
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Compare with total vocabulary in each topic to find low mastery topics
            all_vocab_res = supabase.table("Vocabulary")\
                .select("topic")\
                .execute()
            
            topic_totals = {}
            if all_vocab_res.data:
                for vocab in all_vocab_res.data:
                    topic = vocab.get('topic', 'Other') or 'Other'
                    topic_totals[topic] = topic_totals.get(topic, 0) + 1
            
            # Calculate mastery percentage
            for topic, learned_count in topic_counts.items():
                total_count = topic_totals.get(topic, 0)
                if total_count > 0:
                    mastery_percent = (learned_count / total_count) * 100
                    if mastery_percent < 30:  # Less than 30% mastery
                        topic_weaknesses.append({
                            'topic': topic,
                            'learned': learned_count,
                            'total': total_count,
                            'mastery_percent': round(mastery_percent, 1)
                        })
            
            topic_weaknesses.sort(key=lambda x: x['mastery_percent'])
            topic_weaknesses = topic_weaknesses[:5]
        except Exception as e:
            logger.warning(f"Error analyzing topic weaknesses: {e}")
        
        return {
            "vocabulary_weaknesses": vocab_weaknesses,
            "grammar_weaknesses": grammar_weaknesses,
            "skill_weaknesses": skill_weaknesses,
            "topic_weaknesses": topic_weaknesses
        }
    except Exception as e:
        logger.error(f"Error analyzing user weaknesses: {e}")
        return {
            "vocabulary_weaknesses": [],
            "grammar_weaknesses": [],
            "skill_weaknesses": {},
            "topic_weaknesses": []
        }


def analyze_user_strengths(user_id: int, days: int = 30) -> Dict:
    """
    Phân tích điểm mạnh của người dùng.
    
    Returns:
        Dict với keys:
        - vocabulary_strengths: List of topics with high mastery
        - grammar_strengths: List of grammar topics with high scores
        - skill_strengths: Dict với skill types và high accuracy
        - level_strengths: List of levels with high completion
    """
    if not supabase or not user_id:
        return {
            "vocabulary_strengths": [],
            "grammar_strengths": [],
            "skill_strengths": {},
            "level_strengths": []
        }
    
    try:
        # 1. Vocabulary Strengths - Topics with high mastery
        vocab_strengths = []
        try:
            vocab_progress_res = supabase.table("UserVocabulary")\
                .select("vocab_id, Vocabulary(topic, level)")\
                .eq("user_id", user_id)\
                .execute()
            
            topic_counts = {}
            if vocab_progress_res.data:
                for item in vocab_progress_res.data:
                    vocab_data = item.get('Vocabulary', {})
                    if isinstance(vocab_data, dict):
                        topic = vocab_data.get('topic', 'Other') or 'Other'
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Get total vocabulary in each topic
            all_vocab_res = supabase.table("Vocabulary")\
                .select("topic")\
                .execute()
            
            topic_totals = {}
            if all_vocab_res.data:
                for vocab in all_vocab_res.data:
                    topic = vocab.get('topic', 'Other') or 'Other'
                    topic_totals[topic] = topic_totals.get(topic, 0) + 1
            
            # Calculate mastery percentage
            for topic, learned_count in topic_counts.items():
                total_count = topic_totals.get(topic, 0)
                if total_count > 0 and learned_count >= 5:  # At least 5 words learned
                    mastery_percent = (learned_count / total_count) * 100
                    if mastery_percent >= 70:  # 70%+ mastery
                        vocab_strengths.append({
                            'topic': topic,
                            'learned': learned_count,
                            'total': total_count,
                            'mastery_percent': round(mastery_percent, 1)
                        })
            
            vocab_strengths.sort(key=lambda x: x['mastery_percent'], reverse=True)
            vocab_strengths = vocab_strengths[:5]
        except Exception as e:
            logger.warning(f"Error analyzing vocabulary strengths: {e}")
        
        # 2. Grammar Strengths - Topics with high scores
        grammar_strengths = []
        try:
            grammar_res = supabase.table("UserGrammarProgress")\
                .select("lesson_id, test_score, GrammarLessons(topic, level, title)")\
                .eq("user_id", user_id)\
                .execute()
            
            topic_scores = {}
            if grammar_res.data:
                for progress in grammar_res.data:
                    lesson_data = progress.get('GrammarLessons', {})
                    if isinstance(lesson_data, dict):
                        topic = lesson_data.get('topic', 'Other')
                        test_score = progress.get('test_score')
                        
                        if topic not in topic_scores:
                            topic_scores[topic] = {
                                'topic': topic,
                                'total_score': 0,
                                'count': 0
                            }
                        
                        if test_score is not None and test_score >= 8:
                            topic_scores[topic]['total_score'] += test_score
                            topic_scores[topic]['count'] += 1
            
            # Calculate average scores
            for topic, data in topic_scores.items():
                if data['count'] > 0:
                    avg_score = data['total_score'] / data['count']
                    if avg_score >= 8:
                        grammar_strengths.append({
                            'topic': topic,
                            'avg_score': round(avg_score, 1),
                            'completed_count': data['count']
                        })
            
            grammar_strengths.sort(key=lambda x: x['avg_score'], reverse=True)
            grammar_strengths = grammar_strengths[:5]
        except Exception as e:
            logger.warning(f"Error analyzing grammar strengths: {e}")
        
        # 3. Skill Strengths
        skill_strengths = {
            "listening": 0,
            "speaking": 0,
            "reading": 0,
            "writing": 0
        }
        try:
            skill_res = supabase.table("SkillProgress")\
                .select("skill_type, progress_percent")\
                .eq("user_id", user_id)\
                .gte("progress_percent", 70)\
                .execute()
            
            if skill_res.data:
                for skill in skill_res.data:
                    skill_type = skill.get('skill_type', '').lower()
                    progress = skill.get('progress_percent', 0) or 0
                    if skill_type in skill_strengths:
                        skill_strengths[skill_type] = progress
        except Exception as e:
            # Log Resource temporarily unavailable errors at DEBUG level (non-critical, temporary network issues)
            error_str = str(e)
            if 'Resource temporarily unavailable' in error_str or '[Errno 11]' in error_str:
                logger.debug(f"Error analyzing skill strengths (temporary network issue): {e}")
            else:
                logger.warning(f"Error analyzing skill strengths: {e}")
        
        # 4. Level Strengths
        level_strengths = []
        try:
            level_progress_res = supabase.table("UserVocabulary")\
                .select("vocab_id, Vocabulary(level)")\
                .eq("user_id", user_id)\
                .execute()
            
            level_counts = {}
            if level_progress_res.data:
                for item in level_progress_res.data:
                    vocab_data = item.get('Vocabulary', {})
                    if isinstance(vocab_data, dict):
                        level = vocab_data.get('level', 'A1') or 'A1'
                        level_counts[level] = level_counts.get(level, 0) + 1
            
            # Get total vocabulary per level
            all_vocab_res = supabase.table("Vocabulary")\
                .select("level")\
                .execute()
            
            level_totals = {}
            if all_vocab_res.data:
                for vocab in all_vocab_res.data:
                    level = vocab.get('level', 'A1') or 'A1'
                    level_totals[level] = level_totals.get(level, 0) + 1
            
            # Calculate completion percentage
            for level, learned_count in level_counts.items():
                total_count = level_totals.get(level, 0)
                if total_count > 0 and learned_count >= 10:
                    completion_percent = (learned_count / total_count) * 100
                    if completion_percent >= 50:
                        level_strengths.append({
                            'level': level,
                            'learned': learned_count,
                            'total': total_count,
                            'completion_percent': round(completion_percent, 1)
                        })
            
            level_strengths.sort(key=lambda x: x['completion_percent'], reverse=True)
        except Exception as e:
            logger.warning(f"Error analyzing level strengths: {e}")
        
        return {
            "vocabulary_strengths": vocab_strengths,
            "grammar_strengths": grammar_strengths,
            "skill_strengths": skill_strengths,
            "level_strengths": level_strengths
        }
    except Exception as e:
        logger.error(f"Error analyzing user strengths: {e}")
        return {
            "vocabulary_strengths": [],
            "grammar_strengths": [],
            "skill_strengths": {},
            "level_strengths": []
        }


def generate_learning_recommendations(user_id: int, days: int = 30) -> List[Dict]:
    """
    Generate personalized learning recommendations using AI.
    
    Args:
        user_id: User ID
        days: Number of days to analyze
    
    Returns:
        List of recommendation dicts với keys: type, title, description, priority, action_url
    """
    if not supabase or not user_id:
        return []
    
    try:
        # Get weaknesses and strengths
        weaknesses = analyze_user_weaknesses(user_id, days)
        strengths = analyze_user_strengths(user_id, days)
        
        # Prepare data for AI
        analysis_data = {
            "weaknesses": weaknesses,
            "strengths": strengths
        }
        
        # Generate recommendations using AI
        prompt = f"""Phân tích dữ liệu học tập và đưa ra 5-7 recommendations cụ thể để cải thiện:

Điểm yếu:
- Từ vựng hay quên: {[w.get('word', '') for w in weaknesses.get('vocabulary_weaknesses', [])[:5]]}
- Chủ đề ngữ pháp khó: {[g.get('topic', '') for g in weaknesses.get('grammar_weaknesses', [])[:5]]}
- Kỹ năng cần cải thiện: {[k for k, v in weaknesses.get('skill_weaknesses', {}).items() if v < 70]}
- Chủ đề từ vựng chưa tốt: {[t.get('topic', '') for t in weaknesses.get('topic_weaknesses', [])[:5]]}

Điểm mạnh:
- Chủ đề từ vựng tốt: {[s.get('topic', '') for s in strengths.get('vocabulary_strengths', [])[:5]]}
- Chủ đề ngữ pháp tốt: {[g.get('topic', '') for g in strengths.get('grammar_strengths', [])[:5]]}
- Kỹ năng tốt: {[k for k, v in strengths.get('skill_strengths', {}).items() if v >= 70]}

Hãy đưa ra 5-7 recommendations cụ thể, thực tế, dễ thực hiện. Format JSON array:
[
  {{"type": "vocabulary|grammar|skill", "title": "Tiêu đề ngắn gọn", "description": "Mô tả chi tiết", "priority": "high|medium|low"}},
  ...
]
"""
        
        # Call AI
        response = generate_response_with_fallback(
            prompt=prompt,
            feature_type="learning_insights"
        )
        
        # Parse AI response
        recommendations = []
        try:
            import json
            # Try to extract JSON from response
            response_text = response.get('text', '') if isinstance(response, dict) else str(response)
            
            # Find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                recommendations = json.loads(json_str)
            else:
                # Fallback: Generate basic recommendations from analysis
                recommendations = _generate_basic_recommendations(weaknesses, strengths)
        except Exception as e:
            logger.warning(f"Error parsing AI recommendations: {e}")
            recommendations = _generate_basic_recommendations(weaknesses, strengths)
        
        # Add action URLs and validate
        for rec in recommendations:
            if not isinstance(rec, dict):
                continue
            
            rec_type = rec.get('type', 'general')
            if rec_type == 'vocabulary':
                rec['action_url'] = 'pages/06_On_Tap.py'
            elif rec_type == 'grammar':
                rec['action_url'] = 'pages/07_Ngu_Phap.py'
            elif rec_type == 'skill':
                skill_name = rec.get('title', '').lower()
                if 'nghe' in skill_name or 'listening' in skill_name:
                    rec['action_url'] = 'pages/01_Luyen_Nghe.py'
                elif 'nói' in skill_name or 'speaking' in skill_name:
                    rec['action_url'] = 'pages/02_Luyen_Noi.py'
                elif 'đọc' in skill_name or 'reading' in skill_name:
                    rec['action_url'] = 'pages/03_Luyen_Doc.py'
                elif 'viết' in skill_name or 'writing' in skill_name:
                    rec['action_url'] = 'pages/04_Luyen_Viet.py'
                else:
                    rec['action_url'] = 'pages/01_Luyen_Nghe.py'
            else:
                rec['action_url'] = 'home.py'
        
        # Limit to top 7 recommendations
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        recommendations = recommendations[:7]
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating learning recommendations: {e}")
        return []


def _generate_basic_recommendations(weaknesses: Dict, strengths: Dict) -> List[Dict]:
    """Generate basic recommendations without AI if AI fails."""
    recommendations = []
    
    # Vocabulary recommendations
    vocab_weak = weaknesses.get('vocabulary_weaknesses', [])
    if vocab_weak:
        recommendations.append({
            "type": "vocabulary",
            "title": "Ôn tập từ vựng hay quên",
            "description": f"Bạn có {len(vocab_weak)} từ vựng hay quên. Hãy ôn tập lại để cải thiện!",
            "priority": "high"
        })
    
    # Grammar recommendations
    grammar_weak = weaknesses.get('grammar_weaknesses', [])
    if grammar_weak:
        recommendations.append({
            "type": "grammar",
            "title": "Luyện ngữ pháp",
            "description": f"Bạn cần cải thiện {len(grammar_weak)} chủ đề ngữ pháp.",
            "priority": "medium"
        })
    
    # Skill recommendations
    skill_weak = weaknesses.get('skill_weaknesses', {})
    weak_skills = [k for k, v in skill_weak.items() if v < 70]
    if weak_skills:
        skill_names = {
            'listening': 'Nghe',
            'speaking': 'Nói',
            'reading': 'Đọc',
            'writing': 'Viết'
        }
        skill_list = ', '.join([skill_names.get(s, s) for s in weak_skills])
        recommendations.append({
            "type": "skill",
            "title": f"Luyện kỹ năng {skill_list}",
            "description": f"Cần cải thiện kỹ năng {skill_list}.",
            "priority": "high"
        })
    
    # Topic recommendations
    topic_weak = weaknesses.get('topic_weaknesses', [])
    if topic_weak:
        recommendations.append({
            "type": "vocabulary",
            "title": "Mở rộng từ vựng theo chủ đề",
            "description": f"Học thêm từ vựng về {topic_weak[0].get('topic', 'các chủ đề')}.",
            "priority": "medium"
        })
    
    return recommendations


def get_learning_insights(user_id: int, days: int = 30, use_cache: bool = True) -> Dict:
    """
    Get comprehensive learning insights (with caching).
    
    Args:
        user_id: User ID
        days: Number of days to analyze
        use_cache: Whether to use cached insights (default: True)
    
    Returns:
        Dict với keys:
        - weaknesses: Analysis of weaknesses
        - strengths: Analysis of strengths
        - recommendations: List of AI-generated recommendations
        - last_updated: Timestamp of last update
    """
    if not supabase or not user_id:
        return {}
    
    try:
        # Check cache (stored in session state for now, could use database cache later)
        cache_key = f"learning_insights_{user_id}"
        if use_cache and cache_key in st.session_state:
            cached_data = st.session_state[cache_key]
            last_updated = cached_data.get('last_updated')
            
            # Use cache if updated within last 24 hours
            if last_updated:
                try:
                    from datetime import datetime
                    last_update_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    now_dt = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
                    hours_passed = (now_dt - last_update_dt).total_seconds() / 3600
                    
                    if hours_passed < 24:
                        return cached_data
                except:
                    pass
        
        # Generate fresh insights
        weaknesses = analyze_user_weaknesses(user_id, days)
        strengths = analyze_user_strengths(user_id, days)
        recommendations = generate_learning_recommendations(user_id, days)
        
        insights = {
            "weaknesses": weaknesses,
            "strengths": strengths,
            "recommendations": recommendations,
            "last_updated": get_vn_now_utc()
        }
        
        # Cache in session state
        if use_cache:
            st.session_state[cache_key] = insights
        
        return insights
    
    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        return {}
