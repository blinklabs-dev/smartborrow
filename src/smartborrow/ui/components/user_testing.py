#!/usr/bin/env python3
"""
User Testing and Feedback System for SmartBorrow
Comprehensive testing scenarios and feedback collection for people-first design
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import random

class UserTestingSystem:
    """System for user testing and feedback collection"""
    
    def __init__(self):
        self.test_scenarios = {
            'first_time_user': {
                'name': 'First-Time User Journey',
                'description': 'Complete newcomer to financial aid process',
                'tasks': [
                    'Complete smart intake process',
                    'Navigate to personalized dashboard',
                    'Ask a question about financial aid',
                    'Use the cost calculator',
                    'Find and start a guided workflow'
                ],
                'success_metrics': [
                    'Completes intake without confusion',
                    'Finds relevant information quickly',
                    'Feels supported and not overwhelmed',
                    'Can complete basic tasks independently'
                ]
            },
            'stressed_user': {
                'name': 'Stressed User Support',
                'description': 'User feeling overwhelmed by financial aid complexity',
                'tasks': [
                    'Access emotional support features',
                    'Find stress reduction tools',
                    'Get clear, simple explanations',
                    'Complete a task without feeling rushed',
                    'Find help when stuck'
                ],
                'success_metrics': [
                    'Feels less anxious after using the system',
                    'Can complete tasks without panic',
                    'Finds the interface calming and supportive',
                    'Gets clear answers to questions'
                ]
            },
            'accessibility_user': {
                'name': 'Accessibility Testing',
                'description': 'User with accessibility needs',
                'tasks': [
                    'Navigate using only keyboard',
                    'Use screen reader features',
                    'Adjust visual settings',
                    'Complete tasks with reduced motion',
                    'Access all information without barriers'
                ],
                'success_metrics': [
                    'Can complete all tasks with assistive technology',
                    'Finds interface usable with accessibility tools',
                    'Can customize settings to meet needs',
                    'Gets same information as other users'
                ]
            },
            'mobile_user': {
                'name': 'Mobile User Experience',
                'description': 'User primarily on mobile device',
                'tasks': [
                    'Navigate interface on small screen',
                    'Complete forms on mobile',
                    'Read information clearly',
                    'Use interactive features',
                    'Access all functionality'
                ],
                'success_metrics': [
                    'Can complete all tasks on mobile',
                    'Text and buttons are appropriately sized',
                    'Navigation works well on small screen',
                    'No horizontal scrolling required'
                ]
            },
            'returning_user': {
                'name': 'Returning User Experience',
                'description': 'User who has used the system before',
                'tasks': [
                    'Find previous progress quickly',
                    'Continue where left off',
                    'Access saved information',
                    'Get personalized recommendations',
                    'Track ongoing applications'
                ],
                'success_metrics': [
                    'Can quickly find previous work',
                    'System remembers preferences',
                    'Gets relevant updates and reminders',
                    'Feels like a returning customer'
                ]
            }
        }
        
        self.feedback_questions = {
            'usability': [
                'How easy was it to find what you were looking for?',
                'How clear were the instructions and explanations?',
                'How intuitive was the navigation?',
                'How helpful were the suggestions and recommendations?',
                'How would you rate the overall user experience?'
            ],
            'emotional_support': [
                'Did you feel supported and understood while using the system?',
                'How helpful were the stress reduction features?',
                'Did the system help reduce your anxiety about financial aid?',
                'How encouraging and motivating was the interface?',
                'Did you feel more confident after using the system?'
            ],
            'accessibility': [
                'How accessible was the interface for your needs?',
                'Were you able to customize the experience for your preferences?',
                'How well did the system work with your assistive technology?',
                'Were there any barriers to accessing information?',
                'How would you rate the overall accessibility?'
            ],
            'effectiveness': [
                'Did you accomplish what you set out to do?',
                'How helpful was the information you received?',
                'Did the system answer your questions effectively?',
                'How actionable were the recommendations?',
                'Would you recommend this system to others?'
            ]
        }
    
    def render_testing_dashboard(self) -> None:
        """Render user testing dashboard"""
        st.markdown("## 🧪 User Testing Dashboard")
        
        # Test scenario selection
        st.markdown("### 📋 Select Test Scenario")
        
        scenario_key = st.selectbox(
            "Choose a test scenario:",
            list(self.test_scenarios.keys()),
            format_func=lambda x: self.test_scenarios[x]['name']
        )
        
        if scenario_key:
            self.render_test_scenario(scenario_key)
    
    def render_test_scenario(self, scenario_key: str) -> None:
        """Render specific test scenario"""
        scenario = self.test_scenarios[scenario_key]
        
        st.markdown(f"## 🎯 {scenario['name']}")
        st.markdown(f"**{scenario['description']}**")
        
        # Tasks
        st.markdown("### 📝 Test Tasks")
        for i, task in enumerate(scenario['tasks'], 1):
            task_key = f"task_{scenario_key}_{i}"
            if st.checkbox(f"{i}. {task}", key=task_key):
                st.success(f"✅ Completed: {task}")
            else:
                st.write(f"⏳ {task}")
        
        # Success metrics
        st.markdown("### 🎯 Success Metrics")
        for metric in scenario['success_metrics']:
            st.write(f"• {metric}")
        
        # Feedback collection
        st.markdown("### 💬 Feedback")
        self.render_feedback_form(scenario_key)
    
    def render_feedback_form(self, scenario_key: str) -> None:
        """Render feedback collection form"""
        st.markdown("#### How was your experience?")
        
        # Usability feedback
        st.markdown("**Usability**")
        usability_score = st.slider(
            "Overall ease of use (1-10)",
            min_value=1,
            max_value=10,
            value=5,
            key=f"usability_{scenario_key}"
        )
        
        usability_notes = st.text_area(
            "What made it easy or difficult to use?",
            key=f"usability_notes_{scenario_key}"
        )
        
        # Emotional support feedback
        st.markdown("**Emotional Support**")
        emotional_score = st.slider(
            "How supported did you feel? (1-10)",
            min_value=1,
            max_value=10,
            value=5,
            key=f"emotional_{scenario_key}"
        )
        
        emotional_notes = st.text_area(
            "How did the system make you feel?",
            key=f"emotional_notes_{scenario_key}"
        )
        
        # Accessibility feedback
        st.markdown("**Accessibility**")
        accessibility_score = st.slider(
            "How accessible was the interface? (1-10)",
            min_value=1,
            max_value=10,
            value=5,
            key=f"accessibility_{scenario_key}"
        )
        
        accessibility_notes = st.text_area(
            "Any accessibility issues or improvements?",
            key=f"accessibility_notes_{scenario_key}"
        )
        
        # Effectiveness feedback
        st.markdown("**Effectiveness**")
        effectiveness_score = st.slider(
            "How effective was the system? (1-10)",
            min_value=1,
            max_value=10,
            value=5,
            key=f"effectiveness_{scenario_key}"
        )
        
        effectiveness_notes = st.text_area(
            "Did you accomplish what you wanted to?",
            key=f"effectiveness_notes_{scenario_key}"
        )
        
        # Submit feedback
        if st.button("📤 Submit Feedback", key=f"submit_{scenario_key}"):
            self.save_feedback(scenario_key, {
                'usability_score': usability_score,
                'usability_notes': usability_notes,
                'emotional_score': emotional_score,
                'emotional_notes': emotional_notes,
                'accessibility_score': accessibility_score,
                'accessibility_notes': accessibility_notes,
                'effectiveness_score': effectiveness_score,
                'effectiveness_notes': effectiveness_notes,
                'timestamp': datetime.now().isoformat()
            })
            st.success("Thank you for your feedback!")
    
    def save_feedback(self, scenario_key: str, feedback: Dict[str, Any]) -> None:
        """Save user feedback"""
        if 'user_feedback' not in st.session_state:
            st.session_state.user_feedback = {}
        
        if scenario_key not in st.session_state.user_feedback:
            st.session_state.user_feedback[scenario_key] = []
        
        st.session_state.user_feedback[scenario_key].append(feedback)
    
    def render_feedback_analytics(self) -> None:
        """Render feedback analytics and insights"""
        st.markdown("## 📊 Feedback Analytics")
        
        if 'user_feedback' not in st.session_state or not st.session_state.user_feedback:
            st.info("No feedback data available yet. Complete some test scenarios to see analytics.")
            return
        
        # Overall scores
        st.markdown("### 📈 Overall Scores")
        
        all_scores = {
            'usability': [],
            'emotional': [],
            'accessibility': [],
            'effectiveness': []
        }
        
        for scenario_key, feedback_list in st.session_state.user_feedback.items():
            for feedback in feedback_list:
                all_scores['usability'].append(feedback.get('usability_score', 0))
                all_scores['emotional'].append(feedback.get('emotional_score', 0))
                all_scores['accessibility'].append(feedback.get('accessibility_score', 0))
                all_scores['effectiveness'].append(feedback.get('effectiveness_score', 0))
        
        # Calculate averages
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_usability = sum(all_scores['usability']) / len(all_scores['usability']) if all_scores['usability'] else 0
            st.metric("Usability", f"{avg_usability:.1f}/10")
        
        with col2:
            avg_emotional = sum(all_scores['emotional']) / len(all_scores['emotional']) if all_scores['emotional'] else 0
            st.metric("Emotional Support", f"{avg_emotional:.1f}/10")
        
        with col3:
            avg_accessibility = sum(all_scores['accessibility']) / len(all_scores['accessibility']) if all_scores['accessibility'] else 0
            st.metric("Accessibility", f"{avg_accessibility:.1f}/10")
        
        with col4:
            avg_effectiveness = sum(all_scores['effectiveness']) / len(all_scores['effectiveness']) if all_scores['effectiveness'] else 0
            st.metric("Effectiveness", f"{avg_effectiveness:.1f}/10")
        
        # Detailed feedback analysis
        st.markdown("### 💬 Detailed Feedback")
        
        for scenario_key, feedback_list in st.session_state.user_feedback.items():
            with st.expander(f"📋 {self.test_scenarios[scenario_key]['name']} ({len(feedback_list)} responses)"):
                for i, feedback in enumerate(feedback_list):
                    st.markdown(f"**Response {i+1}**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Usability: {feedback.get('usability_score', 0)}/10")
                        st.write(f"Emotional Support: {feedback.get('emotional_score', 0)}/10")
                    
                    with col2:
                        st.write(f"Accessibility: {feedback.get('accessibility_score', 0)}/10")
                        st.write(f"Effectiveness: {feedback.get('effectiveness_score', 0)}/10")
                    
                    if feedback.get('usability_notes'):
                        st.write(f"**Usability Notes:** {feedback['usability_notes']}")
                    
                    if feedback.get('emotional_notes'):
                        st.write(f"**Emotional Notes:** {feedback['emotional_notes']}")
                    
                    if feedback.get('accessibility_notes'):
                        st.write(f"**Accessibility Notes:** {feedback['accessibility_notes']}")
                    
                    if feedback.get('effectiveness_notes'):
                        st.write(f"**Effectiveness Notes:** {feedback['effectiveness_notes']}")
                    
                    st.markdown("---")

class A/BTestingSystem:
    """System for A/B testing different design approaches"""
    
    def __init__(self):
        self.test_variants = {
            'hero_message': {
                'A': "Your Financial Aid Journey Starts Here",
                'B': "We Understand This Can Feel Overwhelming",
                'C': "Let's Make Financial Aid Simple Together"
            },
            'intake_approach': {
                'A': 'Form-based intake',
                'B': 'Conversational intake',
                'C': 'Progressive disclosure'
            },
            'navigation_style': {
                'A': 'Traditional sidebar',
                'B': 'Card-based navigation',
                'C': 'Wizard-style progression'
            },
            'emotional_support': {
                'A': 'Minimal support messages',
                'B': 'Moderate encouragement',
                'C': 'Comprehensive emotional support'
            }
        }
        
        self.active_tests = {}
    
    def assign_variant(self, test_name: str) -> str:
        """Assign user to a test variant"""
        if test_name not in self.active_tests:
            # Randomly assign variant
            variants = list(self.test_variants[test_name].keys())
            self.active_tests[test_name] = random.choice(variants)
        
        return self.active_tests[test_name]
    
    def render_ab_test_results(self) -> None:
        """Render A/B test results"""
        st.markdown("## 🔬 A/B Test Results")
        
        if not self.active_tests:
            st.info("No active A/B tests. Start testing to see results.")
            return
        
        for test_name, variant in self.active_tests.items():
            st.markdown(f"### 📊 {test_name.replace('_', ' ').title()}")
            st.write(f"**Your variant:** {variant}")
            st.write(f"**Description:** {self.test_variants[test_name][variant]}")
            
            # Mock results (in real implementation, this would track actual metrics)
            st.markdown("**Performance Metrics:**")
            st.write(f"• Engagement: {random.randint(70, 95)}%")
            st.write(f"• Completion: {random.randint(60, 90)}%")
            st.write(f"• Satisfaction: {random.randint(7, 10)}/10")

class UsabilityTestingTools:
    """Tools for conducting usability testing"""
    
    def __init__(self):
        self.task_scenarios = [
            {
                'name': 'Find Financial Aid Information',
                'description': 'You need to understand what financial aid options are available to you.',
                'success_criteria': [
                    'Can find information about grants',
                    'Can find information about loans',
                    'Can find information about scholarships',
                    'Information is clear and understandable'
                ]
            },
            {
                'name': 'Calculate College Costs',
                'description': 'You want to understand the true cost of attending a specific college.',
                'success_criteria': [
                    'Can input school information',
                    'Can input financial information',
                    'Gets accurate cost breakdown',
                    'Understands the results'
                ]
            },
            {
                'name': 'Start FAFSA Application',
                'description': 'You need to begin the FAFSA application process.',
                'success_criteria': [
                    'Can find FAFSA guidance',
                    'Understands the steps involved',
                    'Can start the process',
                    'Feels confident about next steps'
                ]
            },
            {
                'name': 'Get Help with Questions',
                'description': 'You have specific questions about financial aid that you need answered.',
                'success_criteria': [
                    'Can ask questions easily',
                    'Gets relevant answers',
                    'Can ask follow-up questions',
                    'Feels satisfied with the help'
                ]
            }
        ]
    
    def render_usability_test(self) -> None:
        """Render usability testing interface"""
        st.markdown("## 🧪 Usability Testing")
        
        # Task selection
        task_name = st.selectbox(
            "Select a task to test:",
            [task['name'] for task in self.task_scenarios]
        )
        
        if task_name:
            task = next(t for t in self.task_scenarios if t['name'] == task_name)
            self.render_task_test(task)
    
    def render_task_test(self, task: Dict[str, Any]) -> None:
        """Render specific task test"""
        st.markdown(f"### 📝 {task['name']}")
        st.markdown(f"**{task['description']}**")
        
        st.markdown("#### 🎯 Success Criteria")
        for criterion in task['success_criteria']:
            criterion_key = f"criterion_{task['name'].replace(' ', '_')}_{criterion.replace(' ', '_')}"
            if st.checkbox(criterion, key=criterion_key):
                st.success(f"✅ {criterion}")
            else:
                st.write(f"⏳ {criterion}")
        
        # Time tracking
        st.markdown("#### ⏱️ Time Tracking")
        col1, col2 = st.columns(2)
        
        with col1:
            start_time = st.button("⏱️ Start Timer", key=f"start_{task['name']}")
            if start_time:
                st.session_state[f"task_start_{task['name']}"] = datetime.now()
                st.success("Timer started!")
        
        with col2:
            if st.button("⏹️ Stop Timer", key=f"stop_{task['name']}"):
                if f"task_start_{task['name']}" in st.session_state:
                    end_time = datetime.now()
                    start_time = st.session_state[f"task_start_{task['name']}"]
                    duration = (end_time - start_time).total_seconds()
                    st.success(f"Task completed in {duration:.1f} seconds!")
        
        # Difficulty rating
        st.markdown("#### 📊 Task Difficulty")
        difficulty = st.slider(
            "How difficult was this task? (1 = Very Easy, 10 = Very Difficult)",
            min_value=1,
            max_value=10,
            value=5,
            key=f"difficulty_{task['name']}"
        )
        
        # Comments
        comments = st.text_area(
            "Any comments about this task?",
            key=f"comments_{task['name']}"
        )
        
        if st.button("💾 Save Test Results", key=f"save_{task['name']}"):
            self.save_task_results(task, difficulty, comments)
            st.success("Test results saved!")

def create_user_testing_system() -> UserTestingSystem:
    """Factory function to create user testing system"""
    return UserTestingSystem()

def create_ab_testing_system() -> A/BTestingSystem:
    """Factory function to create A/B testing system"""
    return A/BTestingSystem()

def create_usability_testing_tools() -> UsabilityTestingTools:
    """Factory function to create usability testing tools"""
    return UsabilityTestingTools() 