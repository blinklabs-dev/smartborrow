"""
SmartBorrow Financial Aid Wizard
Intelligent intake with adaptive forms and real-time eligibility checking
"""

import logging

logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from smartborrow.rag.rag_service import RAGService
from smartborrow.agents.coordinator import CoordinatorAgent

class FinancialAidWizard:
    """Intelligent financial aid application wizard"""
    
    def __init__(self) -> None:
        self.rag_service = None
        self.coordinator = None
        self.session_state = st.session_state
        self._initialize_services()
        
    def _initialize_services(self) -> None:
        """Initialize AI services"""
        try:
            self.rag_service = RAGService()
            self.coordinator = CoordinatorAgent()
        except Exception as e:
            st.error(f"Service initialization failed: {e}")
    
    def render_wizard(self) -> None:
        """Render the main wizard interface"""
        st.set_page_config(
            page_title="Financial Aid Wizard - SmartBorrow",
            page_icon="📋",
            layout="wide"
        )
        
        st.title("📋 Financial Aid Application Wizard")
        st.markdown("*Let's guide you through your financial aid journey step by step*")
        
        # Initialize wizard state
        if 'wizard_step' not in self.session_state:
            self.session_state.wizard_step = 'welcome'
        if 'user_profile' not in self.session_state:
            self.session_state.user_profile = {}
        
        # Render current step
        if self.session_state.wizard_step == 'welcome':
            self._render_welcome_step()
        elif self.session_state.wizard_step == 'basic_info':
            self._render_basic_info_step()
        elif self.session_state.wizard_step == 'financial_info':
            self._render_financial_info_step()
        elif self.session_state.wizard_step == 'academic_info':
            self._render_academic_info_step()
        elif self.session_state.wizard_step == 'eligibility_check':
            self._render_eligibility_check_step()
        elif self.session_state.wizard_step == 'recommendations':
            self._render_recommendations_step()
        elif self.session_state.wizard_step == 'application_plan':
            self._render_application_plan_step()
        elif self.session_state.wizard_step == 'document_checklist':
            self._render_document_checklist_step()
    
    def _render_welcome_step(self) -> None:
        """Render welcome and user type selection"""
        st.header("🎓 Welcome to Your Financial Aid Journey")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Let's get you started on the right path!** 
            
            This wizard will help you:
            - ✅ Determine your eligibility for different types of aid
            - 💰 Calculate your expected family contribution (EFC)
            - 📋 Create a personalized application plan
            - 🏆 Find scholarships and grants you qualify for
            - 📊 Compare different aid packages
            """)
            
            st.info("**Smart Tip:** The more accurate information you provide, the better we can personalize your recommendations!")
        
        with col2:
            st.image("https://img.icons8.com/color/96/000000/graduation-cap.png", width=120)
        
        st.divider()
        
        # User type selection
        st.subheader("👤 Tell us about yourself")
        user_type = st.selectbox(
            "I am a:",
            ["High School Student", "Current College Student", "Returning Student", "Graduate Student", "Parent/Guardian"],
            help="This helps us provide the most relevant guidance"
        )
        
        # Quick eligibility preview
        if user_type:
            self.session_state.user_profile['user_type'] = user_type
            self._show_quick_eligibility_preview(user_type)
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start Over", use_container_width=True):
                self.session_state.wizard_step = 'welcome'
                self.session_state.user_profile = {}
                st.rerun()
        
        with col2:
            if st.button("➡️ Continue to Basic Information", use_container_width=True):
                self.session_state.wizard_step = 'basic_info'
                st.rerun()
    
    def _show_quick_eligibility_preview(self, user_type: str) -> None:
        """Show quick eligibility preview based on user type"""
        st.subheader("🔍 Quick Eligibility Preview")
        
        eligibility_info = {
            "High School Student": {
                "pell_grant": "Likely eligible",
                "direct_loans": "Available",
                "work_study": "Available",
                "scholarships": "Many opportunities"
            },
            "Current College Student": {
                "pell_grant": "Check renewal",
                "direct_loans": "Available",
                "work_study": "Apply early",
                "scholarships": "Continue searching"
            },
            "Returning Student": {
                "pell_grant": "May be eligible",
                "direct_loans": "Available",
                "work_study": "Limited availability",
                "scholarships": "Adult learner specific"
            },
            "Graduate Student": {
                "pell_grant": "Not eligible",
                "direct_loans": "Grad PLUS available",
                "work_study": "Limited",
                "scholarships": "Graduate specific"
            },
            "Parent/Guardian": {
                "pell_grant": "For student",
                "direct_loans": "Parent PLUS",
                "work_study": "For student",
                "scholarships": "Family scholarships"
            }
        }
        
        info = eligibility_info.get(user_type, {})
        
        cols = st.columns(4)
        with cols[0]:
            st.metric("Pell Grant", info.get("pell_grant", "Check eligibility"))
        with cols[1]:
            st.metric("Direct Loans", info.get("direct_loans", "Available"))
        with cols[2]:
            st.metric("Work-Study", info.get("work_study", "Limited"))
        with cols[3]:
            st.metric("Scholarships", info.get("scholarships", "Many available"))
    
    def _render_basic_info_step(self) -> None:
        """Render basic information collection step"""
        st.header("👤 Basic Information")
        
        # Personal information
        st.subheader("Personal Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", value=self.session_state.user_profile.get('first_name', ''))
            last_name = st.text_input("Last Name", value=self.session_state.user_profile.get('last_name', ''))
            email = st.text_input("Email Address", value=self.session_state.user_profile.get('email', ''))
            phone = st.text_input("Phone Number", value=self.session_state.user_profile.get('phone', ''))
        
        with col2:
            date_of_birth = st.date_input("Date of Birth", value=self.session_state.user_profile.get('date_of_birth'))
            citizenship = st.selectbox(
                "Citizenship Status",
                ["U.S. Citizen", "Permanent Resident", "International Student", "Other"],
                index=0
            )
            marital_status = st.selectbox(
                "Marital Status",
                ["Single", "Married", "Divorced", "Separated", "Widowed"],
                index=0
            )
        
        # Address information
        st.subheader("Address Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            street_address = st.text_input("Street Address", value=self.session_state.user_profile.get('street_address', ''))
            city = st.text_input("City", value=self.session_state.user_profile.get('city', ''))
        
        with col2:
            state = st.selectbox("State", ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"])
            zip_code = st.text_input("ZIP Code", value=self.session_state.user_profile.get('zip_code', ''))
        
        # Save to session state
        self.session_state.user_profile.update({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'date_of_birth': date_of_birth,
            'citizenship': citizenship,
            'marital_status': marital_status,
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_code': zip_code
        })
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'welcome'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Progress", use_container_width=True):
                st.success("Progress saved!")
        
        with col3:
            if st.button("➡️ Continue to Financial Information", use_container_width=True):
                self.session_state.wizard_step = 'financial_info'
                st.rerun()
    
    def _render_financial_info_step(self) -> None:
        """Render financial information collection with smart guidance"""
        st.header("💰 Financial Information")
        
        st.info("💡 **Smart Tip:** This information helps calculate your Expected Family Contribution (EFC) and determine your eligibility for need-based aid.")
        
        # Income information
        st.subheader("Income Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            student_income = st.number_input(
                "Student's Income (2023)",
                min_value=0,
                value=self.session_state.user_profile.get('student_income', 0),
                help="Include wages, salaries, tips, etc."
            )
            
            parent_income = st.number_input(
                "Parent's Income (2023)",
                min_value=0,
                value=self.session_state.user_profile.get('parent_income', 0),
                help="If dependent student"
            )
        
        with col2:
            spouse_income = st.number_input(
                "Spouse's Income (2023)",
                min_value=0,
                value=self.session_state.user_profile.get('spouse_income', 0),
                help="If married"
            )
            
            other_income = st.number_input(
                "Other Income (2023)",
                min_value=0,
                value=self.session_state.user_profile.get('other_income', 0),
                help="Interest, dividends, etc."
            )
        
        # Asset information
        st.subheader("Asset Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cash_savings = st.number_input(
                "Cash and Savings",
                min_value=0,
                value=self.session_state.user_profile.get('cash_savings', 0)
            )
            
            investments = st.number_input(
                "Investments",
                min_value=0,
                value=self.session_state.user_profile.get('investments', 0)
            )
        
        with col2:
            real_estate = st.number_input(
                "Real Estate (excluding primary residence)",
                min_value=0,
                value=self.session_state.user_profile.get('real_estate', 0)
            )
            
            business_value = st.number_input(
                "Business/Farm Net Worth",
                min_value=0,
                value=self.session_state.user_profile.get('business_value', 0)
            )
        
        # Family size
        st.subheader("Family Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            family_size = st.number_input(
                "Number of people in family",
                min_value=1,
                max_value=10,
                value=self.session_state.user_profile.get('family_size', 1)
            )
            
            number_in_college = st.number_input(
                "Number in college (including student)",
                min_value=1,
                max_value=5,
                value=self.session_state.user_profile.get('number_in_college', 1)
            )
        
        with col2:
            # Show EFC estimate
            total_income = student_income + parent_income + spouse_income + other_income
            total_assets = cash_savings + investments + real_estate + business_value
            
            st.metric("Total Income", f"${total_income:,}")
            st.metric("Total Assets", f"${total_assets:,}")
            
            # Quick EFC estimate
            if total_income > 0:
                estimated_efc = self._calculate_quick_efc(total_income, total_assets, family_size, number_in_college)
                st.metric("Estimated EFC", f"${estimated_efc:,}", "Quick estimate")
        
        # Save to session state
        self.session_state.user_profile.update({
            'student_income': student_income,
            'parent_income': parent_income,
            'spouse_income': spouse_income,
            'other_income': other_income,
            'cash_savings': cash_savings,
            'investments': investments,
            'real_estate': real_estate,
            'business_value': business_value,
            'family_size': family_size,
            'number_in_college': number_in_college
        })
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'basic_info'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Progress", use_container_width=True):
                st.success("Progress saved!")
        
        with col3:
            if st.button("➡️ Continue to Academic Information", use_container_width=True):
                self.session_state.wizard_step = 'academic_info'
                st.rerun()
    
    def _calculate_quick_efc(self, income: float, assets: float, family_size: int, in_college: int) -> int:
        """Calculate quick EFC estimate"""
        # Simplified EFC calculation
        # This is a rough estimate - actual FAFSA calculation is more complex
        
        # Income protection allowance (simplified)
        income_protection = 25000 + (family_size - 1) * 9000
        
        # Asset protection allowance (simplified)
        asset_protection = 7000 + (family_size - 1) * 3000
        
        # Available income
        available_income = max(0, income - income_protection)
        
        # Available assets
        available_assets = max(0, assets - asset_protection)
        
        # Contribution from income (simplified)
        income_contribution = available_income * 0.22
        
        # Contribution from assets (simplified)
        asset_contribution = available_assets * 0.05
        
        # Total EFC
        efc = income_contribution + asset_contribution
        
        # Divide by number in college
        if in_college > 1:
            efc = efc / in_college
        
        return int(max(0, efc))
    
    def _render_academic_info_step(self) -> None:
        """Render academic information collection"""
        st.header("📚 Academic Information")
        
        # School information
        st.subheader("School Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            school_type = st.selectbox(
                "Type of School",
                ["4-year Public", "4-year Private", "2-year Community College", "Trade/Technical", "Graduate School"],
                index=0
            )
            
            enrollment_status = st.selectbox(
                "Enrollment Status",
                ["Full-time", "Part-time", "Not yet enrolled"],
                index=0
            )
        
        with col2:
            academic_year = st.selectbox(
                "Academic Year",
                ["2024-25", "2025-26", "2026-27"],
                index=0
            )
            
            degree_program = st.text_input(
                "Degree Program",
                value=self.session_state.user_profile.get('degree_program', ''),
                help="e.g., Bachelor of Science in Computer Science"
            )
        
        # Cost information
        st.subheader("Cost Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tuition_fees = st.number_input(
                "Tuition and Fees",
                min_value=0,
                value=self.session_state.user_profile.get('tuition_fees', 0)
            )
            
            room_board = st.number_input(
                "Room and Board",
                min_value=0,
                value=self.session_state.user_profile.get('room_board', 0)
            )
        
        with col2:
            books_supplies = st.number_input(
                "Books and Supplies",
                min_value=0,
                value=self.session_state.user_profile.get('books_supplies', 0)
            )
            
            other_expenses = st.number_input(
                "Other Expenses",
                min_value=0,
                value=self.session_state.user_profile.get('other_expenses', 0)
            )
        
        # Show total cost
        total_cost = tuition_fees + room_board + books_supplies + other_expenses
        st.metric("Total Cost of Attendance", f"${total_cost:,}")
        
        # Save to session state
        self.session_state.user_profile.update({
            'school_type': school_type,
            'enrollment_status': enrollment_status,
            'academic_year': academic_year,
            'degree_program': degree_program,
            'tuition_fees': tuition_fees,
            'room_board': room_board,
            'books_supplies': books_supplies,
            'other_expenses': other_expenses,
            'total_cost': total_cost
        })
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'financial_info'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Progress", use_container_width=True):
                st.success("Progress saved!")
        
        with col3:
            if st.button("➡️ Check Eligibility", use_container_width=True):
                self.session_state.wizard_step = 'eligibility_check'
                st.rerun()
    
    def _render_eligibility_check_step(self) -> None:
        """Render eligibility checking with AI-powered analysis"""
        st.header("✅ Eligibility Analysis")
        
        # Calculate EFC
        profile = self.session_state.user_profile
        efc = self._calculate_quick_efc(
            profile.get('student_income', 0) + profile.get('parent_income', 0) + profile.get('spouse_income', 0) + profile.get('other_income', 0),
            profile.get('cash_savings', 0) + profile.get('investments', 0) + profile.get('real_estate', 0) + profile.get('business_value', 0),
            profile.get('family_size', 1),
            profile.get('number_in_college', 1)
        )
        
        # Display eligibility results
        st.subheader("📊 Your Eligibility Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Expected Family Contribution (EFC)", f"${efc:,}")
        
        with col2:
            total_cost = profile.get('total_cost', 0)
            need = max(0, total_cost - efc)
            st.metric("Financial Need", f"${need:,}")
        
        with col3:
            if efc <= 5846:  # 2024-25 Pell Grant threshold
                pell_eligible = "Yes"
                pell_color = "green"
            else:
                pell_eligible = "No"
                pell_color = "red"
            st.metric("Pell Grant Eligible", pell_eligible)
        
        # Eligibility breakdown
        st.subheader("🎯 Aid Eligibility Breakdown")
        
        eligibility_data = {
            'Aid Type': ['Pell Grant', 'Direct Loans', 'Work-Study', 'State Grants', 'Institutional Aid'],
            'Eligible': [
                'Yes' if efc <= 5846 else 'No',
                'Yes',
                'Yes' if need > 0 else 'Limited',
                'Check State',
                'Check School'
            ],
            'Estimated Amount': [
                f"${min(7395, max(0, 7395 - efc * 0.5)):,}" if efc <= 5846 else "$0",
                f"${min(5500, need):,}",
                f"${min(3000, need):,}" if need > 0 else "$0",
                "Varies",
                "Varies"
            ]
        }
        
        df = pd.DataFrame(eligibility_data)
        st.dataframe(df, use_container_width=True)
        
        # Visual representation
        st.subheader("📈 Aid Package Visualization")
        
        aid_breakdown = {
            'Pell Grant': min(7395, max(0, 7395 - efc * 0.5)) if efc <= 5846 else 0,
            'Direct Loans': min(5500, need),
            'Work-Study': min(3000, need) if need > 0 else 0,
            'Remaining Need': max(0, need - min(7395, max(0, 7395 - efc * 0.5)) - min(5500, need) - min(3000, need))
        }
        
        fig = px.pie(
            values=list(aid_breakdown.values()),
            names=list(aid_breakdown.keys()),
            title="Estimated Aid Package Breakdown"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'academic_info'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Results", use_container_width=True):
                st.success("Results saved!")
        
        with col3:
            if st.button("➡️ View Recommendations", use_container_width=True):
                self.session_state.wizard_step = 'recommendations'
                st.rerun()
    
    def _render_recommendations_step(self) -> None:
        """Render personalized recommendations"""
        st.header("💡 Personalized Recommendations")
        
        profile = self.session_state.user_profile
        efc = self._calculate_quick_efc(
            profile.get('student_income', 0) + profile.get('parent_income', 0) + profile.get('spouse_income', 0) + profile.get('other_income', 0),
            profile.get('cash_savings', 0) + profile.get('investments', 0) + profile.get('real_estate', 0) + profile.get('business_value', 0),
            profile.get('family_size', 1),
            profile.get('number_in_college', 1)
        )
        
        # Priority recommendations
        st.subheader("🎯 Priority Actions")
        
        recommendations = []
        
        if efc <= 5846:
            recommendations.append({
                'priority': 'High',
                'action': 'Apply for FAFSA immediately',
                'reason': 'You qualify for Pell Grants - apply early for maximum aid',
                'deadline': 'October 1st - June 30th'
            })
        
        if profile.get('total_cost', 0) > 0:
            recommendations.append({
                'priority': 'High',
                'action': 'Research institutional scholarships',
                'reason': 'Contact your school\'s financial aid office for additional aid',
                'deadline': 'Varies by school'
            })
        
        recommendations.append({
            'priority': 'Medium',
            'action': 'Apply for state grants',
            'reason': 'Many states offer additional aid for residents',
            'deadline': 'Check your state deadline'
        })
        
        recommendations.append({
            'priority': 'Medium',
            'action': 'Search for private scholarships',
            'reason': 'Thousands of scholarships available based on various criteria',
            'deadline': 'Ongoing'
        })
        
        # Display recommendations
        for i, rec in enumerate(recommendations):
            with st.expander(f"{rec['priority']} Priority: {rec['action']}"):
                st.write(f"**Why:** {rec['reason']}")
                st.write(f"**Deadline:** {rec['deadline']}")
                
                if rec['priority'] == 'High':
                    st.warning("⚠️ Take action soon!")
                elif rec['priority'] == 'Medium':
                    st.info("ℹ️ Plan to complete this")
        
        # Scholarship opportunities
        st.subheader("🏆 Scholarship Opportunities")
        
        scholarship_data = {
            'Scholarship': ['Merit-based', 'Need-based', 'Major-specific', 'Demographic', 'Essay-based'],
            'Estimated Amount': ['$2,000-$10,000', '$1,000-$5,000', '$1,500-$8,000', '$1,000-$15,000', '$500-$5,000'],
            'Application Period': ['Fall', 'Year-round', 'Spring', 'Year-round', 'Year-round'],
            'Success Rate': ['15%', '25%', '20%', '30%', '10%']
        }
        
        df = pd.DataFrame(scholarship_data)
        st.dataframe(df, use_container_width=True)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'eligibility_check'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Recommendations", use_container_width=True):
                st.success("Recommendations saved!")
        
        with col3:
            if st.button("➡️ Create Application Plan", use_container_width=True):
                self.session_state.wizard_step = 'application_plan'
                st.rerun()
    
    def _render_application_plan_step(self) -> None:
        """Render personalized application plan"""
        st.header("📋 Your Application Plan")
        
        st.info("🎯 **Smart Plan:** This timeline is personalized based on your situation and deadlines.")
        
        # Timeline
        st.subheader("⏰ Application Timeline")
        
        timeline_data = {
            'Month': ['October', 'November', 'December', 'January', 'February', 'March', 'April', 'May'],
            'Action': [
                'Complete FAFSA',
                'Research scholarships',
                'Apply for state grants',
                'Submit institutional applications',
                'Follow up on applications',
                'Review award letters',
                'Compare aid packages',
                'Accept final aid package'
            ],
            'Status': ['Critical', 'Important', 'Important', 'Critical', 'Important', 'Critical', 'Critical', 'Critical'],
            'Deadline': ['Oct 1', 'Nov 30', 'Dec 31', 'Jan 15', 'Feb 28', 'Mar 15', 'Apr 30', 'May 1']
        }
        
        df = pd.DataFrame(timeline_data)
        
        # Color code by status
        def color_status(val) -> None:
            if val == 'Critical':
                return 'background-color: #ffcccc'
            elif val == 'Important':
                return 'background-color: #ffffcc'
            return ''
        
        st.dataframe(df.style.applymap(color_status, subset=['Status']), use_container_width=True)
        
        # Checklist
        st.subheader("✅ Action Checklist")
        
        checklist_items = [
            "Complete FAFSA application",
            "Gather required documents",
            "Research institutional scholarships",
            "Apply for state grants",
            "Search for private scholarships",
            "Submit all applications",
            "Follow up on applications",
            "Review and compare award letters",
            "Accept final aid package"
        ]
        
        for i, item in enumerate(checklist_items):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.checkbox(f"Task {i+1}", key=f"checklist_{i}")
            with col2:
                st.write(item)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                self.session_state.wizard_step = 'recommendations'
                st.rerun()
        
        with col2:
            if st.button("💾 Save Plan", use_container_width=True):
                st.success("Application plan saved!")
        
        with col3:
            if st.button("➡️ Document Checklist", use_container_width=True):
                self.session_state.wizard_step = 'document_checklist'
                st.rerun()
    
    def _render_document_checklist_step(self) -> None:
        """Render document checklist with upload capabilities"""
        st.header("📄 Document Checklist")
        
        st.info("📋 **Smart Checklist:** These documents are required for your financial aid applications.")
        
        # Required documents
        st.subheader("📋 Required Documents")
        
        documents = [
            {
                'document': 'Social Security Card',
                'required_for': 'FAFSA, All Applications',
                'status': 'Required',
                'upload': True
            },
            {
                'document': 'Driver\'s License or State ID',
                'required_for': 'FAFSA',
                'status': 'Required',
                'upload': True
            },
            {
                'document': 'W-2 Forms (2023)',
                'required_for': 'FAFSA',
                'status': 'Required',
                'upload': True
            },
            {
                'document': 'Federal Tax Returns (2023)',
                'required_for': 'FAFSA',
                'status': 'Required',
                'upload': True
            },
            {
                'document': 'Bank Statements',
                'required_for': 'Some Applications',
                'status': 'May be Required',
                'upload': True
            },
            {
                'document': 'Investment Records',
                'required_for': 'FAFSA',
                'status': 'Required',
                'upload': True
            },
            {
                'document': 'Alien Registration Card',
                'required_for': 'Non-citizens',
                'status': 'If Applicable',
                'upload': True
            }
        ]
        
        # Display documents with upload functionality
        for i, doc in enumerate(documents):
            with st.expander(f"📄 {doc['document']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Required for:** {doc['required_for']}")
                    st.write(f"**Status:** {doc['status']}")
                
                with col2:
                    if doc['upload']:
                        uploaded_file = st.file_uploader(
                            f"Upload {doc['document']}",
                            type=['pdf', 'jpg', 'png'],
                            key=f"upload_{i}"
                        )
                        if uploaded_file:
                            st.success(f"✅ {doc['document']} uploaded")
                
                with col3:
                    if st.button("✅ Mark Complete", key=f"complete_{i}"):
                        st.success(f"✅ {doc['document']} marked complete")
        
        # Progress tracking
        st.subheader("📊 Document Progress")
        
        total_docs = len(documents)
        completed_docs = 0  # In real app, track actual completion
        
        progress = completed_docs / total_docs
        st.progress(progress)
        st.write(f"**Progress:** {completed_docs}/{total_docs} documents ready")
        
        # Final summary
        st.subheader("🎉 Congratulations!")
        
        st.success("""
        **You've completed the Financial Aid Wizard!**
        
        Here's what you've accomplished:
        - ✅ Completed personal information profile
        - ✅ Analyzed financial situation
        - ✅ Checked eligibility for various aid types
        - ✅ Received personalized recommendations
        - ✅ Created application timeline
        - ✅ Prepared document checklist
        
        **Next Steps:**
        1. Complete your FAFSA application
        2. Gather required documents
        3. Apply for scholarships and grants
        4. Follow your personalized timeline
        5. Review and accept your aid package
        
        **Need Help?** Use the AI Assistant in the sidebar for any questions!
        """)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back to Plan", use_container_width=True):
                self.session_state.wizard_step = 'application_plan'
                st.rerun()
        
        with col2:
            if st.button("💾 Save All", use_container_width=True):
                st.success("All information saved!")
        
        with col3:
            if st.button("🏠 Return to Dashboard", use_container_width=True):
                self.session_state.wizard_step = 'welcome'
                st.rerun()

def main() -> None:
    """Main wizard interface"""
    wizard = FinancialAidWizard()
    wizard.render_wizard()

if __name__ == "__main__":
    main() 