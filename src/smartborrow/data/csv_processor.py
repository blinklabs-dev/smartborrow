"""
CSV Processor for SmartBorrow

Analyzes complaints.csv to extract patterns, categorize complaints,
and create FAQ-style data from common complaints.
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import Counter, defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComplaintCategory:
    """Represents a category of complaints with analysis"""
    category_name: str
    complaint_count: int
    percentage: float
    common_keywords: List[str]
    common_companies: List[str]
    common_issues: List[str]
    sample_complaints: List[str]
    avg_response_time: Optional[float] = None

@dataclass
class FAQEntry:
    """Represents a FAQ entry derived from complaints"""
    question: str
    answer: str
    category: str
    frequency: int
    keywords: List[str]

class CSVProcessor:
    """Comprehensive CSV processing for SmartBorrow complaints data"""
    
    def __init__(self, raw_data_path: str = "data/raw") -> None:
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path("data/processed")
        self.processed_data_path.mkdir(exist_ok=True)
        
        # Complaint categorization keywords
        self.category_keywords = {
            'payment_issues': [
                'payment', 'autopay', 'auto debit', 'payment reversal', 
                'payment not processed', 'billing', 'payment amount',
                'monthly payment', 'payment plan'
            ],
            'servicer_problems': [
                'servicer', 'nelnet', 'aidvantage', 'mohela', 'edfinancial',
                'maximus', 'navient', 'loan servicer', 'servicing'
            ],
            'information_requests': [
                'information', 'loan balance', 'loan terms', 'account status',
                'need information', 'loan details', 'account information'
            ],
            'forgiveness_issues': [
                'forgiveness', 'discharge', 'cancellation', 'teacher loan forgiveness',
                'loan forgiveness', 'discharge request'
            ],
            'credit_reporting': [
                'credit report', 'credit score', 'credit bureau', 'credit reporting',
                'credit history', 'credit check', 'credit inquiry'
            ],
            'data_privacy': [
                'data breach', 'privacy', 'ferpa', 'personal information',
                'data compromise', 'unauthorized access', 'privacy violation'
            ],
            'application_verification': [
                'application', 'verification', 'documentation', 'income verification',
                'recertification', 'idr application', 'income-driven repayment'
            ],
            'communication_issues': [
                'communication', 'contact', 'phone call', 'email', 'response',
                'customer service', 'representative', 'support'
            ]
        }
        
        # Common pain points and keywords
        self.pain_point_keywords = [
            'frustrated', 'angry', 'disappointed', 'confused', 'worried',
            'stress', 'anxiety', 'difficult', 'complicated', 'unclear',
            'misleading', 'incorrect', 'wrong', 'error', 'mistake',
            'delay', 'wait', 'time', 'long', 'slow', 'unresponsive'
        ]
    
    def load_complaints_data(self) -> pd.DataFrame:
        """Load and clean complaints CSV data"""
        csv_path = self.raw_data_path / "complaints.csv"
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Complaints file not found: {csv_path}")
        
        # Load CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} complaints from {csv_path}")
        
        # Basic cleaning
        df = df.dropna(subset=['Consumer complaint narrative'])
        df = df[df['Consumer complaint narrative'].str.len() > 10]
        
        # Convert date columns
        date_columns = ['Date received', 'Date sent to company']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        logger.info(f"Cleaned data: {len(df)} valid complaints")
        return df
    
    def categorize_complaints(self, df: pd.DataFrame) -> Dict[str, List[int]]:
        """Categorize complaints based on keywords and content"""
        categories = defaultdict(list)
        
        for idx, row in df.iterrows():
            narrative = str(row.get('Consumer complaint narrative', '')).lower()
            issue = str(row.get('Issue', '')).lower()
            sub_issue = str(row.get('Sub-issue', '')).lower()
            
            # Combine all text for analysis
            combined_text = f"{narrative} {issue} {sub_issue}"
            
            # Check each category
            for category_name, keywords in self.category_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        categories[category_name].append(idx)
                        break  # Only assign to first matching category
        
        # Add uncategorized complaints
        categorized_indices = set()
        for indices in categories.values():
            categorized_indices.update(indices)
        
        uncategorized = [idx for idx in df.index if idx not in categorized_indices]
        if uncategorized:
            categories['uncategorized'] = uncategorized
        
        return dict(categories)
    
    def extract_keywords_from_text(self, text: str, top_n: int = 10) -> List[str]:
        """Extract most common keywords from text"""
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'shall'
        }
        
        # Filter words
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(top_n)]
    
    def analyze_category(self, df: pd.DataFrame, category_name: str, indices: List[int]) -> ComplaintCategory:
        """Analyze a specific complaint category"""
        category_df = df.loc[indices]
        
        # Combine all narratives for keyword analysis
        all_narratives = ' '.join(category_df['Consumer complaint narrative'].astype(str))
        common_keywords = self.extract_keywords_from_text(all_narratives, top_n=15)
        
        # Get common companies
        company_counts = category_df['Company'].value_counts()
        common_companies = company_counts.head(5).index.tolist()
        
        # Get common issues
        issue_counts = category_df['Issue'].value_counts()
        common_issues = issue_counts.head(5).index.tolist()
        
        # Get sample complaints (first 3)
        sample_complaints = category_df['Consumer complaint narrative'].head(3).tolist()
        
        # Calculate percentage
        percentage = (len(indices) / len(df)) * 100
        
        # Calculate average response time if available
        avg_response_time = None
        if 'Date received' in category_df.columns and 'Date sent to company' in category_df.columns:
            response_times = (category_df['Date sent to company'] - category_df['Date received']).dt.days
            avg_response_time = response_times.mean()
        
        return ComplaintCategory(
            category_name=category_name,
            complaint_count=len(indices),
            percentage=percentage,
            common_keywords=common_keywords,
            common_companies=common_companies,
            common_issues=common_issues,
            sample_complaints=sample_complaints,
            avg_response_time=avg_response_time
        )
    
    def identify_pain_points(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Identify common pain points and emotional indicators"""
        pain_points = defaultdict(list)
        
        for idx, row in df.iterrows():
            narrative = str(row.get('Consumer complaint narrative', '')).lower()
            
            for keyword in self.pain_point_keywords:
                if keyword in narrative:
                    pain_points[keyword].append(idx)
        
        # Convert to lists of complaint IDs
        return {k: list(set(v)) for k, v in pain_points.items()}
    
    def create_faq_entries(self, df: pd.DataFrame, categories: Dict[str, List[int]]) -> List[FAQEntry]:
        """Create FAQ entries from common complaint patterns"""
        faq_entries = []
        
        # Common question templates
        question_templates = {
            'payment_issues': [
                "Why isn't my auto-payment working?",
                "How do I fix payment processing issues?",
                "What should I do if my payment wasn't processed?"
            ],
            'servicer_problems': [
                "How do I contact my loan servicer?",
                "What if my servicer isn't responding?",
                "How do I change my loan servicer?"
            ],
            'information_requests': [
                "How do I find my loan balance?",
                "Where can I get my loan information?",
                "How do I access my loan details?"
            ],
            'forgiveness_issues': [
                "How do I apply for loan forgiveness?",
                "What documents do I need for forgiveness?",
                "How long does forgiveness take?"
            ],
            'credit_reporting': [
                "How do I fix errors on my credit report?",
                "What if my loan is incorrectly reported?",
                "How do I dispute credit report errors?"
            ],
            'data_privacy': [
                "What should I do about data privacy concerns?",
                "How do I report a data breach?",
                "What are my privacy rights as a borrower?"
            ],
            'application_verification': [
                "How do I complete income verification?",
                "What documents do I need for verification?",
                "How do I recertify my income-driven repayment?"
            ],
            'communication_issues': [
                "How do I get better customer service?",
                "What if I can't reach my servicer?",
                "How do I escalate my complaint?"
            ]
        }
        
        # Answer templates based on common solutions
        answer_templates = {
            'payment_issues': [
                "Contact your loan servicer immediately and document all communication. Keep records of payment attempts and any error messages.",
                "Check your bank account to ensure sufficient funds. Verify your payment method is current and not expired.",
                "Request a payment history and dispute any incorrect charges. Consider setting up automatic payments for future payments."
            ],
            'servicer_problems': [
                "Contact your servicer through multiple channels: phone, email, and their online portal. Keep detailed records of all attempts.",
                "File a complaint with the Consumer Financial Protection Bureau (CFPB) if your servicer is unresponsive.",
                "You can request a servicer change through the Department of Education, but this is typically only done in special circumstances."
            ],
            'information_requests': [
                "Log into your servicer's website or call them directly. You can also check StudentAid.gov for federal loan information.",
                "Contact your loan servicer by phone or through their online portal. Have your account information ready.",
                "Use the National Student Loan Data System (NSLDS) at StudentAid.gov to view all your federal loan information."
            ],
            'forgiveness_issues': [
                "Complete the appropriate forgiveness application and submit all required documentation. Keep copies of everything you submit.",
                "Gather all required documents including employment certification, tax returns, and any other supporting materials.",
                "The process can take several months. Follow up regularly and keep detailed records of your application status."
            ],
            'credit_reporting': [
                "Dispute errors directly with the credit bureaus and your loan servicer. Provide documentation to support your dispute.",
                "Contact your loan servicer to correct any reporting errors. You may also need to contact the credit bureaus directly.",
                "File a complaint with the CFPB if the error persists. Keep all documentation of your dispute attempts."
            ],
            'data_privacy': [
                "Contact the Department of Education's Privacy Office and your loan servicer immediately. Consider placing a fraud alert on your credit.",
                "Report the breach to the Federal Trade Commission and your state's attorney general. Monitor your accounts for suspicious activity.",
                "You have rights under FERPA and other privacy laws. Consider consulting with a consumer protection attorney."
            ],
            'application_verification': [
                "Submit all required documentation promptly and keep copies. Follow up if you don't receive confirmation within 30 days.",
                "Provide complete and accurate information including all income sources, tax returns, and supporting documentation.",
                "Submit your recertification before the deadline to avoid payment increases. Use the IRS Data Retrieval Tool when possible."
            ],
            'communication_issues': [
                "Try multiple contact methods and keep detailed records. Escalate to supervisors if frontline staff can't help.",
                "File a complaint with the CFPB and your state's consumer protection agency. Document all communication attempts.",
                "Consider contacting your congressional representative or senator for assistance with federal loan issues."
            ]
        }
        
        for category_name, indices in categories.items():
            if category_name in question_templates and len(indices) > 0:
                # Get the most common keywords for this category
                category_df = df.loc[indices]
                all_narratives = ' '.join(category_df['Consumer complaint narrative'].astype(str))
                keywords = self.extract_keywords_from_text(all_narratives, top_n=5)
                
                # Create FAQ entries for this category
                questions = question_templates[category_name]
                answers = answer_templates.get(category_name, ["Contact your loan servicer for assistance."])
                
                for i, question in enumerate(questions):
                    answer = answers[i] if i < len(answers) else answers[0]
                    
                    faq_entry = FAQEntry(
                        question=question,
                        answer=answer,
                        category=category_name,
                        frequency=len(indices),
                        keywords=keywords
                    )
                    faq_entries.append(faq_entry)
        
        return faq_entries
    
    def analyze_complaint_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall complaint patterns and trends"""
        analysis = {
            'total_complaints': len(df),
            'date_range': {},
            'company_analysis': {},
            'issue_analysis': {},
            'state_analysis': {},
            'response_analysis': {}
        }
        
        # Date range analysis
        if 'Date received' in df.columns:
            analysis['date_range'] = {
                'earliest': df['Date received'].min().strftime('%Y-%m-%d'),
                'latest': df['Date received'].max().strftime('%Y-%m-%d'),
                'total_days': (df['Date received'].max() - df['Date received'].min()).days
            }
        
        # Company analysis
        if 'Company' in df.columns:
            company_counts = df['Company'].value_counts()
            analysis['company_analysis'] = {
                'top_companies': company_counts.head(10).to_dict(),
                'total_companies': len(company_counts)
            }
        
        # Issue analysis
        if 'Issue' in df.columns:
            issue_counts = df['Issue'].value_counts()
            analysis['issue_analysis'] = {
                'top_issues': issue_counts.head(10).to_dict(),
                'total_issue_types': len(issue_counts)
            }
        
        # State analysis
        if 'State' in df.columns:
            state_counts = df['State'].value_counts()
            analysis['state_analysis'] = {
                'top_states': state_counts.head(10).to_dict(),
                'total_states': len(state_counts)
            }
        
        # Response analysis
        if 'Timely response?' in df.columns:
            timely_counts = df['Timely response?'].value_counts()
            analysis['response_analysis'] = {
                'timely_responses': timely_counts.get('Yes', 0),
                'untimely_responses': timely_counts.get('No', 0),
                'timely_percentage': (timely_counts.get('Yes', 0) / len(df)) * 100
            }
        
        return analysis
    
    def save_processed_data(self, categories: Dict[str, ComplaintCategory], 
                          faq_entries: List[FAQEntry], 
                          analysis: Dict[str, Any]) -> None:
        """Save processed data to JSON files"""
        
        # Save category analysis
        categories_data = {}
        for category_name, category in categories.items():
            categories_data[category_name] = {
                'complaint_count': category.complaint_count,
                'percentage': category.percentage,
                'common_keywords': category.common_keywords,
                'common_companies': category.common_companies,
                'common_issues': category.common_issues,
                'sample_complaints': category.sample_complaints,
                'avg_response_time': category.avg_response_time
            }
        
        categories_file = self.processed_data_path / "complaint_categories.json"
        with open(categories_file, 'w') as f:
            json.dump(categories_data, f, indent=2)
        
        # Save FAQ entries
        faq_data = []
        for entry in faq_entries:
            faq_data.append({
                'question': entry.question,
                'answer': entry.answer,
                'category': entry.category,
                'frequency': entry.frequency,
                'keywords': entry.keywords
            })
        
        faq_file = self.processed_data_path / "complaint_faqs.json"
        with open(faq_file, 'w') as f:
            json.dump(faq_data, f, indent=2)
        
        # Save overall analysis
        analysis_file = self.processed_data_path / "complaint_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Saved processed data to {categories_file}, {faq_file}, and {analysis_file}")
    
    def process_complaints(self) -> Tuple[Dict[str, ComplaintCategory], List[FAQEntry], Dict[str, Any]]:
        """Main function to process complaints data"""
        logger.info("Starting complaints processing...")
        
        # Load data
        df = self.load_complaints_data()
        
        # Categorize complaints
        categories_indices = self.categorize_complaints(df)
        
        # Analyze each category
        categories = {}
        for category_name, indices in categories_indices.items():
            categories[category_name] = self.analyze_category(df, category_name, indices)
        
        # Create FAQ entries
        faq_entries = self.create_faq_entries(df, categories_indices)
        
        # Analyze overall patterns
        analysis = self.analyze_complaint_patterns(df)
        
        # Save processed data
        self.save_processed_data(categories, faq_entries, analysis)
        
        logger.info(f"Complaints processing complete. Processed {len(df)} complaints across {len(categories)} categories")
        logger.info(f"Created {len(faq_entries)} FAQ entries")
        
        return categories, faq_entries, analysis

def main() -> None:
    """Main function to process complaints data"""
    processor = CSVProcessor()
    
    try:
        categories, faq_entries, analysis = processor.process_complaints()
        
        # Print summary
        logger.info("\nComplaints Processing Summary:")
        logger.info("Total complaints processed: {analysis['total_complaints']}")
        logger.info("Categories identified: {len(categories)}")
        logger.info("FAQ entries created: {len(faq_entries)}")
        
        logger.info("\nTop complaint categories:")
        for category_name, category in sorted(categories.items(), key=lambda x: x[1].complaint_count, reverse=True)[:5]:
            logger.info("  {category_name}: {category.complaint_count} complaints ({category.percentage:.1f}%)")
        
        return categories, faq_entries, analysis
        
    except Exception as e:
        logger.error(f"Error processing complaints: {e}")
        raise

if __name__ == "__main__":
    main() 