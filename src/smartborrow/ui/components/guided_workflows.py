#!/usr/bin/env python3
"""
Guided Workflow Components for SmartBorrow
People-first design for complex financial aid processes
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class GuidedWorkflow:
    """Base class for guided workflows"""
    
    def __init__(self, workflow_name: str, steps: List[Dict[str, Any]]):
        self.workflow_name = workflow_name
        self.steps = steps
        self.current_step = 0
        
    def render_progress(self) -> None:
        """Render progress indicator"""
        st.markdown(f"## 📋 {self.workflow_name}")
        
        # Progress bar
        progress = (self.current_step + 1) / len(self.steps)
        st.progress(progress)
        
        # Step indicators
        cols = st.columns(len(self.steps))
        for i, step in enumerate(self.steps):
            with cols[i]:
                if i < self.current_step:
                    st.success(f"✅ {step['title']}")
                elif i == self.current_step:
                    st.info(f"🔄 {step['title']}")
                else:
                    st.write(f"⏳ {step['title']}")

class FAFSAGuidedWorkflow(GuidedWorkflow):
    """Guided FAFSA completion workflow"""
    
    def __init__(self):
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
            },
            {
                "title": "Complete Application",
                "description": "Fill out all required sections",
                "tasks": [
                    "Demographics section",
                    "School selection",
                    "Dependency status",
                    "Parent information",
                    "Financial information",
                    "Review and submit"
                ]
            },
            {
                "title": "Submit & Follow Up",
                "description": "Submit your application and track progress",
                "tasks": [
                    "Review all information",
                    "Sign with FSA ID",
                    "Submit application",
                    "Save confirmation number",
                    "Check status in 3-5 days",
                    "Review Student Aid Report (SAR)"
                ]
            }
        ]
        super().__init__("FAFSA Completion Guide", steps)
    
    def render_current_step(self) -> None:
        """Render the current step with detailed guidance"""
        if self.current_step >= len(self.steps):
            self.render_completion()
            return
        
        step = self.steps[self.current_step]
        
        st.markdown(f"### 📝 Step {self.current_step + 1}: {step['title']}")
        st.markdown(f"**{step['description']}**")
        
        # Task checklist
        st.markdown("#### ✅ Your Checklist:")
        for i, task in enumerate(step['tasks']):
            task_key = f"task_{self.current_step}_{i}"
            if st.checkbox(task, key=task_key):
                st.success(f"✅ {task}")
            else:
                st.write(f"⏳ {task}")
        
        # Helpful tips
        self.render_step_tips(step)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if self.current_step > 0:
                if st.button("⬅️ Previous Step", key=f"prev_{self.current_step}"):
                    self.current_step -= 1
                    st.rerun()
        
        with col2:
            if st.button("💾 Save Progress", key=f"save_{self.current_step}"):
                self.save_progress()
                st.success("Progress saved!")
        
        with col3:
            if st.button("➡️ Next Step", key=f"next_{self.current_step}"):
                self.current_step += 1
                st.rerun()
    
    def render_step_tips(self, step: Dict[str, Any]) -> None:
        """Render helpful tips for the current step"""
        st.markdown("#### 💡 Helpful Tips:")
        
        if step['title'] == "Prepare Documents":
            st.info("""
            - **Don't worry if you don't have everything** - You can start with what you have and update later
            - **Use estimates if needed** - You can update with actual numbers when you file taxes
            - **Ask for help** - Many schools and libraries offer free FAFSA help
            """)
        
        elif step['title'] == "Create FSA ID":
            st.info("""
            - **Write down your FSA ID** - You'll need it every year
            - **Use a strong password** - This protects your financial information
            - **Keep it secure** - Don't share your FSA ID with anyone
            """)
        
        elif step['title'] == "Start FAFSA":
            st.info("""
            - **Take your time** - You can save and return later
            - **Be accurate** - Double-check all information
            - **Don't leave anything blank** - Use $0 if you have no income
            """)
        
        elif step['title'] == "Complete Application":
            st.info("""
            - **Use the IRS Data Retrieval Tool** - It's faster and more accurate
            - **Include all schools** - You can add more later
            - **Answer dependency questions carefully** - This affects your aid
            """)
        
        elif step['title'] == "Submit & Follow Up":
            st.info("""
            - **Save your confirmation number** - You'll need it for reference
            - **Check your email** - You'll receive a confirmation
            - **Review your SAR** - Make sure all information is correct
            """)
    
    def render_completion(self) -> None:
        """Render completion message"""
        st.success("🎉 Congratulations! You've completed the FAFSA guide!")
        
        st.markdown("""
        ### 📋 What's Next?
        
        **Immediate Actions:**
        - ✅ Save your confirmation number
        - ✅ Check your email for confirmation
        - ✅ Review your Student Aid Report (SAR) when it arrives
        
        **In the Next Few Weeks:**
        - 📧 Check your email for updates
        - 🏫 Contact your schools about additional requirements
        - 💰 Research school-specific scholarships
        - 📅 Mark important deadlines on your calendar
        
        **Remember:**
        - You can update your FAFSA if information changes
        - Many schools have additional forms or deadlines
        - Don't hesitate to ask for help if you need it!
        """)
        
        if st.button("🏠 Return to Dashboard"):
            st.session_state.user_journey['stage'] = 'dashboard'
            st.rerun()
    
    def save_progress(self) -> None:
        """Save user progress"""
        if 'fafsa_progress' not in st.session_state:
            st.session_state.fafsa_progress = {}
        
        st.session_state.fafsa_progress['current_step'] = self.current_step
        st.session_state.fafsa_progress['last_updated'] = datetime.now().isoformat()

class ScholarshipSearchWorkflow(GuidedWorkflow):
    """Guided scholarship search workflow"""
    
    def __init__(self):
        steps = [
            {
                "title": "Assess Your Profile",
                "description": "Identify your unique characteristics and achievements",
                "categories": [
                    "Academic achievements (GPA, test scores)",
                    "Extracurricular activities",
                    "Community service",
                    "Leadership experience",
                    "Special talents or skills",
                    "Demographic factors",
                    "Field of study",
                    "Geographic location"
                ]
            },
            {
                "title": "Research Opportunities",
                "description": "Find scholarships that match your profile",
                "categories": [
                    "School-specific scholarships",
                    "Local community scholarships",
                    "Professional associations",
                    "Employer scholarships",
                    "Government programs",
                    "Private foundations",
                    "Online scholarship databases"
                ]
            },
            {
                "title": "Organize Applications",
                "description": "Create a system to track your applications",
                "categories": [
                    "Create a spreadsheet or folder",
                    "Note deadlines and requirements",
                    "Gather required documents",
                    "Prepare personal statements",
                    "Request letters of recommendation",
                    "Set up calendar reminders"
                ]
            },
            {
                "title": "Submit Applications",
                "description": "Complete and submit your scholarship applications",
                "categories": [
                    "Follow all instructions carefully",
                    "Proofread all materials",
                    "Submit before deadlines",
                    "Keep copies of everything",
                    "Follow up if needed",
                    "Track application status"
                ]
            }
        ]
        super().__init__("Scholarship Search Guide", steps)
    
    def render_current_step(self) -> None:
        """Render the current step with detailed guidance"""
        if self.current_step >= len(self.steps):
            self.render_completion()
            return
        
        step = self.steps[self.current_step]
        
        st.markdown(f"### 🎯 Step {self.current_step + 1}: {step['title']}")
        st.markdown(f"**{step['description']}**")
        
        # Interactive profile builder
        if step['title'] == "Assess Your Profile":
            self.render_profile_builder()
        elif step['title'] == "Research Opportunities":
            self.render_scholarship_research()
        elif step['title'] == "Organize Applications":
            self.render_organization_tools()
        elif step['title'] == "Submit Applications":
            self.render_application_tracker()
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if self.current_step > 0:
                if st.button("⬅️ Previous Step", key=f"prev_{self.current_step}"):
                    self.current_step -= 1
                    st.rerun()
        
        with col2:
            if st.button("💾 Save Progress", key=f"save_{self.current_step}"):
                self.save_progress()
                st.success("Progress saved!")
        
        with col3:
            if st.button("➡️ Next Step", key=f"next_{self.current_step}"):
                self.current_step += 1
                st.rerun()
    
    def render_profile_builder(self) -> None:
        """Render interactive profile builder"""
        st.markdown("#### 🎯 Build Your Scholarship Profile")
        
        # Academic Information
        st.markdown("**📚 Academic Information**")
        gpa = st.slider("GPA", 0.0, 4.0, 3.5, 0.1)
        sat_score = st.number_input("SAT Score (if applicable)", min_value=400, max_value=1600, value=1200)
        act_score = st.number_input("ACT Score (if applicable)", min_value=1, max_value=36, value=20)
        
        # Activities and Achievements
        st.markdown("**🏆 Activities and Achievements**")
        activities = st.multiselect(
            "Select activities that apply to you:",
            [
                "Student government", "Sports teams", "Academic clubs", "Music/Arts",
                "Community service", "Part-time job", "Internships", "Research projects",
                "Leadership roles", "Awards and honors", "Volunteer work", "Hobbies"
            ]
        )
        
        # Demographics and Background
        st.markdown("**👥 Demographics and Background**")
        demographics = st.multiselect(
            "Select characteristics that apply to you:",
            [
                "First-generation college student", "Low-income family", "Rural area",
                "Urban area", "Military family", "Disability", "LGBTQ+", "International student",
                "Transfer student", "Adult learner", "Single parent", "Foster youth"
            ]
        )
        
        # Field of Study
        st.markdown("**🎓 Field of Study**")
        major = st.text_input("Intended Major", placeholder="e.g., Computer Science")
        career_goals = st.text_area("Career Goals", placeholder="Describe your career aspirations...")
        
        # Save profile
        if st.button("💾 Save My Profile"):
            profile = {
                'gpa': gpa,
                'sat_score': sat_score,
                'act_score': act_score,
                'activities': activities,
                'demographics': demographics,
                'major': major,
                'career_goals': career_goals
            }
            st.session_state.scholarship_profile = profile
            st.success("Profile saved! This will help us find relevant scholarships.")
    
    def render_scholarship_research(self) -> None:
        """Render scholarship research tools"""
        st.markdown("#### 🔍 Find Scholarships That Match You")
        
        # Search by category
        search_category = st.selectbox(
            "Search by category:",
            ["Academic Merit", "Financial Need", "Field of Study", "Demographics", "Location", "Activities"]
        )
        
        if search_category == "Academic Merit":
            st.info("**Academic Merit Scholarships**")
            st.markdown("""
            - **National Merit Scholarship** - Based on PSAT scores
            - **Presidential Scholars** - Top academic achievers
            - **School-specific merit awards** - Check with your target schools
            - **Phi Beta Kappa** - Academic excellence in liberal arts
            """)
        
        elif search_category == "Financial Need":
            st.info("**Need-Based Scholarships**")
            st.markdown("""
            - **Pell Grant** - Federal need-based grant
            - **State need-based programs** - Check your state's website
            - **School-specific need grants** - Contact financial aid offices
            - **Private need-based scholarships** - Search online databases
            """)
        
        elif search_category == "Field of Study":
            st.info("**Field-Specific Scholarships**")
            st.markdown("""
            - **STEM scholarships** - Many organizations support STEM students
            - **Arts scholarships** - Creative fields have unique opportunities
            - **Business scholarships** - Professional associations offer awards
            - **Education scholarships** - Future teachers have many options
            """)
        
        # Search results
        st.markdown("#### 📋 Recommended Scholarships")
        
        # Mock search results
        scholarships = [
            {
                "name": "Academic Excellence Award",
                "amount": "$5,000",
                "deadline": "March 15",
                "requirements": "3.5+ GPA, leadership experience"
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
        
        for scholarship in scholarships:
            with st.expander(f"💰 {scholarship['name']} - {scholarship['amount']}"):
                st.write(f"**Deadline:** {scholarship['deadline']}")
                st.write(f"**Requirements:** {scholarship['requirements']}")
                if st.button(f"📝 Apply for {scholarship['name']}", key=f"apply_{scholarship['name']}"):
                    st.success("Application started! We'll help you track it.")
    
    def render_organization_tools(self) -> None:
        """Render organization and tracking tools"""
        st.markdown("#### 📊 Organize Your Scholarship Applications")
        
        # Application tracker
        st.markdown("**📋 Application Tracker**")
        
        # Add new application
        with st.expander("➕ Add New Application"):
            app_name = st.text_input("Scholarship Name")
            app_deadline = st.date_input("Deadline")
            app_amount = st.number_input("Amount", min_value=0)
            app_status = st.selectbox("Status", ["Planning", "In Progress", "Submitted", "Awarded", "Rejected"])
            
            if st.button("Add Application"):
                if 'applications' not in st.session_state:
                    st.session_state.applications = []
                
                st.session_state.applications.append({
                    'name': app_name,
                    'deadline': app_deadline,
                    'amount': app_amount,
                    'status': app_status
                })
                st.success("Application added to tracker!")
        
        # View applications
        if 'applications' in st.session_state and st.session_state.applications:
            st.markdown("**📊 Your Applications**")
            
            for i, app in enumerate(st.session_state.applications):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**{app['name']}**")
                with col2:
                    st.write(f"${app['amount']:,}")
                with col3:
                    st.write(f"Due: {app['deadline']}")
                with col4:
                    st.write(f"Status: {app['status']}")
    
    def render_application_tracker(self) -> None:
        """Render application submission tracker"""
        st.markdown("#### ✅ Application Submission Checklist")
        
        checklist_items = [
            "Application form completed",
            "Personal statement written",
            "Letters of recommendation requested",
            "Transcripts ordered",
            "Financial documents gathered",
            "Application fee paid (if required)",
            "Application submitted",
            "Confirmation received",
            "Follow-up email sent",
            "Status checked after 2 weeks"
        ]
        
        for i, item in enumerate(checklist_items):
            if st.checkbox(item, key=f"checklist_{i}"):
                st.success(f"✅ {item}")
            else:
                st.write(f"⏳ {item}")
        
        st.markdown("#### 💡 Submission Tips")
        st.info("""
        - **Submit early** - Many scholarships have rolling deadlines
        - **Proofread everything** - Typos can hurt your chances
        - **Follow instructions exactly** - Don't disqualify yourself
        - **Keep copies** - Save everything for your records
        - **Follow up** - Check on your application status
        """)
    
    def render_completion(self) -> None:
        """Render completion message"""
        st.success("🎉 Great job! You're well on your way to finding scholarships!")
        
        st.markdown("""
        ### 📋 What's Next?
        
        **Keep Going:**
        - 🔍 Continue searching for new opportunities
        - 📝 Work on your applications
        - 📅 Set reminders for deadlines
        - 📞 Follow up on submitted applications
        
        **Stay Organized:**
        - 📊 Update your application tracker
        - 📧 Check your email regularly
        - 💰 Track any awards received
        - 📚 Keep improving your profile
        
        **Remember:**
        - Every scholarship is worth applying for
        - Don't get discouraged by rejections
        - Keep applying throughout your college career
        - Ask for help when you need it!
        """)
        
        if st.button("🏠 Return to Dashboard"):
            st.session_state.user_journey['stage'] = 'dashboard'
            st.rerun()
    
    def save_progress(self) -> None:
        """Save user progress"""
        if 'scholarship_progress' not in st.session_state:
            st.session_state.scholarship_progress = {}
        
        st.session_state.scholarship_progress['current_step'] = self.current_step
        st.session_state.scholarship_progress['last_updated'] = datetime.now().isoformat()

def create_workflow(workflow_type: str) -> GuidedWorkflow:
    """Factory function to create guided workflows"""
    if workflow_type == "fafsa":
        return FAFSAGuidedWorkflow()
    elif workflow_type == "scholarship":
        return ScholarshipSearchWorkflow()
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}") 