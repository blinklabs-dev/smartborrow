#!/usr/bin/env python3
"""
Emotional Support and Accessibility Components for SmartBorrow
Addressing anxiety, stress, and accessibility needs in financial aid
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

class EmotionalSupportSystem:
    """System for providing emotional support and reducing anxiety"""
    
    def __init__(self):
        self.support_messages = {
            'welcome': [
                "You're not alone in this journey. Many students feel overwhelmed by financial aid, and that's completely normal.",
                "We're here to break down the complex process into manageable steps. You've got this!",
                "Remember: every student who goes to college faces these same questions. You're taking the right first step."
            ],
            'stress': [
                "It's okay to feel stressed about this. Financial aid is complex, but we'll work through it together.",
                "Take a deep breath. We'll tackle this one step at a time.",
                "You don't have to figure everything out today. Let's start with what you know and build from there."
            ],
            'confusion': [
                "Confusion is normal! Financial aid has a lot of moving parts. We'll clarify things as we go.",
                "Don't worry about understanding everything at once. We'll explain each piece when you need it.",
                "If something doesn't make sense, that's our cue to explain it better. Ask questions anytime!"
            ],
            'success': [
                "Great job! You're making real progress on your financial aid journey.",
                "Celebrate this win! Every step forward is important.",
                "You're building important skills for your future. This experience will help you in many ways."
            ],
            'encouragement': [
                "You're doing better than you think. Many students never even start this process.",
                "Your future self will thank you for taking these steps now.",
                "Every question you ask brings you closer to your goals."
            ]
        }
        
        self.accessibility_features = {
            'high_contrast': False,
            'large_text': False,
            'screen_reader_friendly': True,
            'keyboard_navigation': True,
            'reduced_motion': False
        }
    
    def render_support_message(self, message_type: str) -> None:
        """Render an empathetic support message"""
        messages = self.support_messages.get(message_type, self.support_messages['encouragement'])
        message = random.choice(messages)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <p style="margin: 0; font-style: italic; color: #1e40af;">
                💙 {message}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_anxiety_reduction(self) -> None:
        """Render anxiety reduction techniques"""
        st.markdown("## 😌 Feeling Overwhelmed?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🧘‍♀️ Quick Stress Relief
            
            **Take a moment to:**
            - Breathe deeply (inhale for 4, hold for 4, exhale for 6)
            - Remember: You don't have to do everything at once
            - Focus on just the next small step
            
            **You're not alone:**
            - Millions of students go through this every year
            - There are people ready to help you
            - Many students feel exactly like you do
            """)
        
        with col2:
            st.markdown("""
            ### 💡 Remember
            
            **It's okay to:**
            - Ask for help when you need it
            - Take breaks when you're feeling stressed
            - Not know all the answers right away
            - Make mistakes and learn from them
            
            **You're doing great by:**
            - Starting this process early
            - Seeking out information and help
            - Taking control of your education
            """)
        
        if st.button("😌 I'm feeling better now"):
            st.success("Great! Let's continue with your financial aid journey.")
    
    def render_confidence_builder(self, user_profile: Dict[str, Any]) -> None:
        """Build user confidence based on their profile"""
        st.markdown("## 💪 You've Got This!")
        
        # Personalized confidence messages
        if user_profile.get('academic_level') == "High school student":
            st.info("""
            **You're ahead of the game!** Many students don't start thinking about financial aid until senior year. 
            You're being proactive, which shows maturity and responsibility.
            """)
        
        elif user_profile.get('academic_level') == "Current college student":
            st.info("""
            **You're building experience!** You've already navigated some of the financial aid process. 
            Each year gets easier as you learn the system.
            """)
        
        # Highlight strengths
        strengths = []
        if user_profile.get('family_income') in ["Under $30,000", "$30,000 - $60,000"]:
            strengths.append("You may qualify for significant need-based aid")
        if "Maximize grants and scholarships" in user_profile.get('financial_goals', []):
            strengths.append("You're focused on the right priorities")
        if "Get help with applications" in user_profile.get('financial_goals', []):
            strengths.append("You're smart to seek help when needed")
        
        if strengths:
            st.markdown("### 🎯 Your Strengths:")
            for strength in strengths:
                st.markdown(f"- ✅ {strength}")
    
    def render_accessibility_panel(self) -> None:
        """Render accessibility options panel"""
        with st.expander("♿ Accessibility Options"):
            st.markdown("### 🎨 Visual Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                high_contrast = st.checkbox("High Contrast Mode", value=self.accessibility_features['high_contrast'])
                large_text = st.checkbox("Large Text", value=self.accessibility_features['large_text'])
            
            with col2:
                reduced_motion = st.checkbox("Reduce Motion", value=self.accessibility_features['reduced_motion'])
                screen_reader = st.checkbox("Screen Reader Optimized", value=self.accessibility_features['screen_reader_friendly'])
            
            # Apply accessibility settings
            if high_contrast != self.accessibility_features['high_contrast']:
                self.accessibility_features['high_contrast'] = high_contrast
                st.success("High contrast mode updated!")
            
            if large_text != self.accessibility_features['large_text']:
                self.accessibility_features['large_text'] = large_text
                st.success("Text size updated!")
            
            st.markdown("### ⌨️ Keyboard Navigation")
            st.info("""
            **Keyboard shortcuts:**
            - Tab: Navigate between elements
            - Enter/Space: Activate buttons
            - Arrow keys: Navigate options
            - Escape: Close dialogs
            
            **All interactive elements are keyboard accessible.**
            """)
            
            st.markdown("### 🎧 Screen Reader Support")
            st.info("""
            **This interface is designed for screen readers:**
            - All images have descriptive alt text
            - Headings are properly structured
            - Form labels are clearly associated
            - Status messages are announced
            """)

class StressReductionTools:
    """Tools for reducing stress and anxiety"""
    
    def __init__(self):
        self.breathing_exercises = [
            {
                "name": "4-7-8 Breathing",
                "description": "Inhale for 4, hold for 7, exhale for 8",
                "duration": "2 minutes",
                "benefit": "Calms nervous system"
            },
            {
                "name": "Box Breathing",
                "description": "Inhale for 4, hold for 4, exhale for 4, hold for 4",
                "duration": "3 minutes",
                "benefit": "Reduces stress and anxiety"
            },
            {
                "name": "Deep Belly Breathing",
                "description": "Place hand on belly, breathe deeply",
                "duration": "1 minute",
                "benefit": "Activates relaxation response"
            }
        ]
    
    def render_breathing_exercise(self) -> None:
        """Render interactive breathing exercise"""
        st.markdown("## 🫁 Take a Moment to Breathe")
        
        exercise = random.choice(self.breathing_exercises)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        ">
            <h3>🧘‍♀️ {exercise['name']}</h3>
            <p><strong>{exercise['description']}</strong></p>
            <p>Duration: {exercise['duration']}</p>
            <p>Benefit: {exercise['benefit']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🫁 Start Breathing Exercise"):
            self.run_breathing_timer()
    
    def run_breathing_timer(self) -> None:
        """Run a breathing timer"""
        st.markdown("### 🫁 Follow the rhythm...")
        
        # Simple breathing timer
        for i in range(5):  # 5 breaths
            st.markdown(f"**Breath {i+1}/5**")
            
            # Inhale
            st.markdown("🫁 **Inhale** (4 seconds)")
            st.progress(0.25)
            
            # Hold
            st.markdown("⏸️ **Hold** (7 seconds)")
            st.progress(0.5)
            
            # Exhale
            st.markdown("🫁 **Exhale** (8 seconds)")
            st.progress(0.75)
            
            # Hold
            st.markdown("⏸️ **Hold** (4 seconds)")
            st.progress(1.0)
            
            st.markdown("---")
        
        st.success("Great job! You've completed the breathing exercise. How are you feeling?")

class EncouragementSystem:
    """System for providing ongoing encouragement"""
    
    def __init__(self):
        self.encouragement_messages = [
            "Every step you take brings you closer to your goals.",
            "You're building important skills for your future.",
            "Your persistence will pay off in the long run.",
            "You're showing real maturity by tackling this head-on.",
            "Many students never even start this process - you're ahead of the game!",
            "Your future self will thank you for doing this now.",
            "You're not just applying for aid, you're investing in your future.",
            "Every question you ask makes you stronger and more informed.",
            "You're taking control of your education - that's powerful!",
            "Remember: you're not alone in this journey."
        ]
    
    def render_progress_encouragement(self, completed_steps: int, total_steps: int) -> None:
        """Render encouragement based on progress"""
        progress_percentage = (completed_steps / total_steps) * 100
        
        if progress_percentage >= 80:
            message = "🎉 You're almost there! You've made incredible progress."
        elif progress_percentage >= 50:
            message = "🚀 You're more than halfway there! Keep up the great work."
        elif progress_percentage >= 25:
            message = "💪 You're making real progress! Every step counts."
        else:
            message = "🌟 You've taken the first step - that's often the hardest part!"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            text-align: center;
        ">
            <h4>{message}</h4>
            <p>Progress: {completed_steps}/{total_steps} steps completed ({progress_percentage:.0f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_random_encouragement(self) -> None:
        """Render a random encouragement message"""
        message = random.choice(self.encouragement_messages)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            text-align: center;
        ">
            <p style="font-style: italic; margin: 0;">💝 {message}</p>
        </div>
        """, unsafe_allow_html=True)

class AccessibilityHelper:
    """Helper for accessibility features"""
    
    def __init__(self):
        self.accessibility_settings = {
            'font_size': 'normal',
            'contrast': 'normal',
            'motion': 'normal',
            'focus_indicators': True
        }
    
    def render_accessibility_controls(self) -> None:
        """Render accessibility control panel"""
        st.markdown("## ♿ Accessibility Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            font_size = st.selectbox(
                "Text Size",
                ["Small", "Normal", "Large", "Extra Large"],
                index=1
            )
            
            contrast = st.selectbox(
                "Contrast",
                ["Normal", "High", "Very High"],
                index=0
            )
        
        with col2:
            motion = st.selectbox(
                "Motion",
                ["Normal", "Reduced"],
                index=0
            )
            
            focus_indicators = st.checkbox(
                "Show Focus Indicators",
                value=True
            )
        
        # Apply settings
        if st.button("Apply Accessibility Settings"):
            self.accessibility_settings.update({
                'font_size': font_size.lower(),
                'contrast': contrast.lower(),
                'motion': motion.lower(),
                'focus_indicators': focus_indicators
            })
            st.success("Accessibility settings applied!")
    
    def get_accessibility_css(self) -> str:
        """Get CSS for current accessibility settings"""
        css = ""
        
        if self.accessibility_settings['font_size'] == 'large':
            css += "body { font-size: 18px; }"
        elif self.accessibility_settings['font_size'] == 'extra large':
            css += "body { font-size: 20px; }"
        
        if self.accessibility_settings['contrast'] == 'high':
            css += """
            :root {
                --text-primary: #000000;
                --text-secondary: #333333;
                --background-white: #ffffff;
                --border-color: #000000;
            }
            """
        elif self.accessibility_settings['contrast'] == 'very high':
            css += """
            :root {
                --text-primary: #000000;
                --text-secondary: #000000;
                --background-white: #ffffff;
                --border-color: #000000;
            }
            """
        
        if self.accessibility_settings['motion'] == 'reduced':
            css += """
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            """
        
        if self.accessibility_settings['focus_indicators']:
            css += """
            *:focus {
                outline: 3px solid #2563eb !important;
                outline-offset: 2px !important;
            }
            """
        
        return css

def create_emotional_support_system() -> EmotionalSupportSystem:
    """Factory function to create emotional support system"""
    return EmotionalSupportSystem()

def create_stress_reduction_tools() -> StressReductionTools:
    """Factory function to create stress reduction tools"""
    return StressReductionTools()

def create_encouragement_system() -> EncouragementSystem:
    """Factory function to create encouragement system"""
    return EncouragementSystem()

def create_accessibility_helper() -> AccessibilityHelper:
    """Factory function to create accessibility helper"""
    return AccessibilityHelper() 