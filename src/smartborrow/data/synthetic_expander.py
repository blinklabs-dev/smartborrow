"""
Synthetic Expander for SmartBorrow

Generates additional Q&A pairs from PDF content, creates variations
of procedures and requirements, and builds test datasets from existing content.
"""

import json
import re
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SyntheticQA:
    """Represents a synthetic Q&A pair"""
    question: str
    answer: str
    category: str
    source_document: str
    confidence: float
    variations: List[str] = None

@dataclass
class TestCase:
    """Represents a test case for evaluation"""
    scenario: str
    expected_answer: str
    category: str
    difficulty: str
    source_document: str

class SyntheticExpander:
    """Expands content by generating synthetic Q&A pairs and test datasets"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        
        # Question templates for different categories
        self.question_templates = {
            'pell_grant': [
                "What is the maximum Pell Grant amount for {year}?",
                "How do I qualify for a Pell Grant?",
                "What is the income limit for Pell Grant eligibility?",
                "Can I receive a Pell Grant if I already have a bachelor's degree?",
                "How is my Pell Grant amount calculated?",
                "What happens to my Pell Grant if I drop classes?",
                "Can I receive a Pell Grant for summer classes?",
                "How do I apply for a Pell Grant?",
                "What documents do I need for Pell Grant verification?",
                "How long does it take to receive my Pell Grant?"
            ],
            'direct_loans': [
                "What is the difference between subsidized and unsubsidized loans?",
                "What are the current interest rates for Direct Loans?",
                "What are the loan limits for undergraduate students?",
                "How do I apply for a Direct Loan?",
                "What is the grace period for Direct Loans?",
                "Can I consolidate my Direct Loans?",
                "What are the repayment options for Direct Loans?",
                "How do I check my Direct Loan balance?",
                "What happens if I default on my Direct Loan?",
                "Can I defer my Direct Loan payments?"
            ],
            'cost_of_attendance': [
                "What is included in the cost of attendance?",
                "How is the cost of attendance calculated?",
                "Can the cost of attendance be appealed?",
                "What is the average cost of attendance for {school_type}?",
                "How does the cost of attendance affect my financial aid?",
                "What expenses are not included in the cost of attendance?",
                "How often is the cost of attendance updated?",
                "Can I get additional aid if my expenses exceed the cost of attendance?",
                "What is the difference between in-state and out-of-state cost of attendance?",
                "How do I find the cost of attendance for my school?"
            ],
            'verification': [
                "What is verification and why was I selected?",
                "What documents do I need for verification?",
                "How do I submit verification documents?",
                "What happens if I don't complete verification?",
                "How long does verification take?",
                "Can I appeal a verification decision?",
                "What is the deadline for verification?",
                "How do I know if my verification is complete?",
                "What if my verification documents are lost?",
                "Can I get an extension for verification?"
            ],
            'repayment_plans': [
                "What is an income-driven repayment plan?",
                "How do I apply for an income-driven repayment plan?",
                "What is the difference between IBR and PAYE?",
                "How often do I need to recertify my income?",
                "What happens if I don't recertify on time?",
                "Can I switch between repayment plans?",
                "What is the standard repayment plan?",
                "How is my monthly payment calculated?",
                "What is loan forgiveness and how do I qualify?",
                "How do I apply for Public Service Loan Forgiveness?"
            ],
            'forgiveness': [
                "What is Public Service Loan Forgiveness (PSLF)?",
                "How do I qualify for PSLF?",
                "What is Teacher Loan Forgiveness?",
                "How do I apply for loan forgiveness?",
                "What documents do I need for forgiveness?",
                "How long does forgiveness take?",
                "Can I apply for multiple forgiveness programs?",
                "What happens if my forgiveness application is denied?",
                "How do I track my forgiveness progress?",
                "What is the difference between forgiveness and discharge?"
            ]
        }
        
        # Answer templates and variations
        self.answer_templates = {
            'pell_grant': [
                "The maximum Pell Grant amount for {year} is ${amount}. The actual amount you receive depends on your Expected Family Contribution (EFC), cost of attendance, and enrollment status.",
                "To qualify for a Pell Grant, you must demonstrate financial need, be enrolled in an eligible program, and meet citizenship requirements. Your Expected Family Contribution (EFC) must be below the maximum threshold.",
                "Pell Grant eligibility is based on your Expected Family Contribution (EFC). For {year}, students with an EFC of ${efc_limit} or less may be eligible for a Pell Grant.",
                "Generally, you cannot receive a Pell Grant if you already have a bachelor's degree. However, there are exceptions for certain post-baccalaureate teacher certification programs.",
                "Your Pell Grant amount is calculated based on your Expected Family Contribution (EFC), cost of attendance, and enrollment status. The formula is: Cost of Attendance - EFC = Financial Need."
            ],
            'direct_loans': [
                "Subsidized loans are based on financial need and the government pays the interest while you're in school. Unsubsidized loans are not based on need and you're responsible for all interest.",
                "Current interest rates for Direct Loans are set annually by Congress. For {year}, undergraduate subsidized and unsubsidized loans have a {rate}% interest rate.",
                "Annual loan limits for undergraduate students depend on your year in school and dependency status. First-year dependent students can borrow up to ${limit} in subsidized loans.",
                "To apply for a Direct Loan, you must complete the FAFSA and be enrolled at least half-time in an eligible program. Your school will determine your eligibility and loan amount.",
                "The grace period for Direct Loans is 6 months after you graduate, leave school, or drop below half-time enrollment. During this time, you don't have to make payments."
            ],
            'cost_of_attendance': [
                "The cost of attendance includes tuition and fees, room and board, books and supplies, transportation, and personal expenses. It represents the total cost of attending your school for one academic year.",
                "The cost of attendance is calculated by your school based on average costs for students. It includes both direct costs (tuition, fees) and indirect costs (transportation, personal expenses).",
                "Yes, you can appeal your cost of attendance if you have unusual circumstances that increase your educational expenses. Contact your school's financial aid office for the appeal process.",
                "The average cost of attendance varies by school type and location. Public in-state schools typically cost ${amount} per year, while private schools may cost ${private_amount} or more.",
                "The cost of attendance directly affects your financial need calculation. Your need is determined by: Cost of Attendance - Expected Family Contribution = Financial Need."
            ],
            'verification': [
                "Verification is a process where your school confirms the information on your FAFSA. You may be selected randomly or because of inconsistent information. About 30% of students are selected each year.",
                "For verification, you typically need to provide tax returns, W-2 forms, and other income documentation. Your school will provide a specific list of required documents.",
                "Submit verification documents to your school's financial aid office by the deadline. You can usually submit them online, by mail, or in person. Keep copies of everything you submit.",
                "If you don't complete verification, you won't receive federal financial aid. Your FAFSA will be considered incomplete until verification is finished.",
                "Verification typically takes 2-4 weeks, but can take longer during peak periods. Contact your financial aid office if it's taking longer than expected."
            ],
            'repayment_plans': [
                "Income-driven repayment plans base your monthly payment on your income and family size. They include IBR, PAYE, REPAYE, and ICR. Your payment can be as low as $0 if your income is low enough.",
                "To apply for an income-driven repayment plan, contact your loan servicer. You'll need to provide income documentation and may need to recertify annually.",
                "IBR (Income-Based Repayment) and PAYE (Pay As You Earn) are both income-driven plans, but PAYE generally has lower payments and faster forgiveness. PAYE is only available to newer borrowers.",
                "You must recertify your income annually for income-driven repayment plans. If you don't recertify on time, your payment may increase to the standard payment amount.",
                "If you don't recertify on time, your payment will revert to the standard payment amount, which is usually higher than your income-driven payment."
            ],
            'forgiveness': [
                "Public Service Loan Forgiveness (PSLF) forgives your remaining loan balance after 120 qualifying payments while working full-time for a qualifying employer.",
                "To qualify for PSLF, you must work full-time for a qualifying employer (government or nonprofit), have Direct Loans, and make 120 qualifying payments under an income-driven repayment plan.",
                "Teacher Loan Forgiveness provides up to ${amount} in forgiveness for teachers who work in low-income schools for 5 consecutive years. You must have Direct or FFEL loans.",
                "To apply for loan forgiveness, submit the appropriate application to your loan servicer. For PSLF, use the PSLF application. For Teacher Loan Forgiveness, use the Teacher Loan Forgiveness application.",
                "You'll need employment certification forms, proof of qualifying payments, and other documentation depending on the forgiveness program. Keep copies of everything you submit."
            ]
        }
        
        # Variation patterns
        self.variation_patterns = {
            'amounts': ['$5,500', '$6,500', '$7,500', '$8,000', '$9,000', '$10,000'],
            'years': ['2024', '2025', '2026', '2027', '2028'],
            'rates': ['3.73%', '4.99%', '5.50%', '6.28%', '7.54%'],
            'school_types': ['public university', 'private college', 'community college', 'trade school'],
            'time_periods': ['2-4 weeks', '4-6 weeks', '6-8 weeks', '30 days', '60 days'],
            'percentages': ['10%', '15%', '20%', '25%', '30%']
        }
    
    def load_processed_data(self) -> Dict[str, Any]:
        """Load all processed data for expansion"""
        processed_data = {}
        
        # Load structured knowledge
        knowledge_file = self.processed_data_path / "structured_knowledge.json"
        if knowledge_file.exists():
            with open(knowledge_file, 'r') as f:
                processed_data['structured_knowledge'] = json.load(f)
        
        # Load FAQ data
        faq_file = self.processed_data_path / "complaint_faqs.json"
        if faq_file.exists():
            with open(faq_file, 'r') as f:
                processed_data['faqs'] = json.load(f)
        
        # Load numerical data
        numerical_file = self.processed_data_path / "numerical_data.json"
        if numerical_file.exists():
            with open(numerical_file, 'r') as f:
                processed_data['numerical_data'] = json.load(f)
        
        # Load cross-references
        cross_refs_file = self.processed_data_path / "cross_references.json"
        if cross_refs_file.exists():
            with open(cross_refs_file, 'r') as f:
                processed_data['cross_references'] = json.load(f)
        
        logger.info(f"Loaded processed data: {list(processed_data.keys())}")
        return processed_data
    
    def generate_synthetic_qa_pairs(self, processed_data: Dict[str, Any]) -> List[SyntheticQA]:
        """Generate synthetic Q&A pairs from processed data"""
        synthetic_qa_pairs = []
        
        # Get structured knowledge
        structured_knowledge = processed_data.get('structured_knowledge', {})
        
        for concept_name, knowledge in structured_knowledge.items():
            if concept_name in self.question_templates:
                # Get question templates for this concept
                questions = self.question_templates[concept_name]
                answers = self.answer_templates.get(concept_name, [])
                
                # Generate variations for each template
                for i, question_template in enumerate(questions):
                    # Create variations of the question
                    question_variations = self._create_question_variations(question_template, concept_name)
                    
                    # Get corresponding answer template
                    answer_template = answers[i] if i < len(answers) else answers[0] if answers else ""
                    
                    # Create variations of the answer
                    answer_variations = self._create_answer_variations(answer_template, concept_name)
                    
                    # Generate multiple Q&A pairs
                    for j in range(min(3, len(question_variations))):  # Generate up to 3 variations
                        qa_pair = SyntheticQA(
                            question=question_variations[j],
                            answer=answer_variations[j] if j < len(answer_variations) else answer_variations[0],
                            category=concept_name,
                            source_document=knowledge.get('source_documents', ['unknown'])[0] if knowledge.get('source_documents') else 'unknown',
                            confidence=0.8,
                            variations=question_variations[:3]  # Store first 3 variations
                        )
                        synthetic_qa_pairs.append(qa_pair)
        
        return synthetic_qa_pairs
    
    def _create_question_variations(self, template: str, concept: str) -> List[str]:
        """Create variations of a question template"""
        variations = []
        
        # Replace placeholders with different values
        if '{year}' in template:
            for year in self.variation_patterns['years']:
                variations.append(template.replace('{year}', year))
        
        elif '{amount}' in template:
            for amount in self.variation_patterns['amounts']:
                variations.append(template.replace('{amount}', amount))
        
        elif '{rate}' in template:
            for rate in self.variation_patterns['rates']:
                variations.append(template.replace('{rate}', rate))
        
        elif '{school_type}' in template:
            for school_type in self.variation_patterns['school_types']:
                variations.append(template.replace('{school_type}', school_type))
        
        else:
            # Create simple variations by changing wording
            variations = [
                template,
                template.replace('What is', 'How do I find'),
                template.replace('How do I', 'What is the process to'),
                template.replace('What are', 'Can you explain'),
                template.replace('How is', 'What determines')
            ]
        
        return variations[:5]  # Limit to 5 variations
    
    def _create_answer_variations(self, template: str, concept: str) -> List[str]:
        """Create variations of an answer template"""
        variations = []
        
        # Replace placeholders with different values
        if '{year}' in template:
            for year in self.variation_patterns['years']:
                variations.append(template.replace('{year}', year))
        
        elif '{amount}' in template:
            for amount in self.variation_patterns['amounts']:
                variations.append(template.replace('{amount}', amount))
        
        elif '{rate}' in template:
            for rate in self.variation_patterns['rates']:
                variations.append(template.replace('{rate}', rate))
        
        elif '{efc_limit}' in template:
            for limit in ['$5,846', '$6,000', '$6,500', '$7,000']:
                variations.append(template.replace('{efc_limit}', limit))
        
        elif '{limit}' in template:
            for limit in ['$3,500', '$4,500', '$5,500', '$6,500']:
                variations.append(template.replace('{limit}', limit))
        
        else:
            # Create simple variations by changing wording
            variations = [
                template,
                template.replace('is', 'refers to'),
                template.replace('must', 'need to'),
                template.replace('should', 'are required to'),
                template.replace('can', 'are able to')
            ]
        
        return variations[:5]  # Limit to 5 variations
    
    def create_procedure_variations(self, processed_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create variations of procedures and requirements"""
        procedure_variations = []
        
        structured_knowledge = processed_data.get('structured_knowledge', {})
        
        for concept_name, knowledge in structured_knowledge.items():
            procedures = knowledge.get('procedures', [])
            requirements = knowledge.get('requirements', [])
            
            # Create variations of procedures
            for procedure in procedures[:3]:  # Limit to first 3 procedures
                variations = self._create_procedure_variations(procedure, concept_name)
                for variation in variations:
                    procedure_variations.append({
                        'original': procedure,
                        'variation': variation,
                        'category': concept_name,
                        'type': 'procedure'
                    })
            
            # Create variations of requirements
            for requirement in requirements[:3]:  # Limit to first 3 requirements
                variations = self._create_requirement_variations(requirement, concept_name)
                for variation in variations:
                    procedure_variations.append({
                        'original': requirement,
                        'variation': variation,
                        'category': concept_name,
                        'type': 'requirement'
                    })
        
        return procedure_variations
    
    def _create_procedure_variations(self, procedure: str, concept: str) -> List[str]:
        """Create variations of a procedure"""
        variations = []
        
        # Simple word substitutions
        substitutions = {
            'contact': ['call', 'reach out to', 'get in touch with', 'notify'],
            'submit': ['send', 'provide', 'file', 'turn in'],
            'complete': ['fill out', 'finish', 'fill in', 'answer'],
            'apply': ['submit an application for', 'request', 'ask for'],
            'verify': ['confirm', 'check', 'validate', 'prove']
        }
        
        # Create variations by substituting words
        for original_word, replacement_words in substitutions.items():
            if original_word in procedure.lower():
                for replacement in replacement_words:
                    variation = procedure.replace(original_word, replacement)
                    variations.append(variation)
        
        # Add original procedure
        variations.insert(0, procedure)
        
        return variations[:3]  # Limit to 3 variations
    
    def _create_requirement_variations(self, requirement: str, concept: str) -> List[str]:
        """Create variations of a requirement"""
        variations = []
        
        # Simple word substitutions
        substitutions = {
            'must': ['need to', 'are required to', 'have to', 'should'],
            'required': ['necessary', 'mandatory', 'needed', 'essential'],
            'eligible': ['qualified', 'entitled', 'able to receive'],
            'qualify': ['be eligible for', 'meet the criteria for', 'be entitled to']
        }
        
        # Create variations by substituting words
        for original_word, replacement_words in substitutions.items():
            if original_word in requirement.lower():
                for replacement in replacement_words:
                    variation = requirement.replace(original_word, replacement)
                    variations.append(variation)
        
        # Add original requirement
        variations.insert(0, requirement)
        
        return variations[:3]  # Limit to 3 variations
    
    def expand_complaint_categories(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand complaint categories with similar scenarios"""
        expanded_categories = []
        
        # Load complaint categories if available
        categories_file = self.processed_data_path / "complaint_categories.json"
        if categories_file.exists():
            with open(categories_file, 'r') as f:
                complaint_categories = json.load(f)
            
            for category_name, category_data in complaint_categories.items():
                # Create similar scenarios based on common keywords
                common_keywords = category_data.get('common_keywords', [])
                sample_complaints = category_data.get('sample_complaints', [])
                
                # Generate similar scenarios
                similar_scenarios = self._generate_similar_scenarios(category_name, common_keywords, sample_complaints)
                
                expanded_categories.append({
                    'original_category': category_name,
                    'original_data': category_data,
                    'similar_scenarios': similar_scenarios,
                    'expanded_keywords': self._expand_keywords(common_keywords)
                })
        
        return expanded_categories
    
    def _generate_similar_scenarios(self, category: str, keywords: List[str], samples: List[str]) -> List[str]:
        """Generate similar scenarios based on category and keywords"""
        scenarios = []
        
        # Template scenarios based on category
        category_templates = {
            'payment_issues': [
                "I set up autopay but my payment wasn't processed on time",
                "My payment was reversed without explanation",
                "I'm being charged late fees even though I made my payment",
                "My payment amount changed without notice",
                "I can't access my payment history online"
            ],
            'servicer_problems': [
                "I can't reach my loan servicer by phone",
                "My servicer transferred my loan without notice",
                "I'm getting conflicting information from different representatives",
                "My servicer's website is not working",
                "I'm being transferred between departments repeatedly"
            ],
            'information_requests': [
                "I need to know my current loan balance",
                "I can't find my loan account information",
                "I need to update my contact information",
                "I want to know my payment due date",
                "I need to verify my loan servicer"
            ],
            'forgiveness_issues': [
                "My forgiveness application is taking too long",
                "I'm not sure if my employment qualifies for forgiveness",
                "My forgiveness application was denied",
                "I need help tracking my forgiveness progress",
                "I'm confused about forgiveness requirements"
            ]
        }
        
        # Get templates for this category
        templates = category_templates.get(category, [])
        
        # Create variations of templates
        for template in templates:
            # Replace keywords with variations
            variation = template
            for keyword in keywords[:3]:  # Use first 3 keywords
                if keyword in variation.lower():
                    # Create a variation by changing the keyword
                    variation = variation.replace(keyword, f"different_{keyword}")
                    break
            
            scenarios.append(variation)
        
        return scenarios[:5]  # Limit to 5 scenarios
    
    def _expand_keywords(self, keywords: List[str]) -> List[str]:
        """Expand keywords with related terms"""
        expanded = []
        
        # Keyword expansion mappings
        expansions = {
            'payment': ['autopay', 'billing', 'due date', 'amount', 'processing'],
            'servicer': ['loan servicer', 'company', 'provider', 'manager'],
            'information': ['details', 'data', 'records', 'account', 'status'],
            'forgiveness': ['discharge', 'cancellation', 'waiver', 'relief'],
            'verification': ['documentation', 'proof', 'evidence', 'confirmation'],
            'application': ['form', 'request', 'submission', 'petition']
        }
        
        for keyword in keywords:
            expanded.append(keyword)
            # Add related terms
            for base_term, related_terms in expansions.items():
                if base_term in keyword.lower():
                    expanded.extend(related_terms)
        
        return list(set(expanded))  # Remove duplicates
    
    def build_test_datasets(self, processed_data: Dict[str, Any]) -> Dict[str, List[TestCase]]:
        """Build test datasets from existing content"""
        test_datasets = {
            'easy': [],
            'medium': [],
            'hard': []
        }
        
        # Create test cases from structured knowledge
        structured_knowledge = processed_data.get('structured_knowledge', {})
        
        for concept_name, knowledge in structured_knowledge.items():
            # Easy test cases - basic definitions
            if knowledge.get('definition'):
                test_datasets['easy'].append(TestCase(
                    scenario=f"What is {concept_name.replace('_', ' ')}?",
                    expected_answer=knowledge['definition'][:200] + "..." if len(knowledge['definition']) > 200 else knowledge['definition'],
                    category=concept_name,
                    difficulty='easy',
                    source_document=knowledge.get('source_documents', ['unknown'])[0] if knowledge.get('source_documents') else 'unknown'
                ))
            
            # Medium test cases - requirements and procedures
            requirements = knowledge.get('requirements', [])
            if requirements:
                test_datasets['medium'].append(TestCase(
                    scenario=f"What are the requirements for {concept_name.replace('_', ' ')}?",
                    expected_answer="; ".join(requirements[:3]),
                    category=concept_name,
                    difficulty='medium',
                    source_document=knowledge.get('source_documents', ['unknown'])[0] if knowledge.get('source_documents') else 'unknown'
                ))
            
            # Hard test cases - complex procedures
            procedures = knowledge.get('procedures', [])
            if procedures:
                test_datasets['hard'].append(TestCase(
                    scenario=f"How do I apply for {concept_name.replace('_', ' ')}?",
                    expected_answer="; ".join(procedures[:3]),
                    category=concept_name,
                    difficulty='hard',
                    source_document=knowledge.get('source_documents', ['unknown'])[0] if knowledge.get('source_documents') else 'unknown'
                ))
        
        # Create test cases from FAQ data
        faqs = processed_data.get('faqs', [])
        for faq in faqs[:10]:  # Use first 10 FAQs
            difficulty = 'medium'  # Default difficulty
            if any(word in faq['question'].lower() for word in ['how', 'what', 'why']):
                difficulty = 'hard'
            elif any(word in faq['question'].lower() for word in ['what is', 'define', 'explain']):
                difficulty = 'easy'
            
            test_datasets[difficulty].append(TestCase(
                scenario=faq['question'],
                expected_answer=faq['answer'],
                category=faq['category'],
                difficulty=difficulty,
                source_document='complaints_data'
            ))
        
        return test_datasets
    
    def save_synthetic_data(self, synthetic_qa_pairs: List[SyntheticQA],
                           procedure_variations: List[Dict[str, str]],
                           expanded_categories: List[Dict[str, Any]],
                           test_datasets: Dict[str, List[TestCase]]) -> None:
        """Save synthetic data to JSON files"""
        
        # Save synthetic Q&A pairs
        qa_data = []
        for qa in synthetic_qa_pairs:
            qa_data.append({
                'question': qa.question,
                'answer': qa.answer,
                'category': qa.category,
                'source_document': qa.source_document,
                'confidence': qa.confidence,
                'variations': qa.variations
            })
        
        qa_file = self.processed_data_path / "synthetic_qa_pairs.json"
        with open(qa_file, 'w') as f:
            json.dump(qa_data, f, indent=2)
        
        # Save procedure variations
        proc_file = self.processed_data_path / "procedure_variations.json"
        with open(proc_file, 'w') as f:
            json.dump(procedure_variations, f, indent=2)
        
        # Save expanded categories
        cat_file = self.processed_data_path / "expanded_categories.json"
        with open(cat_file, 'w') as f:
            json.dump(expanded_categories, f, indent=2)
        
        # Save test datasets
        test_data = {}
        for difficulty, test_cases in test_datasets.items():
            test_data[difficulty] = [
                {
                    'scenario': tc.scenario,
                    'expected_answer': tc.expected_answer,
                    'category': tc.category,
                    'difficulty': tc.difficulty,
                    'source_document': tc.source_document
                }
                for tc in test_cases
            ]
        
        test_file = self.processed_data_path / "test_datasets.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        logger.info(f"Saved synthetic data to {qa_file}, {proc_file}, {cat_file}, and {test_file}")
    
    def expand_content(self) -> Tuple[List[SyntheticQA], List[Dict[str, str]], 
                                   List[Dict[str, Any]], Dict[str, List[TestCase]]]:
        """Main function to expand content with synthetic data"""
        logger.info("Starting content expansion...")
        
        # Load processed data
        processed_data = self.load_processed_data()
        
        if not processed_data:
            logger.warning("No processed data found. Please run other processors first.")
            return [], [], [], {}
        
        # Generate synthetic Q&A pairs
        synthetic_qa_pairs = self.generate_synthetic_qa_pairs(processed_data)
        
        # Create procedure variations
        procedure_variations = self.create_procedure_variations(processed_data)
        
        # Expand complaint categories
        expanded_categories = self.expand_complaint_categories(processed_data)
        
        # Build test datasets
        test_datasets = self.build_test_datasets(processed_data)
        
        # Save synthetic data
        self.save_synthetic_data(synthetic_qa_pairs, procedure_variations, expanded_categories, test_datasets)
        
        logger.info(f"Content expansion complete.")
        logger.info(f"Generated {len(synthetic_qa_pairs)} synthetic Q&A pairs")
        logger.info(f"Created {len(procedure_variations)} procedure variations")
        logger.info(f"Expanded {len(expanded_categories)} complaint categories")
        logger.info(f"Built test datasets: {sum(len(cases) for cases in test_datasets.values())} total test cases")
        
        return synthetic_qa_pairs, procedure_variations, expanded_categories, test_datasets

def main() -> None:
    """Main function to expand content"""
    expander = SyntheticExpander()
    
    try:
        synthetic_qa_pairs, procedure_variations, expanded_categories, test_datasets = expander.expand_content()
        
        # Print summary
        logger.info("\nContent Expansion Summary:")
        logger.info("Synthetic Q&A pairs generated: {len(synthetic_qa_pairs)}")
        logger.info("Procedure variations created: {len(procedure_variations)}")
        logger.info("Complaint categories expanded: {len(expanded_categories)}")
        
        logger.info("\nTest datasets created:")
        for difficulty, cases in test_datasets.items():
            logger.info("  {difficulty}: {len(cases)} test cases")
        
        return synthetic_qa_pairs, procedure_variations, expanded_categories, test_datasets
        
    except Exception as e:
        logger.error(f"Error expanding content: {e}")
        raise

if __name__ == "__main__":
    main() 