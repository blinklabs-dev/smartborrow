"""
SmartBorrow Financial Planner
Interactive cost calculator, loan comparison, and repayment simulator
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
import numpy as np

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from smartborrow.rag.rag_service import RAGService
from smartborrow.agents.coordinator import CoordinatorAgent

class SmartFinancialPlanner:
    """Intelligent financial planning and cost analysis"""
    
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
    
    def render_planner(self) -> None:
        """Render the main financial planner interface"""
        st.set_page_config(
            page_title="Smart Financial Planner - SmartBorrow",
            page_icon="💰",
            layout="wide"
        )
        
        st.title("💰 Smart Financial Planner")
        st.markdown("*Plan your education costs, compare loan options, and simulate repayment scenarios*")
        
        # Tab navigation
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Cost Calculator", 
            "🏦 Loan Comparison", 
            "💳 Repayment Simulator", 
            "📈 ROI Calculator",
            "🚨 Emergency Planning"
        ])
        
        with tab1:
            self._render_cost_calculator()
        with tab2:
            self._render_loan_comparison()
        with tab3:
            self._render_repayment_simulator()
        with tab4:
            self._render_roi_calculator()
        with tab5:
            self._render_emergency_planning()
    
    def _render_cost_calculator(self) -> None:
        """Render interactive cost calculator"""
        st.header("📊 Interactive Cost Calculator")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🏫 School Information")
            
            # School selection
            school_type = st.selectbox(
                "Type of Institution",
                ["4-year Public", "4-year Private", "2-year Community College", "Trade/Technical", "Graduate School"],
                help="Different school types have different cost structures"
            )
            
            # Cost inputs
            col1a, col1b = st.columns(2)
            
            with col1a:
                tuition_fees = st.number_input(
                    "Tuition & Fees (per year)",
                    min_value=0,
                    value=25000,
                    step=1000,
                    help="Base tuition and mandatory fees"
                )
                
                room_board = st.number_input(
                    "Room & Board (per year)",
                    min_value=0,
                    value=12000,
                    step=1000,
                    help="Housing and meal plan costs"
                )
            
            with col1b:
                books_supplies = st.number_input(
                    "Books & Supplies (per year)",
                    min_value=0,
                    value=1200,
                    step=100,
                    help="Textbooks, supplies, and materials"
                )
                
                other_expenses = st.number_input(
                    "Other Expenses (per year)",
                    min_value=0,
                    value=3000,
                    step=500,
                    help="Transportation, personal expenses, etc."
                )
            
            # Program duration
            program_years = st.slider(
                "Program Duration (years)",
                min_value=1,
                max_value=8,
                value=4,
                help="How long will your program take?"
            )
            
            # Calculate total cost
            annual_cost = tuition_fees + room_board + books_supplies + other_expenses
            total_cost = annual_cost * program_years
            
            st.metric("Annual Cost of Attendance", f"${annual_cost:,}")
            st.metric("Total Program Cost", f"${total_cost:,}")
        
        with col2:
            st.subheader("💰 Cost Breakdown")
            
            # Pie chart of costs
            cost_data = {
                'Tuition & Fees': tuition_fees,
                'Room & Board': room_board,
                'Books & Supplies': books_supplies,
                'Other Expenses': other_expenses
            }
            
            fig = px.pie(
                values=list(cost_data.values()),
                names=list(cost_data.keys()),
                title="Annual Cost Breakdown"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Multi-year projection
        st.subheader("📈 Multi-Year Cost Projection")
        
        years = list(range(1, program_years + 1))
        costs = [annual_cost * year for year in years]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=costs,
            mode='lines+markers',
            name='Cumulative Cost',
            line=dict(color='blue', width=3)
        ))
        
        fig.update_layout(
            title="Cumulative Cost Over Time",
            xaxis_title="Year",
            yaxis_title="Cumulative Cost ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost comparison
        st.subheader("🏫 Cost Comparison by School Type")
        
        comparison_data = {
            'School Type': ['4-year Public', '4-year Private', '2-year Community College', 'Trade/Technical', 'Graduate School'],
            'Average Annual Cost': [25000, 50000, 8000, 15000, 40000],
            'Average Total Cost': [100000, 200000, 16000, 30000, 80000]
        }
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_loan_comparison(self) -> None:
        """Render loan comparison tool"""
        st.header("🏦 Loan Comparison Tool")
        
        st.info("💡 **Smart Comparison:** Compare different loan options to find the best fit for your situation.")
        
        # Loan options
        st.subheader("📋 Loan Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Federal Direct Loans**")
            
            # Direct Subsidized
            subsidized_amount = st.number_input(
                "Direct Subsidized Amount",
                min_value=0,
                value=3500,
                step=500,
                help="No interest while in school"
            )
            
            # Direct Unsubsidized
            unsubsidized_amount = st.number_input(
                "Direct Unsubsidized Amount",
                min_value=0,
                value=2000,
                step=500,
                help="Interest accrues while in school"
            )
            
            # Parent PLUS
            parent_plus_amount = st.number_input(
                "Parent PLUS Amount",
                min_value=0,
                value=0,
                step=1000,
                help="For parents of dependent students"
            )
        
        with col2:
            st.write("**Private Loan Options**")
            
            # Private loan 1
            private_1_amount = st.number_input(
                "Private Loan 1 Amount",
                min_value=0,
                value=0,
                step=1000
            )
            
            private_1_rate = st.slider(
                "Private Loan 1 Rate (%)",
                min_value=3.0,
                max_value=15.0,
                value=8.0,
                step=0.1
            )
            
            # Private loan 2
            private_2_amount = st.number_input(
                "Private Loan 2 Amount",
                min_value=0,
                value=0,
                step=1000
            )
            
            private_2_rate = st.slider(
                "Private Loan 2 Rate (%)",
                min_value=3.0,
                max_value=15.0,
                value=10.0,
                step=0.1
            )
        
        # Calculate loan comparisons
        st.subheader("📊 Loan Comparison Analysis")
        
        loans = []
        
        if subsidized_amount > 0:
            loans.append({
                'Type': 'Direct Subsidized',
                'Amount': subsidized_amount,
                'Rate': 5.50,  # 2024-25 rate
                'Interest_While_In_School': 0,
                'Fees': 0,
                'Repayment_Options': 'Income-driven available'
            })
        
        if unsubsidized_amount > 0:
            loans.append({
                'Type': 'Direct Unsubsidized',
                'Amount': unsubsidized_amount,
                'Rate': 5.50,  # 2024-25 rate
                'Interest_While_In_School': unsubsidized_amount * 0.055 * 4,  # 4 years
                'Fees': 0,
                'Repayment_Options': 'Income-driven available'
            })
        
        if parent_plus_amount > 0:
            loans.append({
                'Type': 'Parent PLUS',
                'Amount': parent_plus_amount,
                'Rate': 8.05,  # 2024-25 rate
                'Interest_While_In_School': parent_plus_amount * 0.0805 * 4,
                'Fees': parent_plus_amount * 0.0429,  # 4.29% fee
                'Repayment_Options': 'Standard only'
            })
        
        if private_1_amount > 0:
            loans.append({
                'Type': 'Private Loan 1',
                'Amount': private_1_amount,
                'Rate': private_1_rate,
                'Interest_While_In_School': private_1_amount * (private_1_rate/100) * 4,
                'Fees': 0,
                'Repayment_Options': 'Limited options'
            })
        
        if private_2_amount > 0:
            loans.append({
                'Type': 'Private Loan 2',
                'Amount': private_2_amount,
                'Rate': private_2_rate,
                'Interest_While_In_School': private_2_amount * (private_2_rate/100) * 4,
                'Fees': 0,
                'Repayment_Options': 'Limited options'
            })
        
        if loans:
            df = pd.DataFrame(loans)
            
            # Calculate total costs
            df['Total_Interest'] = df['Interest_While_In_School'] + (df['Amount'] * (df['Rate']/100) * 10)  # 10-year repayment
            df['Total_Cost'] = df['Amount'] + df['Total_Interest'] + df['Fees']
            
            st.dataframe(df, use_container_width=True)
            
            # Visual comparison
            st.subheader("📈 Cost Comparison Chart")
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['Type'],
                y=df['Amount'],
                name='Principal',
                marker_color='blue'
            ))
            
            fig.add_trace(go.Bar(
                x=df['Type'],
                y=df['Total_Interest'],
                name='Interest',
                marker_color='red'
            ))
            
            fig.add_trace(go.Bar(
                x=df['Type'],
                y=df['Fees'],
                name='Fees',
                marker_color='orange'
            ))
            
            fig.update_layout(
                title="Loan Cost Breakdown",
                barmode='stack',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 Smart Recommendations")
            
            total_federal = sum([loan['Amount'] for loan in loans if 'Direct' in loan['Type'] or 'Parent PLUS' in loan['Type']])
            total_private = sum([loan['Amount'] for loan in loans if 'Private' in loan['Type']])
            
            if total_federal > 0:
                st.success(f"✅ Federal loans: ${total_federal:,} - Better terms and protections")
            
            if total_private > 0:
                st.warning(f"⚠️ Private loans: ${total_private:,} - Higher rates, fewer protections")
            
            if total_private > total_federal:
                st.error("🚨 Consider reducing private loans - federal loans offer better terms")
    
    def _render_repayment_simulator(self) -> None:
        """Render repayment simulator with different plans"""
        st.header("💳 Repayment Simulator")
        
        st.info("🎯 **Smart Simulation:** See how different repayment plans affect your monthly payments and total cost.")
        
        # Loan information
        st.subheader("📋 Loan Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_loan_amount = st.number_input(
                "Total Loan Amount",
                min_value=1000,
                value=30000,
                step=1000
            )
            
            interest_rate = st.slider(
                "Interest Rate (%)",
                min_value=1.0,
                max_value=15.0,
                value=5.5,
                step=0.1
            )
        
        with col2:
            loan_term = st.selectbox(
                "Repayment Term",
                ["10 years", "15 years", "20 years", "25 years", "Income-driven"],
                help="Standard term or income-driven repayment"
            )
            
            starting_salary = st.number_input(
                "Starting Salary",
                min_value=20000,
                value=50000,
                step=5000,
                help="For income-driven repayment calculations"
            )
        
        # Calculate different repayment scenarios
        st.subheader("📊 Repayment Scenarios")
        
        scenarios = []
        
        # Standard repayment
        if loan_term != "Income-driven":
            years = int(loan_term.split()[0])
            monthly_rate = interest_rate / 100 / 12
            num_payments = years * 12
            
            if monthly_rate > 0:
                monthly_payment = total_loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            else:
                monthly_payment = total_loan_amount / num_payments
            
            total_paid = monthly_payment * num_payments
            total_interest = total_paid - total_loan_amount
            
            scenarios.append({
                'Plan': 'Standard Repayment',
                'Monthly Payment': monthly_payment,
                'Total Paid': total_paid,
                'Total Interest': total_interest,
                'Years': years
            })
        
        # Income-driven repayment options
        if loan_term == "Income-driven" or st.checkbox("Show Income-Driven Options"):
            # REPAYE
            repaye_payment = max(0.10 * (starting_salary - 20000) / 12, 0)
            repaye_years = 20
            repaye_total = repaye_payment * 12 * repaye_years
            repaye_interest = max(0, repaye_total - total_loan_amount)
            
            scenarios.append({
                'Plan': 'REPAYE',
                'Monthly Payment': repaye_payment,
                'Total Paid': repaye_total,
                'Total Interest': repaye_interest,
                'Years': repaye_years
            })
            
            # IBR
            ibr_payment = max(0.15 * (starting_salary - 20000) / 12, 0)
            ibr_years = 25
            ibr_total = ibr_payment * 12 * ibr_years
            ibr_interest = max(0, ibr_total - total_loan_amount)
            
            scenarios.append({
                'Plan': 'Income-Based Repayment',
                'Monthly Payment': ibr_payment,
                'Total Paid': ibr_total,
                'Total Interest': ibr_interest,
                'Years': ibr_years
            })
            
            # PAYE
            paye_payment = max(0.10 * (starting_salary - 20000) / 12, 0)
            paye_years = 20
            paye_total = paye_payment * 12 * paye_years
            paye_interest = max(0, paye_total - total_loan_amount)
            
            scenarios.append({
                'Plan': 'PAYE',
                'Monthly Payment': paye_payment,
                'Total Paid': paye_total,
                'Total Interest': paye_interest,
                'Years': paye_years
            })
        
        # Display scenarios
        if scenarios:
            df = pd.DataFrame(scenarios)
            df['Monthly Payment'] = df['Monthly Payment'].round(2)
            df['Total Paid'] = df['Total Paid'].round(2)
            df['Total Interest'] = df['Total Interest'].round(2)
            
            st.dataframe(df, use_container_width=True)
            
            # Visual comparison
            st.subheader("📈 Payment Comparison")
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['Plan'],
                y=df['Monthly Payment'],
                name='Monthly Payment',
                marker_color='blue'
            ))
            
            fig.update_layout(
                title="Monthly Payment by Repayment Plan",
                xaxis_title="Repayment Plan",
                yaxis_title="Monthly Payment ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Total cost comparison
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=df['Plan'],
                y=df['Total Paid'],
                name='Total Paid',
                marker_color='green'
            ))
            
            fig2.update_layout(
                title="Total Cost by Repayment Plan",
                xaxis_title="Repayment Plan",
                yaxis_title="Total Paid ($)",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 Smart Recommendations")
            
            min_monthly = df['Monthly Payment'].min()
            min_total = df['Total Paid'].min()
            
            best_monthly_plan = df.loc[df['Monthly Payment'] == min_monthly, 'Plan'].iloc[0]
            best_total_plan = df.loc[df['Total Paid'] == min_total, 'Plan'].iloc[0]
            
            st.success(f"💰 **Lowest monthly payment:** {best_monthly_plan} (${min_monthly:.2f}/month)")
            st.success(f"💵 **Lowest total cost:** {best_total_plan} (${min_total:.2f} total)")
            
            if 'Income' in best_monthly_plan:
                st.info("ℹ️ Income-driven plans may have tax implications on forgiven amounts")
    
    def _render_roi_calculator(self) -> None:
        """Render ROI calculator for education investment"""
        st.header("📈 Education ROI Calculator")
        
        st.info("🎯 **Smart ROI:** Calculate the return on investment for your education and career choices.")
        
        # Education costs
        st.subheader("💰 Education Investment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_education_cost = st.number_input(
                "Total Education Cost",
                min_value=0,
                value=100000,
                step=5000,
                help="Including loans, out-of-pocket costs, opportunity cost"
            )
            
            years_to_complete = st.slider(
                "Years to Complete",
                min_value=1,
                max_value=8,
                value=4
            )
        
        with col2:
            starting_salary = st.number_input(
                "Starting Salary",
                min_value=20000,
                value=50000,
                step=5000
            )
            
            salary_growth_rate = st.slider(
                "Annual Salary Growth Rate (%)",
                min_value=0,
                max_value=20,
                value=3,
                step=1
            )
        
        # Career information
        st.subheader("💼 Career Projections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            years_working = st.slider(
                "Years Working",
                min_value=10,
                max_value=50,
                value=30
            )
            
            alternative_salary = st.number_input(
                "Salary Without Degree",
                min_value=20000,
                value=30000,
                step=5000,
                help="What you would earn without this education"
            )
        
        with col2:
            alternative_growth = st.slider(
                "Alternative Salary Growth Rate (%)",
                min_value=0,
                max_value=15,
                value=1,
                step=1
            )
            
            tax_rate = st.slider(
                "Effective Tax Rate (%)",
                min_value=0,
                max_value=50,
                value=25,
                step=5
            )
        
        # Calculate ROI
        st.subheader("📊 ROI Analysis")
        
        # Calculate earnings over time
        years = list(range(years_working))
        
        with_degree_earnings = []
        without_degree_earnings = []
        
        for year in years:
            with_degree = starting_salary * (1 + salary_growth_rate/100) ** year
            without_degree = alternative_salary * (1 + alternative_growth/100) ** year
            
            # Apply tax rate
            with_degree_after_tax = with_degree * (1 - tax_rate/100)
            without_degree_after_tax = without_degree * (1 - tax_rate/100)
            
            with_degree_earnings.append(with_degree_after_tax)
            without_degree_earnings.append(without_degree_after_tax)
        
        # Calculate cumulative earnings
        cumulative_with_degree = [sum(with_degree_earnings[:i+1]) for i in range(len(with_degree_earnings))]
        cumulative_without_degree = [sum(without_degree_earnings[:i+1]) for i in range(len(without_degree_earnings))]
        
        # Calculate ROI metrics
        total_earnings_with_degree = cumulative_with_degree[-1]
        total_earnings_without_degree = cumulative_without_degree[-1]
        
        additional_earnings = total_earnings_with_degree - total_earnings_without_degree
        roi_percentage = ((additional_earnings - total_education_cost) / total_education_cost) * 100 if total_education_cost > 0 else 0
        payback_period = total_education_cost / (starting_salary * (1 - tax_rate/100) - alternative_salary * (1 - tax_rate/100)) if (starting_salary * (1 - tax_rate/100) - alternative_salary * (1 - tax_rate/100)) > 0 else float('inf')
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Additional Lifetime Earnings", f"${additional_earnings:,.0f}")
        
        with col2:
            st.metric("ROI Percentage", f"{roi_percentage:.1f}%")
        
        with col3:
            if payback_period != float('inf'):
                st.metric("Payback Period", f"{payback_period:.1f} years")
            else:
                st.metric("Payback Period", "Never")
        
        # Visual comparison
        st.subheader("📈 Earnings Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative_with_degree,
            mode='lines',
            name='With Degree',
            line=dict(color='blue', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative_without_degree,
            mode='lines',
            name='Without Degree',
            line=dict(color='red', width=3)
        ))
        
        fig.update_layout(
            title="Cumulative Earnings Over Time",
            xaxis_title="Years Working",
            yaxis_title="Cumulative Earnings ($)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.subheader("💡 Smart Insights")
        
        if roi_percentage > 0:
            st.success(f"✅ **Positive ROI:** Your education investment will pay off with a {roi_percentage:.1f}% return")
        else:
            st.warning(f"⚠️ **Negative ROI:** Consider if this education investment makes financial sense")
        
        if payback_period < 10:
            st.success(f"✅ **Quick payback:** You'll recoup your investment in {payback_period:.1f} years")
        elif payback_period < 20:
            st.info(f"ℹ️ **Moderate payback:** Investment will be recouped in {payback_period:.1f} years")
        else:
            st.warning(f"⚠️ **Long payback:** Consider the long-term commitment")
    
    def _render_emergency_planning(self) -> None:
        """Render emergency financial planning tools"""
        st.header("🚨 Emergency Financial Planning")
        
        st.info("🛡️ **Smart Protection:** Plan for financial emergencies and unexpected expenses during your education.")
        
        # Emergency fund calculator
        st.subheader("💰 Emergency Fund Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            monthly_expenses = st.number_input(
                "Monthly Living Expenses",
                min_value=500,
                value=2000,
                step=100
            )
            
            insurance_deductible = st.number_input(
                "Insurance Deductible",
                min_value=0,
                value=1000,
                step=100
            )
        
        with col2:
            job_search_months = st.slider(
                "Months to Find New Job",
                min_value=1,
                max_value=12,
                value=3
            )
            
            additional_emergency = st.number_input(
                "Additional Emergency Buffer",
                min_value=0,
                value=2000,
                step=500
            )
        
        # Calculate emergency fund needs
        basic_emergency = monthly_expenses * 3  # 3 months of expenses
        comprehensive_emergency = (monthly_expenses * job_search_months) + insurance_deductible + additional_emergency
        
        st.metric("Basic Emergency Fund (3 months)", f"${basic_emergency:,}")
        st.metric("Comprehensive Emergency Fund", f"${comprehensive_emergency:,}")
        
        # Emergency fund progress
        current_emergency_savings = st.number_input(
            "Current Emergency Savings",
            min_value=0,
            value=5000,
            step=500
        )
        
        progress = min(100, (current_emergency_savings / comprehensive_emergency) * 100)
        st.progress(progress / 100)
        st.write(f"**Emergency Fund Progress:** {progress:.1f}%")
        
        if progress < 100:
            needed = comprehensive_emergency - current_emergency_savings
            st.warning(f"⚠️ **Still need:** ${needed:,} to reach your emergency fund goal")
        else:
            st.success("✅ **Emergency fund complete!** You're well-protected")
        
        # Emergency planning strategies
        st.subheader("🛡️ Emergency Planning Strategies")
        
        strategies = [
            {
                'Strategy': 'Build Emergency Fund',
                'Priority': 'High',
                'Action': 'Save 3-6 months of expenses',
                'Timeline': 'Ongoing'
            },
            {
                'Strategy': 'Reduce Expenses',
                'Priority': 'High',
                'Action': 'Create budget and cut non-essentials',
                'Timeline': 'Immediate'
            },
            {
                'Strategy': 'Income Diversification',
                'Priority': 'Medium',
                'Action': 'Part-time work, freelancing, side hustles',
                'Timeline': '1-3 months'
            },
            {
                'Strategy': 'Insurance Coverage',
                'Priority': 'Medium',
                'Action': 'Health, auto, renter\'s insurance',
                'Timeline': 'Immediate'
            },
            {
                'Strategy': 'Credit Backup',
                'Priority': 'Low',
                'Action': 'Emergency credit card (use sparingly)',
                'Timeline': 'As needed'
            }
        ]
        
        df = pd.DataFrame(strategies)
        st.dataframe(df, use_container_width=True)
        
        # Emergency scenarios
        st.subheader("🎯 Emergency Scenario Planning")
        
        scenarios = [
            "Medical emergency",
            "Car breakdown",
            "Job loss",
            "Family emergency",
            "Natural disaster",
            "Technology failure (laptop, phone)"
        ]
        
        for scenario in scenarios:
            with st.expander(f"🚨 {scenario}"):
                st.write(f"**Potential cost:** $1,000-$10,000")
                st.write(f"**Emergency fund needed:** ${comprehensive_emergency:,}")
                st.write(f"**Coverage:** {'✅ Covered' if current_emergency_savings >= comprehensive_emergency else '❌ Not covered'}")
                
                if current_emergency_savings < comprehensive_emergency:
                    st.warning("Consider building your emergency fund to handle this scenario")

def main() -> None:
    """Main financial planner interface"""
    planner = SmartFinancialPlanner()
    planner.render_planner()

if __name__ == "__main__":
    main() 