#!/usr/bin/env python3
"""
SmartBorrow - People-First Financial Aid Assistant
A redesigned UI focused on user empathy, intuitive navigation, and proactive assistance.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from smartborrow.rag.rag_service import RAGService
from smartborrow.agents.enhanced_coordinator import EnhancedCoordinatorAgent
from smartborrow.rag.optimized_rag_service import OptimizedRAGService
from smartborrow.retrieval.hybrid_retriever_advanced import create_advanced_hybrid_retriever
from smartborrow.rag.advanced_chunking import create_advanced_chunker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SmartBorrow - Your Financial Aid Journey",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for people-first design
st.markdown("""
<style>
    /* People-First Design System with Adaptive Colors */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        
        /* Adaptive text colors based on background */
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --text-on-light: #1f2937;
        --text-on-dark: #ffffff;
        
        /* Background colors */
        --background-light: #f9fafb;
        --background-white: #ffffff;
        --background-dark: #1f2937;
        --border-color: #e5e7eb;
        
        /* Card and component backgrounds */
        --card-bg-light: #ffffff;
        --card-bg-dark: #374151;
        --input-bg-light: #ffffff;
        --input-bg-dark: #4b5563;
    }
    
    /* Typography */
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* Journey Cards */
    .journey-card {
        background: var(--background-white);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        color: #1f2937 !important;
    }
    
    .journey-card:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        transform: translateY(-2px);
    }
    
    .journey-card.active {
        border-color: var(--success-color);
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    }
    
    /* Action Buttons */
    .action-button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
    }
    
    .action-button.secondary {
        background: var(--background-white);
        color: var(--primary-color);
        border: 2px solid var(--primary-color);
        box-shadow: none;
    }
    
    /* Suggestion buttons styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .action-button.secondary:hover {
        background: var(--primary-color);
        color: white;
    }
    
    /* Progress Indicators */
    .progress-step {
        display: flex;
        align-items: center;
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 12px;
        background: var(--background-light);
    }
    
    .progress-step.completed {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid var(--success-color);
    }
    
    .progress-step.current {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid var(--primary-color);
    }
    
    /* Chat Interface */
    .chat-container {
        background: var(--background-white);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        color: #1f2937 !important;
    }
    
    .user-message {
        background: var(--primary-color);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .ai-message {
        background: var(--background-light);
        color: #1f2937 !important;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        max-width: 80%;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Calculator Interface */
    .calculator-card {
        background: var(--background-white);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .result-highlight {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid var(--warning-color);
        margin: 1rem 0;
    }
    
    /* Force dark text on light backgrounds for all input elements */
    .stTextInput > div > div > input,
    .stTextInput > div > div > input:focus,
    .stTextInput > div > div > input:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > div:focus,
    .stSelectbox > div > div > div:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    .stNumberInput > div > div > input,
    .stNumberInput > div > div > input:focus,
    .stNumberInput > div > div > input:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Adaptive button styling */
    .stButton > button {
        color: var(--text-on-dark) !important;
        background-color: var(--primary-color) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: var(--secondary-color) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Adaptive suggestion buttons */
    .suggestion-button {
        background: var(--card-bg-light);
        color: var(--primary-color);
        border: 2px solid var(--primary-color);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .suggestion-button:hover {
        background: var(--primary-color);
        color: var(--text-on-dark);
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
    }
    
    /* Force dark text for all input elements */
    input, textarea, select {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Specific fix for Streamlit text inputs */
    .stTextInput input {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix for multiselect */
    .stMultiSelect > div > div > div {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Force dark text for all Streamlit components */
    .stTextInput > div > div > input,
    .stTextInput > div > div > input:focus,
    .stTextInput > div > div > input:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stNumberInput > div > div > input,
    .stNumberInput > div > div > input:focus,
    .stNumberInput > div > div > input:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > div:focus,
    .stSelectbox > div > div > div:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    .stMultiSelect > div > div > div,
    .stMultiSelect > div > div > div:focus,
    .stMultiSelect > div > div > div:hover {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix for any remaining text visibility issues */
    .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect {
        color: #1f2937 !important;
    }
    
    /* Ensure all text in Streamlit components is visible */
    .stTextInput *, .stNumberInput *, .stSelectbox *, .stMultiSelect * {
        color: #1f2937 !important;
    }
    
    /* Additional fixes for text visibility */
    .stTextInput > div > div > input::placeholder {
        color: #6b7280 !important;
    }
    
    .stTextInput > div > div > input:focus::placeholder {
        color: #9ca3af !important;
    }
    
    /* Force dark text for any remaining elements */
    .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect, 
    .stTextInput *, .stNumberInput *, .stSelectbox *, .stMultiSelect * {
        color: #1f2937 !important;
    }
    
    /* Override any Streamlit default colors */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stMultiSelect select {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix text color ONLY for specific problematic areas */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix ONLY the chat input and response areas */
    .stTextInput input[placeholder*="How do I qualify"] {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .journey-card {
            padding: 1.5rem;
        }
    }
    
    /* Accessibility */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    
    /* Focus states for keyboard navigation */
    .action-button:focus,
    .journey-card:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }
</style>
""", unsafe_allow_html=True)

class PeopleFirstSmartBorrowApp:
    """People-first SmartBorrow application with empathetic design"""
    
    def __init__(self) -> None:
        self.initialize_services()
        self.initialize_user_journey()
        self.load_user_profile()
    
    def initialize_services(self) -> None:
        """Initialize enhanced multi-agent system and advanced services"""
        try:
            # Initialize enhanced coordinator agent
            self.enhanced_coordinator = EnhancedCoordinatorAgent()
            
            # Initialize optimized RAG service
            self.optimized_rag_service = OptimizedRAGService()
            asyncio.run(self.optimized_rag_service.initialize())
            
            # Initialize advanced hybrid retriever
            self.hybrid_retriever = create_advanced_hybrid_retriever()
            
            # Initialize advanced chunker
            self.advanced_chunker = create_advanced_chunker()
            
            # Keep original RAG service for fallback
            self.rag_service = RAGService()
            self.rag_service.initialize()
            
            st.session_state.services_initialized = True
            logger.info("✅ Enhanced multi-agent system and advanced services initialized successfully")
            
        except Exception as e:
            st.error(f"Error initializing enhanced services: {e}")
            st.session_state.services_initialized = False
    
    def initialize_user_journey(self) -> None:
        """Initialize user journey tracking"""
        if 'user_journey' not in st.session_state:
            st.session_state.user_journey = {
                'stage': 'welcome',
                'completed_steps': [],
                'current_goals': [],
                'pain_points': [],
                'preferences': {}
            }
    
    def load_user_profile(self) -> None:
        """Load or create user profile"""
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {
                'academic_level': None,
                'family_income': None,
                'target_schools': [],
                'financial_goals': [],
                'deadlines': {},
                'documents_needed': [],
                'preferences': {
                    'communication_style': 'supportive',
                    'detail_level': 'moderate',
                    'focus_areas': []
                }
            }
    
    def render_hero_section(self) -> None:
        """Render the hero section with current system status"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: var(--primary-color); margin-bottom: 0.5rem;">🎓 SmartBorrow</h1>
            <p style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 2rem;">
                Your AI-powered financial aid assistant
            </p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 2rem;">
                <span style="background: #dcfce7; color: #166534; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    ✅ RAG System Active
                </span>
                <span style="background: #dbeafe; color: #1e40af; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    🚀 Optimized Performance
                </span>
                <span style="background: #fef3c7; color: #92400e; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    📚 Knowledge Base Ready
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_smart_intake(self) -> None:
        """Render intelligent intake system"""
        st.markdown("## 🤝 Let's Start with Your Situation")
        
        # Smart intake form
        with st.expander("Tell us about your situation", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                academic_level = st.selectbox(
                    "What's your academic level?",
                    ["High school student", "Current college student", "Graduate student", "Parent/Guardian", "Other"],
                    help="This helps us provide the most relevant guidance"
                )
                
                family_income = st.selectbox(
                    "What's your family's approximate annual income?",
                    ["Under $30,000", "$30,000 - $60,000", "$60,000 - $100,000", "$100,000 - $150,000", "Over $150,000", "Prefer not to say"],
                    help="This helps determine eligibility for need-based aid"
                )
            
            with col2:
                goals = st.multiselect(
                    "What are your main financial aid goals?",
                    ["Maximize grants and scholarships", "Minimize student loan debt", "Understand all options", "Get help with applications", "Calculate costs", "Compare schools"],
                    help="Select all that apply"
                )
                
                concerns = st.multiselect(
                    "What concerns you most about financial aid?",
                    ["Complex application process", "High costs", "Loan repayment", "Missing deadlines", "Not qualifying", "Understanding options", "Other"],
                    help="This helps us address your specific worries"
                )
            
            if st.button("🎯 Get My Personalized Plan", type="primary"):
                self.update_user_profile(academic_level, family_income, goals, concerns)
                st.session_state.user_journey['stage'] = 'personalized_plan'
                st.rerun()
    
    def update_user_profile(self, academic_level: str, family_income: str, goals: List[str], concerns: List[str]) -> None:
        """Update user profile with intake information"""
        st.session_state.user_profile.update({
            'academic_level': academic_level,
            'family_income': family_income,
            'financial_goals': goals,
            'pain_points': concerns
        })
    
    def render_personalized_dashboard(self) -> None:
        """Render personalized dashboard based on user profile"""
        profile = st.session_state.user_profile
        
        st.markdown("## 🎯 Your Personalized Financial Aid Dashboard")
        
        # Progress overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Next Deadline", "FAFSA Due", "2 weeks")
        
        with col2:
            st.metric("Estimated Aid", "$12,500", "+$2,300 vs last year")
        
        with col3:
            st.metric("Applications", "3 of 5", "60% complete")
        
        # Action cards based on user profile
        st.markdown("### 📋 Your Next Steps")
        
        if profile['academic_level'] == "High school student":
            self.render_high_school_actions()
        elif profile['academic_level'] == "Current college student":
            self.render_college_student_actions()
        else:
            self.render_general_actions()
    
    def render_high_school_actions(self) -> None:
        """Render actions for high school students"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="journey-card active">
                <h3>📝 Complete FAFSA</h3>
                <p>Your first step to financial aid. We'll guide you through every question.</p>
                <ul>
                    <li>Gather required documents</li>
                    <li>Create FSA ID</li>
                    <li>Complete application</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Start FAFSA Guide", key="fafsa_guide"):
                st.session_state.current_task = "fafsa_guide"
                st.session_state.user_journey['stage'] = 'fafsa_guide'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="journey-card">
                <h3>🎯 Research Scholarships</h3>
                <p>Find scholarships that match your profile and interests.</p>
                <ul>
                    <li>Merit-based opportunities</li>
                    <li>Local scholarships</li>
                    <li>Major-specific awards</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 Find Scholarships", key="scholarships"):
                st.session_state.current_task = "scholarship_search"
                st.session_state.user_journey['stage'] = 'scholarship_search'
                st.rerun()
    
    def render_college_student_actions(self) -> None:
        """Render actions for current college students"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="journey-card active">
                <h3>🔄 Renew FAFSA</h3>
                <p>Don't lose your aid! Renew your FAFSA for next year.</p>
                <ul>
                    <li>Update information</li>
                    <li>Check for changes</li>
                    <li>Submit early</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📅 Renew Now", key="renew_fafsa"):
                st.session_state.current_task = "renew_fafsa"
                st.session_state.user_journey['stage'] = 'renew_fafsa'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="journey-card">
                <h3>💰 Loan Management</h3>
                <p>Understand your current loans and plan for the future.</p>
                <ul>
                    <li>Check loan status</li>
                    <li>Explore repayment options</li>
                    <li>Consider consolidation</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📊 Loan Analysis", key="loan_analysis"):
                st.session_state.current_task = "loan_analysis"
                st.session_state.user_journey['stage'] = 'loan_analysis'
                st.rerun()
    
    def render_general_actions(self) -> None:
        """Render general actions for all users"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="journey-card active">
                <h3>💬 Ask Questions</h3>
                <p>Get personalized answers to your financial aid questions.</p>
                <ul>
                    <li>Eligibility questions</li>
                    <li>Application help</li>
                    <li>Cost calculations</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💭 Start Chat", key="start_chat"):
                st.session_state.current_task = "chat"
                st.session_state.user_journey['stage'] = 'chat'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="journey-card">
                <h3>🧮 Cost Calculator</h3>
                <p>Calculate the true cost of college and your aid options.</p>
                <ul>
                    <li>School comparisons</li>
                    <li>Loan scenarios</li>
                    <li>Repayment planning</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📊 Calculate Costs", key="cost_calculator"):
                st.session_state.current_task = "cost_calculator"
                st.session_state.user_journey['stage'] = 'calculator'
                st.rerun()
    
    def render_conversational_interface(self) -> None:
        """Render conversational AI interface"""
        st.markdown("## 💬 Let's Talk About Your Financial Aid")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            st.markdown("""
            <div class="chat-container">
                <p><strong>SmartBorrow:</strong> Hi! I'm here to help with your financial aid journey. 
                What would you like to know? You can ask me anything about:</p>
                <ul>
                    <li>Grants and scholarships</li>
                    <li>Student loans</li>
                    <li>Application processes</li>
                    <li>Cost calculations</li>
                    <li>Deadlines and requirements</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Chat input
        user_question = st.text_input(
            "What's on your mind?",
            placeholder="e.g., How do I qualify for a Pell Grant?",
            key="chat_input"
        )
        
        # Ask Question button on its own row
        if st.button("Ask Question", disabled=not user_question, type="primary"):
            self.process_chat_question(user_question)
        
        # Also process if suggestion button was clicked
        if user_question and st.session_state.get('process_question', False):
            st.session_state.process_question = False
            self.process_chat_question(user_question)
    
    def process_chat_question(self, question: str) -> None:
        """Process user question using RAG service"""
        with st.spinner("🤖 Analyzing your question..."):
            try:
                # Use the working RAG service directly
                result = self.rag_service.query(question)
                
                # Extract the answer from the result
                if isinstance(result, dict):
                    answer = result.get('answer', str(result))
                    confidence = result.get('confidence', 'medium')
                    sources = result.get('sources', [])
                else:
                    answer = str(result)
                    confidence = 'medium'
                    sources = []
                
                # Display response with information
                source_info = ""
                if sources:
                    # Clean up sources to remove duplicates and format properly
                    unique_sources = list(set([f"📚 {source.get('document_type', 'Unknown')} ({source.get('category', 'general')})" for source in sources]))
                    source_info = f"**Sources:**<br>" + "<br>".join(unique_sources)
                
                # Clean the answer to remove any existing Sources section
                cleaned_answer = answer
                if "**Sources:**" in answer:
                    cleaned_answer = answer.split("**Sources:**")[0].strip()
                
                # Create a properly contained response box with all content inside
                st.markdown(f"""
                <div style="background-color: #f9fafb; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; border-left: 4px solid #2563eb; width: 100%; max-width: 100%;">
                    <div style="color: #2563eb; font-weight: bold; margin-bottom: 0.5rem;">SmartBorrow:</div>
                    <div style="color: #1f2937; line-height: 1.6; margin-bottom: 1rem; white-space: pre-line;">{cleaned_answer}</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">🎯 Confidence: {confidence}</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">{source_info}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add follow-up suggestions
                self.render_follow_up_suggestions(question)
                
            except Exception as e:
                st.error(f"I'm having trouble processing that right now. Error: {e}")
                logger.error(f"Error processing question: {e}")
                
                # Show a helpful fallback message
                st.markdown(f"""
                <div style="background-color: #fef3c7; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; border-left: 4px solid #f59e0b; width: 100%; max-width: 100%; color: #1f2937;">
                    <strong style="color: #f59e0b; display: block; margin-bottom: 0.5rem;">SmartBorrow:</strong>
                    <div style="color: #1f2937;">I'm experiencing technical difficulties. Please try rephrasing your question or try again in a moment.</div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_follow_up_suggestions(self, original_question: str) -> None:
        """Render contextual follow-up suggestions"""
        st.markdown("### 💡 Related Questions You Might Have:")
        
        # Contextual suggestions based on question type
        if "pell grant" in original_question.lower():
            suggestions = [
                "What's the maximum Pell Grant amount?",
                "How do I apply for a Pell Grant?",
                "What's the Expected Family Contribution (EFC)?"
            ]
        elif "loan" in original_question.lower():
            suggestions = [
                "What are current interest rates?",
                "How do I apply for student loans?",
                "What's the difference between subsidized and unsubsidized loans?"
            ]
        else:
            suggestions = [
                "How do I complete the FAFSA?",
                "What scholarships am I eligible for?",
                "How do I calculate my college costs?"
            ]
        
        # Use regular buttons with unique keys
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            with cols[i]:
                # Use a unique key that includes the suggestion text
                button_key = f"suggestion_{i}_{hash(suggestion) % 10000}"
                if st.button(f"💭 {suggestion}", key=button_key):
                    # Process the question immediately
                    self.process_chat_question(suggestion)
    
    def render_cost_calculator(self) -> None:
        """Render interactive cost calculator"""
        st.markdown("## 🧮 College Cost Calculator")
        
        st.markdown("Let's calculate the true cost of college and explore your aid options.")
        
        # Calculator inputs
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 School Information")
            school_name = st.text_input("School Name", placeholder="e.g., University of California")
            tuition = st.number_input("Annual Tuition & Fees", min_value=0, value=15000, step=1000)
            room_board = st.number_input("Room & Board", min_value=0, value=12000, step=1000)
            books_supplies = st.number_input("Books & Supplies", min_value=0, value=1200, step=100)
        
        with col2:
            st.markdown("### 💰 Your Financial Information")
            family_income = st.number_input("Family Annual Income", min_value=0, value=60000, step=1000)
            savings = st.number_input("Available Savings", min_value=0, value=5000, step=1000)
            other_aid = st.number_input("Other Aid/Scholarships", min_value=0, value=0, step=1000)
        
        # Calculate results
        if st.button("📊 Calculate My Costs", type="primary"):
            self.calculate_college_costs(tuition, room_board, books_supplies, family_income, savings, other_aid)
    
    def calculate_college_costs(self, tuition: float, room_board: float, books_supplies: float, 
                              family_income: float, savings: float, other_aid: float) -> None:
        """Calculate and display college costs with smart recommendations"""
        total_cost = tuition + room_board + books_supplies
        estimated_pell = self.estimate_pell_grant(family_income)
        estimated_loans = self.estimate_loan_eligibility(total_cost, family_income)
        
        # Calculate additional costs
        transportation = 1200  # Estimated annual transportation
        personal_expenses = 2000  # Estimated personal expenses
        total_with_extras = total_cost + transportation + personal_expenses
        
        # Display results
        st.markdown("### 📈 Your Cost Breakdown")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Annual Cost", f"${total_cost:,.0f}")
            st.metric("Tuition & Fees", f"${tuition:,.0f}")
            st.metric("Room & Board", f"${room_board:,.0f}")
            st.metric("Books & Supplies", f"${books_supplies:,.0f}")
        
        with col2:
            st.metric("Estimated Pell Grant", f"${estimated_pell:,.0f}")
            st.metric("Other Aid", f"${other_aid:,.0f}")
            st.metric("Available Savings", f"${savings:,.0f}")
            st.metric("Transportation & Personal", f"${transportation + personal_expenses:,.0f}")
        
        with col3:
            net_cost = total_with_extras - estimated_pell - other_aid - savings
            st.metric("Net Cost After Aid", f"${net_cost:,.0f}")
            st.metric("Estimated Loans Needed", f"${estimated_loans:,.0f}")
            st.metric("Monthly Payment (10yr)", f"${estimated_loans/120:,.0f}")
        
        # Smart recommendations based on situation
        st.markdown("### 💡 Smart Recommendations")
        
        if net_cost > 0:
            st.warning(f"You'll need approximately ${net_cost:,.0f} in additional funding.")
            
            # Personalized recommendations
            recommendations = []
            
            if family_income < 50000:
                recommendations.append("🎯 **Apply for state need-based grants** - You likely qualify")
                recommendations.append("🏫 **Check with your school's financial aid office** - They may have additional funds")
            
            if estimated_loans > 0:
                recommendations.append("💰 **Apply for additional scholarships** - Every dollar helps")
                recommendations.append("💼 **Explore work-study opportunities** - Earn while you learn")
                recommendations.append("📚 **Consider community college for first 2 years** - Save significantly")
            
            if savings < 5000:
                recommendations.append("💳 **Look into payment plans** - Many schools offer 0% interest")
                recommendations.append("🏠 **Consider living off-campus** - Often cheaper than dorms")
            
            # Display recommendations
            for rec in recommendations:
                st.info(rec)
            
            # Additional funding options
            st.markdown("### 🎯 Additional Funding Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Federal Aid:**")
                st.markdown("- Direct Subsidized Loans (no interest while in school)")
                st.markdown("- Direct Unsubsidized Loans")
                st.markdown("- Federal Work-Study")
                st.markdown("- State grants (check your state)")
            
            with col2:
                st.markdown("**Alternative Options:**")
                st.markdown("- Private scholarships (fastweb.com, scholarships.com)")
                st.markdown("- Employer tuition assistance")
                st.markdown("- Military benefits (if applicable)")
                st.markdown("- Income-based repayment plans")
        else:
            st.success("🎉 Great news! Your aid covers your costs with money left over.")
            st.info("Consider saving the excess for future years or graduate school.")
        
        # Cost comparison
        st.markdown("### 📊 Cost Comparison")
        
        # Sample schools for comparison
        schools = [
            {"name": "Community College", "tuition": 3000, "room": 0, "total": 3000},
            {"name": "State University", "tuition": 12000, "room": 8000, "total": 20000},
            {"name": "Private University", "tuition": 45000, "room": 12000, "total": 57000}
        ]
        
        comparison_data = []
        for school in schools:
            comparison_data.append({
                "School Type": school["name"],
                "Annual Cost": f"${school['total']:,}",
                "4-Year Total": f"${school['total'] * 4:,}"
            })
        
        st.table(comparison_data)
    
    def estimate_pell_grant(self, family_income: float) -> float:
        """Estimate Pell Grant amount based on family income"""
        if family_income < 30000:
            return 7395  # Maximum Pell Grant 2024-2025
        elif family_income < 60000:
            return 5000
        elif family_income < 100000:
            return 2000
        else:
            return 0
    
    def estimate_loan_eligibility(self, total_cost: float, family_income: float) -> float:
        """Estimate loan eligibility"""
        # Simplified calculation
        if family_income < 50000:
            return min(total_cost * 0.8, 5500)  # Subsidized loan limit
        else:
            return min(total_cost * 0.6, 7500)  # Unsubsidized loan limit
    
    def render_fafsa_guide(self) -> None:
        """Render FAFSA completion guide"""
        st.markdown("## 📝 FAFSA Completion Guide")
        st.markdown("Let's walk through completing your FAFSA step by step.")
        
        steps = [
            {
                "title": "Prepare Documents",
                "description": "Gather all required documents before starting",
                "tasks": [
                    "Social Security Number",
                    "Driver's License",
                    "Tax Returns (2022)",
                    "W-2 Forms",
                    "Bank Statements",
                    "Investment Records"
                ]
            },
            {
                "title": "Create FSA ID",
                "description": "Create your Federal Student Aid ID",
                "tasks": [
                    "Go to fsaid.ed.gov",
                    "Enter personal information",
                    "Create username and password",
                    "Verify email address",
                    "Set up security questions"
                ]
            },
            {
                "title": "Start FAFSA",
                "description": "Begin your FAFSA application",
                "tasks": [
                    "Go to fafsa.gov",
                    "Click 'Start Here'",
                    "Select application year",
                    "Enter student information",
                    "Add parent information"
                ]
            }
        ]
        
        current_step = st.session_state.get('fafsa_step', 0)
        
        if current_step < len(steps):
            step = steps[current_step]
            
            st.markdown(f"### 📝 Step {current_step + 1}: {step['title']}")
            st.markdown(f"**{step['description']}**")
            
            # Task checklist
            st.markdown("#### ✅ Your Checklist:")
            for i, task in enumerate(step['tasks']):
                task_key = f"fafsa_task_{current_step}_{i}"
                if st.checkbox(task, key=task_key):
                    st.success(f"✅ {task}")
                else:
                    st.write(f"⏳ {task}")
            
            # Navigation
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if current_step > 0:
                    if st.button("⬅️ Previous Step", key=f"fafsa_prev_{current_step}"):
                        st.session_state.fafsa_step = current_step - 1
                        st.rerun()
            
            with col2:
                if st.button("💾 Save Progress", key=f"fafsa_save_{current_step}"):
                    st.success("Progress saved!")
            
            with col3:
                if st.button("➡️ Next Step", key=f"fafsa_next_{current_step}"):
                    st.session_state.fafsa_step = current_step + 1
                    st.rerun()
        else:
            st.success("🎉 Congratulations! You've completed the FAFSA guide!")
            st.markdown("### 📋 What's Next?")
            st.markdown("- Save your confirmation number")
            st.markdown("- Check your email for confirmation")
            st.markdown("- Review your Student Aid Report (SAR) when it arrives")
            
            if st.button("🏠 Return to Dashboard"):
                st.session_state.user_journey['stage'] = 'dashboard'
                st.rerun()
    
    def render_scholarship_guide(self) -> None:
        """Render scholarship search guide"""
        st.markdown("## 🎯 Scholarship Search Guide")
        st.markdown("Let's find scholarships that match your profile.")
        
        # Profile builder
        st.markdown("### 🎯 Build Your Scholarship Profile")
        
        col1, col2 = st.columns(2)
        
        with col1:
            gpa = st.slider("GPA", 0.0, 4.0, 3.5, 0.1)
            sat_score = st.number_input("SAT Score (if applicable)", min_value=400, max_value=1600, value=1200)
            act_score = st.number_input("ACT Score (if applicable)", min_value=1, max_value=36, value=20)
        
        with col2:
            activities = st.multiselect(
                "Select activities that apply to you:",
                [
                    "Student government", "Sports teams", "Academic clubs", "Music/Arts",
                    "Community service", "Part-time job", "Internships", "Research projects",
                    "Leadership roles", "Awards and honors", "Volunteer work", "Hobbies"
                ]
            )
            
            demographics = st.multiselect(
                "Select characteristics that apply to you:",
                [
                    "First-generation college student", "Low-income family", "Rural area",
                    "Urban area", "Military family", "Disability", "LGBTQ+", "International student",
                    "Transfer student", "Adult learner", "Single parent", "Foster youth"
                ]
            )
        
        major = st.text_input("Intended Major", placeholder="e.g., Computer Science")
        
        if st.button("🔍 Find Scholarships"):
            st.success("Searching for scholarships that match your profile...")
            
            # Mock scholarship results
            scholarships = [
                {
                    "name": "Academic Excellence Award",
                    "amount": "$5,000",
                    "deadline": "March 15",
                    "requirements": f"3.5+ GPA, {major} major"
                },
                {
                    "name": "First-Generation Student Grant",
                    "amount": "$3,000",
                    "deadline": "April 1",
                    "requirements": "First in family to attend college"
                },
                {
                    "name": "Community Service Scholarship",
                    "amount": "$2,500",
                    "deadline": "May 1",
                    "requirements": "100+ volunteer hours"
                }
            ]
            
            st.markdown("### 📋 Recommended Scholarships")
            
            for scholarship in scholarships:
                with st.expander(f"💰 {scholarship['name']} - {scholarship['amount']}"):
                    st.write(f"**Deadline:** {scholarship['deadline']}")
                    st.write(f"**Requirements:** {scholarship['requirements']}")
                    if st.button(f"📝 Apply for {scholarship['name']}", key=f"apply_{scholarship['name']}"):
                        st.success("Application started! We'll help you track it.")
    
    def render_renewal_guide(self) -> None:
        """Render FAFSA renewal guide"""
        st.markdown("## 🔄 FAFSA Renewal Guide")
        st.markdown("Don't lose your aid! Let's renew your FAFSA for next year.")
        
        st.info("""
        **Renewal is easier than the first application because:**
        - Most information is pre-filled
        - You can update what's changed
        - You can use the IRS Data Retrieval Tool
        """)
        
        steps = [
            "Log into fafsa.gov with your FSA ID",
            "Select the new academic year",
            "Review and update personal information",
            "Update financial information if needed",
            "Add any new schools you're considering",
            "Review and submit your application"
        ]
        
        st.markdown("### 📝 Renewal Steps")
        for i, step in enumerate(steps):
            if st.checkbox(f"{i+1}. {step}", key=f"renewal_step_{i}"):
                st.success(f"✅ {step}")
            else:
                st.write(f"⏳ {step}")
        
        if st.button("🏠 Return to Dashboard"):
            st.session_state.user_journey['stage'] = 'dashboard'
            st.rerun()
    
    def render_loan_analysis(self) -> None:
        """Render loan analysis guide"""
        st.markdown("## 💰 Loan Analysis & Management")
        st.markdown("Let's understand your current loans and plan for the future.")
        
        # Current loan information
        st.markdown("### 📊 Current Loan Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input("Current Loan Balance", min_value=0, value=25000, step=1000)
            st.selectbox("Loan Type", ["Direct Subsidized", "Direct Unsubsidized", "Private Loans"])
            st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0, value=5.5, step=0.1)
        
        with col2:
            st.number_input("Monthly Payment", min_value=0, value=300, step=50)
            st.selectbox("Repayment Plan", ["Standard", "Income-Based", "Graduated", "Extended"])
            st.number_input("Years Remaining", min_value=1, max_value=30, value=10)
        
        if st.button("📊 Analyze My Loans"):
            st.markdown("### 💡 Loan Analysis Results")
            
            st.info("""
            **Your Current Situation:**
            - Total Balance: $25,000
            - Monthly Payment: $300
            - Interest Rate: 5.5%
            - Years Remaining: 10
            """)
            
            st.warning("""
            **Recommendations:**
            - Consider income-based repayment if your income is low
            - Look into loan consolidation if you have multiple loans
            - Check if you qualify for Public Service Loan Forgiveness
            - Consider refinancing if you have good credit
            """)
            
            st.markdown("### 🎯 Next Steps")
            st.markdown("1. **Contact your loan servicer** - They can help with repayment options")
            st.markdown("2. **Check your eligibility** - For forgiveness programs")
            st.markdown("3. **Consider consolidation** - If you have multiple loans")
            st.markdown("4. **Set up auto-pay** - Often reduces interest rate by 0.25%")
        
        if st.button("🏠 Return to Dashboard"):
            st.session_state.user_journey['stage'] = 'dashboard'
            st.rerun()
    
    def render_sidebar(self) -> None:
        """Render helpful sidebar"""
        with st.sidebar:
            st.markdown("## 🎯 Quick Actions")
            
            if st.button("🏠 Dashboard", key="sidebar_dashboard"):
                st.session_state.user_journey['stage'] = 'dashboard'
                st.rerun()
            
            if st.button("💬 Ask Questions", key="sidebar_chat"):
                st.session_state.user_journey['stage'] = 'chat'
                st.rerun()
            
            if st.button("🧮 Cost Calculator", key="sidebar_calculator"):
                st.session_state.user_journey['stage'] = 'calculator'
                st.rerun()
            
            st.markdown("---")
            
            st.markdown("## 📅 Important Deadlines")
            st.info("FAFSA Due: October 1")
            st.info("State Aid: Varies by state")
            st.info("School Deadlines: Check with your school")
            
            st.markdown("---")
            
            st.markdown("## 💡 Tips")
            st.markdown("- Apply early for best aid opportunities")
            st.markdown("- Keep copies of all documents")
            st.markdown("- Check your school's specific deadlines")
            st.markdown("- Don't be afraid to ask for help!")
    
    def run(self) -> None:
        """Run the people-first SmartBorrow application"""
        # Render sidebar
        self.render_sidebar()
        
        # Main content based on user journey stage
        stage = st.session_state.user_journey.get('stage', 'welcome')
        
        if stage == 'welcome':
            self.render_hero_section()
            self.render_smart_intake()
        
        elif stage == 'personalized_plan':
            self.render_personalized_dashboard()
        
        elif stage == 'chat':
            self.render_conversational_interface()
        
        elif stage == 'calculator':
            self.render_cost_calculator()
        
        elif stage == 'dashboard':
            self.render_personalized_dashboard()
        
        elif stage == 'fafsa_guide':
            self.render_fafsa_guide()
        
        elif stage == 'scholarship_search':
            self.render_scholarship_guide()
        
        elif stage == 'renew_fafsa':
            self.render_renewal_guide()
        
        elif stage == 'loan_analysis':
            self.render_loan_analysis()
        
        else:
            self.render_hero_section()
            self.render_smart_intake()

def main() -> None:
    """Main function to run the people-first SmartBorrow app"""
    app = PeopleFirstSmartBorrowApp()
    app.run()

if __name__ == "__main__":
    main() 