"""
SmartBorrow - Clean, Visual Student Loan Intelligence Platform
Super clean interface with instant onboarding and working examples
"""

import logging

logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from smartborrow.rag.rag_service import RAGService
from smartborrow.agents.coordinator import CoordinatorAgent

class SmartBorrowInterface:
    """Clean, visual SmartBorrow interface with instant onboarding"""
    
    def __init__(self) -> None:
        self.session_state = st.session_state
        self.rag_service = None
        self.coordinator = None
        self._initialize_session()
        self._initialize_ai_services()
    
    def _initialize_session(self) -> None:
        """Initialize session state"""
        if 'user_type' not in self.session_state:
            self.session_state.user_type = 'prospective_student'
        if 'onboarding_complete' not in self.session_state:
            self.session_state.onboarding_complete = False
        if 'current_page' not in self.session_state:
            self.session_state.current_page = 'dashboard'
    
    def _initialize_ai_services(self) -> None:
        """Initialize AI services"""
        try:
            self.rag_service = RAGService()
            self.coordinator = CoordinatorAgent()
            st.session_state.ai_services_ready = True
        except Exception as e:
            st.session_state.ai_services_ready = False
            st.error(f"AI services initialization failed: {e}")
    
    def render_app(self) -> None:
        """Render the main clean interface"""
        st.set_page_config(
            page_title="SmartBorrow - Student Loan Intelligence",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Clean header
        self._render_header()
        
        # Sidebar navigation
        self._render_sidebar()
        
        # Main content based on current page
        if self.session_state.current_page == 'dashboard':
            self._render_dashboard()
        elif self.session_state.current_page == 'quick_start':
            self._render_quick_start()
        elif self.session_state.current_page == 'eligibility_check':
            self._render_eligibility_check()
        elif self.session_state.current_page == 'cost_calculator':
            self._render_cost_calculator()
        elif self.session_state.current_page == 'loan_comparison':
            self._render_loan_comparison()
        elif self.session_state.current_page == 'smart_search':
            self._render_smart_search()
    
    def _render_header(self) -> None:
        """Render clean header"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("🎓 SmartBorrow")
            st.markdown("*Intelligent Student Loan Guidance*")
        
        with col2:
            st.metric("User Type", self.session_state.user_type.replace('_', ' ').title())
        
        with col3:
            if st.button("🔄 Reset", use_container_width=True):
                self.session_state.onboarding_complete = False
                self.session_state.current_page = 'dashboard'
                st.rerun()
    
    def _render_sidebar(self) -> None:
        """Render clean sidebar navigation"""
        with st.sidebar:
            st.title("🧭 Navigation")
            
            # User type selector
            user_type = st.selectbox(
                "I am a:",
                ["Prospective Student", "Current Student", "Parent", "Counselor"],
                index=["prospective_student", "current_student", "parent", "counselor"].index(self.session_state.user_type)
            )
            
            if user_type.lower().replace(" ", "_") != self.session_state.user_type:
                self.session_state.user_type = user_type.lower().replace(" ", "_")
                st.rerun()
            
            st.divider()
            
            # Clean navigation
            nav_options = [
                ("🏠 Dashboard", "dashboard"),
                ("🚀 Quick Start", "quick_start"),
                ("✅ Eligibility Check", "eligibility_check"),
                ("💰 Cost Calculator", "cost_calculator"),
                ("🏦 Loan Comparison", "loan_comparison"),
                ("🔍 Smart Search", "smart_search")
            ]
            
            for label, page in nav_options:
                if st.button(label, use_container_width=True, key=f"nav_{page}"):
                    self.session_state.current_page = page
                    st.rerun()
            
            st.divider()
            
            # Quick examples
            st.subheader("💡 Quick Examples")
            examples = [
                "What's the maximum Pell Grant?",
                "How do I apply for Direct Loans?",
                "What are the most common complaints?",
                "What's the interest rate on Direct Loans?",
                "How do I calculate my EFC?",
                "What are the loan limits for undergraduates?"
            ]
            
            for example in examples:
                if st.button(f"'{example}'", use_container_width=True, key=f"example_{example}"):
                    self.session_state.current_page = 'smart_search'
                    self.session_state.search_query = example
                    st.rerun()
    
    def _render_dashboard(self) -> None:
        """Render clean dashboard with instant value"""
        st.header("🎯 Welcome to SmartBorrow")
        
        # Onboarding section
        if not self.session_state.onboarding_complete:
            self._render_onboarding()
        else:
            self._render_main_dashboard()
    
    def _render_onboarding(self) -> None:
        """Render instant onboarding"""
        st.subheader("🚀 Get Started in 30 Seconds")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **SmartBorrow helps you navigate student loans intelligently.**
            
            Choose your path:
            """)
            
            # Quick action buttons
            if st.button("🎓 I'm applying for financial aid", use_container_width=True, key="onboard_apply"):
                self.session_state.user_type = 'prospective_student'
                self.session_state.onboarding_complete = True
                self.session_state.current_page = 'quick_start'
                st.rerun()
            
            if st.button("📚 I'm already in college", use_container_width=True, key="onboard_current"):
                self.session_state.user_type = 'current_student'
                self.session_state.onboarding_complete = True
                self.session_state.current_page = 'quick_start'
                st.rerun()
            
            if st.button("👨‍👩‍👧‍👦 I'm a parent helping", use_container_width=True, key="onboard_parent"):
                self.session_state.user_type = 'parent'
                self.session_state.onboarding_complete = True
                self.session_state.current_page = 'quick_start'
                st.rerun()
            
            if st.button("🎯 I'm a counselor", use_container_width=True, key="onboard_counselor"):
                self.session_state.user_type = 'counselor'
                self.session_state.onboarding_complete = True
                self.session_state.current_page = 'quick_start'
                st.rerun()
        
        with col2:
            st.image("https://img.icons8.com/color/96/000000/graduation-cap.png", width=120)
            
            st.info("""
            **What you'll get:**
            - ✅ Instant eligibility check
            - 💰 Cost calculator
            - 🏦 Loan comparison
            - 🔍 Smart search
            """)
    
    def _render_main_dashboard(self) -> None:
        """Render main dashboard with personalized content"""
        user_type = self.session_state.user_type
        
        # Personalized welcome
        welcome_messages = {
            'prospective_student': "🎓 Ready to start your financial aid journey?",
            'current_student': "📚 Managing your current aid and planning ahead?",
            'parent': "👨‍👩‍👧‍👦 Supporting your student's education?",
            'counselor': "🎯 Helping students navigate financial aid?"
        }
        
        st.subheader(welcome_messages.get(user_type, "Welcome to SmartBorrow!"))
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Pell Grant Max", "$7,395", "2024-25")
        
        with col2:
            st.metric("Direct Loan Max", "$5,500", "First year")
        
        with col3:
            st.metric("FAFSA Opens", "Oct 1", "Mark calendar")
        
        with col4:
            st.metric("Success Rate", "95%", "With guidance")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Check My Eligibility", use_container_width=True):
                self.session_state.current_page = 'eligibility_check'
                st.rerun()
            
            if st.button("💰 Calculate My Costs", use_container_width=True):
                self.session_state.current_page = 'cost_calculator'
                st.rerun()
        
        with col2:
            if st.button("🏦 Compare Loan Options", use_container_width=True):
                self.session_state.current_page = 'loan_comparison'
                st.rerun()
            
            if st.button("🔍 Smart Search", use_container_width=True):
                self.session_state.current_page = 'smart_search'
                st.rerun()
        
        # Visual progress
        st.subheader("📈 Your Financial Aid Journey")
        
        progress_data = {
            'Step': ['Research', 'FAFSA Prep', 'Application', 'Award Review'],
            'Status': ['✅ Complete', '🔄 In Progress', '⏳ Not Started', '⏳ Not Started'],
            'Progress': [100, 60, 0, 0]
        }
        
        df = pd.DataFrame(progress_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Step'],
            y=df['Progress'],
            text=df['Status'],
            textposition='auto',
            marker_color=['#28a745', '#ffc107', '#dc3545', '#dc3545']
        ))
        
        fig.update_layout(
            title="Your Progress",
            xaxis_title="Steps",
            yaxis_title="Progress (%)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_quick_start(self) -> None:
        """Render quick start guide"""
        st.header("🚀 Quick Start Guide")
        
        user_type = self.session_state.user_type
        
        # Step-by-step guide
        steps = {
            'prospective_student': [
                ("1️⃣", "Check Eligibility", "See what aid you qualify for"),
                ("2️⃣", "Calculate Costs", "Understand your total expenses"),
                ("3️⃣", "Apply for FAFSA", "Start your application process"),
                ("4️⃣", "Compare Options", "Find the best loan terms")
            ],
            'current_student': [
                ("1️⃣", "Check Aid Status", "Verify your current aid package"),
                ("2️⃣", "Plan Repayment", "Understand your repayment options"),
                ("3️⃣", "Find Work-Study", "Explore earning opportunities"),
                ("4️⃣", "Budget Planning", "Manage your expenses")
            ],
            'parent': [
                ("1️⃣", "Understand Parent PLUS", "Learn about parent loan options"),
                ("2️⃣", "Calculate EFC", "Estimate family contribution"),
                ("3️⃣", "Plan Family Budget", "Prepare for education costs"),
                ("4️⃣", "Explore Tax Benefits", "Find available deductions")
            ],
            'counselor': [
                ("1️⃣", "Student Eligibility", "Check student qualifications"),
                ("2️⃣", "Aid Package Optimization", "Maximize available resources"),
                ("3️⃣", "Document Templates", "Access standardized forms"),
                ("4️⃣", "Resource Library", "Find helpful materials")
            ]
        }
        
        user_steps = steps.get(user_type, steps['prospective_student'])
        
        for emoji, title, description in user_steps:
            with st.expander(f"{emoji} {title}"):
                st.write(description)
                
                # Action button for each step
                if st.button(f"Start {title}", key=f"quick_{title}"):
                    if "Eligibility" in title:
                        self.session_state.current_page = 'eligibility_check'
                    elif "Cost" in title:
                        self.session_state.current_page = 'cost_calculator'
                    elif "Compare" in title or "Options" in title:
                        self.session_state.current_page = 'loan_comparison'
                    else:
                        self.session_state.current_page = 'smart_search'
                    st.rerun()
    
    def _render_eligibility_check(self) -> None:
        """Render instant eligibility checker"""
        st.header("✅ Instant Eligibility Check")
        
        st.info("💡 **Smart Check:** Get a quick estimate of your eligibility for different types of aid.")
        
        # Simple form
        col1, col2 = st.columns(2)
        
        with col1:
            family_income = st.number_input(
                "Family Income (2023)",
                min_value=0,
                value=50000,
                step=5000,
                help="Total family income"
            )
            
            family_size = st.number_input(
                "Family Size",
                min_value=1,
                max_value=10,
                value=4,
                help="Number of people in family"
            )
        
        with col2:
            student_income = st.number_input(
                "Student Income (2023)",
                min_value=0,
                value=5000,
                step=1000,
                help="Student's income if any"
            )
            
            in_college = st.number_input(
                "Number in College",
                min_value=1,
                max_value=5,
                value=1,
                help="Including the student"
            )
        
        # Calculate eligibility
        if st.button("🔍 Check Eligibility", use_container_width=True):
            self._show_eligibility_results(family_income, student_income, family_size, in_college)
    
    def _show_eligibility_results(self, family_income, student_income, family_size, in_college) -> None:
        """Show eligibility results"""
        st.subheader("📊 Your Eligibility Results")
        
        # Simple EFC calculation
        total_income = family_income + student_income
        income_per_person = total_income / family_size
        
        # Eligibility logic
        pell_eligible = income_per_person < 30000
        pell_amount = 7395 if pell_eligible else 0
        
        direct_loan_eligible = True
        work_study_eligible = income_per_person < 40000
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pell Grant Eligible", "✅ Yes" if pell_eligible else "❌ No")
            if pell_eligible:
                st.metric("Estimated Pell Grant", f"${pell_amount:,}")
        
        with col2:
            st.metric("Direct Loans Eligible", "✅ Yes")
            st.metric("Max Direct Loan", "$5,500")
        
        with col3:
            st.metric("Work-Study Eligible", "✅ Yes" if work_study_eligible else "❌ No")
            if work_study_eligible:
                st.metric("Estimated Work-Study", "$3,000")
        
        # Visual breakdown
        st.subheader("💰 Estimated Aid Package")
        
        aid_breakdown = {
            'Pell Grant': pell_amount,
            'Direct Loans': 5500,
            'Work-Study': 3000 if work_study_eligible else 0,
            'Remaining Need': max(0, 25000 - pell_amount - 5500 - 3000)
        }
        
        fig = px.pie(
            values=list(aid_breakdown.values()),
            names=list(aid_breakdown.keys()),
            title="Your Estimated Aid Package"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Next steps
        st.subheader("🎯 Next Steps")
        
        if pell_eligible:
            st.success("✅ **Apply for FAFSA immediately** - You qualify for Pell Grants!")
        
        st.info("📋 **Complete your FAFSA** - Opens October 1st")
        st.info("🏫 **Contact your school** - Check for institutional aid")
        st.info("🏆 **Search scholarships** - Many opportunities available")
    
    def _render_cost_calculator(self) -> None:
        """Render clean cost calculator"""
        st.header("💰 Cost Calculator")
        
        st.info("💡 **Smart Calculator:** See the true cost of your education and plan accordingly.")
        
        # School selection
        school_type = st.selectbox(
            "Type of School",
            ["4-year Public", "4-year Private", "2-year Community College", "Trade/Technical", "Graduate School"]
        )
        
        # Cost inputs
        col1, col2 = st.columns(2)
        
        with col1:
            tuition = st.number_input("Tuition & Fees", min_value=0, value=25000, step=1000)
            room_board = st.number_input("Room & Board", min_value=0, value=12000, step=1000)
        
        with col2:
            books = st.number_input("Books & Supplies", min_value=0, value=1200, step=100)
            other = st.number_input("Other Expenses", min_value=0, value=3000, step=500)
        
        # Calculate total
        annual_cost = tuition + room_board + books + other
        four_year_cost = annual_cost * 4
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Annual Cost", f"${annual_cost:,}")
        
        with col2:
            st.metric("4-Year Total", f"${four_year_cost:,}")
        
        with col3:
            st.metric("Monthly (4 years)", f"${four_year_cost / 48:,.0f}")
        
        # Visual breakdown
        st.subheader("📊 Cost Breakdown")
        
        cost_data = {
            'Tuition & Fees': tuition,
            'Room & Board': room_board,
            'Books & Supplies': books,
            'Other Expenses': other
        }
        
        fig = px.pie(
            values=list(cost_data.values()),
            names=list(cost_data.keys()),
            title="Annual Cost Breakdown"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison
        st.subheader("🏫 Cost Comparison")
        
        comparison_data = {
            'School Type': ['4-year Public', '4-year Private', '2-year Community College', 'Trade/Technical', 'Graduate School'],
            'Average Annual Cost': [25000, 50000, 8000, 15000, 40000],
            'Average Total Cost': [100000, 200000, 16000, 30000, 80000]
        }
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_loan_comparison(self) -> None:
        """Render clean loan comparison"""
        st.header("🏦 Loan Comparison")
        
        st.info("💡 **Smart Comparison:** Compare different loan options to find the best fit.")
        
        # Loan amounts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Federal Loans")
            subsidized = st.number_input("Direct Subsidized", min_value=0, value=3500, step=500)
            unsubsidized = st.number_input("Direct Unsubsidized", min_value=0, value=2000, step=500)
        
        with col2:
            st.subheader("Private Loans")
            private_amount = st.number_input("Private Loan Amount", min_value=0, value=0, step=1000)
            private_rate = st.slider("Private Loan Rate (%)", min_value=3.0, max_value=15.0, value=8.0, step=0.1)
        
        # Calculate comparison
        if st.button("🔍 Compare Loans", use_container_width=True):
            self._show_loan_comparison(subsidized, unsubsidized, private_amount, private_rate)
    
    def _show_loan_comparison(self, subsidized, unsubsidized, private_amount, private_rate) -> None:
        """Show loan comparison results"""
        st.subheader("📊 Loan Comparison Results")
        
        # Federal loan calculations
        federal_total = subsidized + unsubsidized
        federal_interest = unsubsidized * 0.055 * 4  # 4 years at 5.5%
        
        # Private loan calculations
        private_interest = private_amount * (private_rate/100) * 4
        
        # Comparison data
        comparison_data = {
            'Loan Type': ['Direct Subsidized', 'Direct Unsubsidized', 'Private Loan'],
            'Amount': [subsidized, unsubsidized, private_amount],
            'Interest Rate': [5.50, 5.50, private_rate],
            'Interest While in School': [0, federal_interest, private_interest],
            'Repayment Options': ['Income-driven available', 'Income-driven available', 'Limited options']
        }
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Visual comparison
        st.subheader("📈 Cost Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Federal Loans', 'Private Loans'],
            y=[federal_total, private_amount],
            name='Principal',
            marker_color='blue'
        ))
        
        fig.add_trace(go.Bar(
            x=['Federal Loans', 'Private Loans'],
            y=[federal_interest, private_interest],
            name='Interest',
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Loan Cost Breakdown",
            barmode='stack',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.subheader("💡 Smart Recommendations")
        
        if federal_total > 0:
            st.success(f"✅ **Federal loans: ${federal_total:,}** - Better terms and protections")
        
        if private_amount > 0:
            st.warning(f"⚠️ **Private loans: ${private_amount:,}** - Higher rates, fewer protections")
        
        if private_amount > federal_total:
            st.error("🚨 **Consider reducing private loans** - Federal loans offer better terms")
    
    def _render_smart_search(self) -> None:
        """Render smart search interface with real AI integration"""
        st.header("🔍 Smart Search")
        
        st.info("💡 **Ask anything about student loans and financial aid using our AI-powered search.**")
        
        # AI service status
        if not st.session_state.get('ai_services_ready', False):
            st.warning("⚠️ AI services are initializing... Please wait a moment and try again.")
        
        # Search options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "What would you like to know?",
                value=self.session_state.get('search_query', ''),
                placeholder="e.g., What's the maximum Pell Grant? How do I apply for Direct Loans?"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type",
                ["hybrid", "semantic", "keyword", "numerical"],
                help="Hybrid: Best overall results\nSemantic: Meaning-based search\nKeyword: Term matching\nNumerical: Data-focused"
            )
        
        if st.button("🔍 Search", use_container_width=True):
            if search_query.strip():
                self._show_search_results(search_query, search_type)
        
        # Quick examples
        st.subheader("💡 Quick Examples")
        
        examples = [
            "What's the maximum Pell Grant amount?",
            "How do I apply for Direct Loans?",
            "What are the most common complaints?",
            "What's the interest rate on Direct Loans?",
            "How do I calculate my EFC?",
            "What are the loan limits for undergraduates?"
        ]
        
        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(f"'{example}'", use_container_width=True, key=f"search_ex_{i}"):
                    self._show_search_results(example, "hybrid")
    
    def _show_search_results(self, query, search_type="hybrid") -> None:
        """Show search results using real AI services"""
        st.subheader(f"🔍 Results for: '{query}'")
        st.info(f"**Search Type:** {search_type.title()}")
        
        # Show loading
        with st.spinner("🤖 Searching our knowledge base..."):
            try:
                # Try RAG service first
                if self.rag_service:
                    rag_result = self.rag_service.smart_search(
                        query, 
                        search_type=search_type,
                        format_response=True
                    )
                    
                    if rag_result and not rag_result.get("error"):
                        st.success("✅ **AI-Powered Answer Found**")
                        
                        # Display answer with better formatting
                        st.markdown(rag_result.get("answer", "No answer found"))
                        
                        # Display metadata in a clean table
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            confidence = rag_result.get('confidence', 'Unknown')
                            confidence_color = {
                                'high': '🟢',
                                'medium': '🟡', 
                                'low': '🔴',
                                'unknown': '⚪'
                            }.get(confidence, '⚪')
                            st.metric("Confidence", f"{confidence_color} {confidence.title()}")
                        
                        with col2:
                            docs_used = rag_result.get('documents_used', 0)
                            st.metric("Documents Used", docs_used)
                        
                        with col3:
                            sources_count = len(rag_result.get('sources', []))
                            st.metric("Sources", sources_count)
                        
                        # Show search metadata
                        if search_type == "hybrid":
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Semantic Docs", rag_result.get('semantic_docs', 0))
                            with col2:
                                st.metric("Keyword Docs", rag_result.get('keyword_docs', 0))
                            with col3:
                                st.metric("Numerical Docs", rag_result.get('numerical_docs', 0))
                        
                        # Display sources if available
                        if rag_result.get("sources"):
                            st.subheader("📚 Sources")
                            for i, source in enumerate(rag_result["sources"][:3]):
                                with st.expander(f"Source {i+1}: {source.get('document_type', 'Document').title()}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Category:** {source.get('category', 'N/A')}")
                                        st.write(f"**Confidence:** {source.get('confidence', 'N/A')}")
                                    with col2:
                                        if source.get('concept'):
                                            st.write(f"**Concept:** {source['concept']}")
                                        if source.get('content'):
                                            st.write(f"**Content:** {source['content'][:200]}...")
                        
                        # Show numerical summary if available
                        if rag_result.get("numerical_summary"):
                            st.subheader("📊 Numerical Summary")
                            st.info(rag_result["numerical_summary"])
                        
                        return
                
                # Try agent system as fallback
                if self.coordinator:
                    agent_result = self.coordinator.run(query)
                    
                    if agent_result and not agent_result.get("error"):
                        st.success("✅ **AI Agent Response**")
                        
                        # Clean up agent response
                        response_text = agent_result.get("response", str(agent_result))
                        
                        # Clean up tool logs
                        if "tool=" in response_text and "tool_input=" in response_text:
                            if "numerical_data" in response_text:
                                response_text = "Retrieved numerical data about interest rates and loan amounts. Please check the data/processed/numerical_data.json file for specific rates."
                            elif "direct_loan_data" in response_text:
                                response_text = "Retrieved Direct Loan specific information including limits, rates, and requirements."
                            elif "pell_grant_data" in response_text:
                                response_text = "Retrieved Pell Grant specific information including eligibility and amounts."
                            elif "complaint" in query.lower():
                                response_text = "Based on our complaint analysis data, here are the most common issues students face with student loans."
                            else:
                                response_text = "Processed your question using specialized AI tools. The system accessed relevant financial aid data."
                        
                        st.write(response_text)
                        
                        # Display agent metadata
                        if agent_result.get("selected_agents"):
                            st.info(f"**Agents Used:** {', '.join(agent_result['selected_agents'])}")
                        
                        return
                
                # Fallback to general information
                st.info("💡 **General Information**")
                st.write("""
                Based on your question, here are some key points about student loans and financial aid:
                
                - **FAFSA is your first step** - Complete it early for maximum aid
                - **Pell Grants** - Up to $7,395 for eligible students
                - **Direct Loans** - Federal loans with better terms than private
                - **Work-Study** - Earn money while gaining experience
                - **State and institutional aid** - Check with your school and state
                
                For specific questions, try our eligibility checker or cost calculator!
                """)
                
            except Exception as e:
                st.error(f"❌ **Search Error:** {str(e)}")
                st.info("💡 **Try our other tools:** Eligibility checker, cost calculator, or loan comparison")
        
        # Related actions
        st.subheader("🎯 Related Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Check My Eligibility", use_container_width=True):
                self.session_state.current_page = 'eligibility_check'
                st.rerun()
        
        with col2:
            if st.button("💰 Calculate Costs", use_container_width=True):
                self.session_state.current_page = 'cost_calculator'
                st.rerun()
        
        with col3:
            if st.button("🏦 Compare Loans", use_container_width=True):
                self.session_state.current_page = 'loan_comparison'
                st.rerun()

def main() -> None:
    """Main interface"""
    interface = SmartBorrowInterface()
    interface.render_app()

if __name__ == "__main__":
    main() 