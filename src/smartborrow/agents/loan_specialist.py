"""
Loan Specialist Agent for SmartBorrow

LoanSpecialist using Direct_Loan processed data:
- Access loan-specific numerical data points
- Use loan-related Q&A pairs for better responses
- Specialized knowledge for Direct Loan questions
"""

import os
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain.agents import create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv

from .base_agent import BaseAgent, AgentState, RAGQueryTool, NumericalDataTool, StructuredKnowledgeTool

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DirectLoanDataTool(BaseTool):
    """Tool for accessing Direct Loan specific data"""
    
    name: str = "direct_loan_data"
    description: str = "Access Direct Loan specific information including interest rates, loan limits, repayment terms, and eligibility requirements"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, data_type: str = "overview") -> str:
        """Get Direct Loan specific data"""
        try:
            import json
            from pathlib import Path
            
            # Load numerical data
            numerical_file = Path(self.processed_data_path) / "numerical_data.json"
            if numerical_file.exists():
                with open(numerical_file, 'r') as f:
                    numerical_data = json.load(f)
                
                # Filter for Direct Loan related data
                direct_loan_data = [
                    item for item in numerical_data 
                    if 'direct' in item.get('context', '').lower() or 
                       'loan' in item.get('context', '').lower() or
                       item.get('category') == 'direct_loans'
                ]
            else:
                direct_loan_data = []
            
            # Load Q&A pairs
            qa_file = Path(self.processed_data_path) / "synthetic_qa_pairs.json"
            if qa_file.exists():
                with open(qa_file, 'r') as f:
                    qa_data = json.load(f)
                
                # Filter for Direct Loan Q&A pairs
                direct_loan_qa = [
                    qa for qa in qa_data 
                    if qa.get('category') == 'direct_loans' or
                       'direct' in qa.get('question', '').lower() or
                       'loan' in qa.get('question', '').lower()
                ]
            else:
                direct_loan_qa = []
            
            if data_type == "overview":
                result = f"Direct Loan Data Overview:\n"
                result += f"- {len(direct_loan_data)} numerical data points\n"
                result += f"- {len(direct_loan_qa)} Q&A pairs\n"
                
                if direct_loan_data:
                    result += f"\nKey numerical data:\n"
                    for item in direct_loan_data[:5]:
                        result += f"- {item['value']} ({item['unit']}): {item['context'][:80]}...\n"
                
                if direct_loan_qa:
                    result += f"\nSample Q&A pairs:\n"
                    for qa in direct_loan_qa[:3]:
                        result += f"Q: {qa['question']}\n"
                        result += f"A: {qa['answer'][:100]}...\n\n"
                
                return result
            
            elif data_type == "interest_rates":
                rate_data = [item for item in direct_loan_data if 'rate' in item.get('context', '').lower()]
                if rate_data:
                    result = "Direct Loan Interest Rates:\n"
                    for item in rate_data:
                        result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                    return result
                else:
                    return "No interest rate data found for Direct Loans"
            
            elif data_type == "loan_limits":
                limit_data = [item for item in direct_loan_data if 'limit' in item.get('context', '').lower()]
                if limit_data:
                    result = "Direct Loan Limits:\n"
                    for item in limit_data:
                        result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                    return result
                else:
                    return "No loan limit data found for Direct Loans"
            
            elif data_type == "eligibility":
                # Get eligibility Q&A pairs
                eligibility_qa = [qa for qa in direct_loan_qa if 'eligibility' in qa.get('question', '').lower()]
                if eligibility_qa:
                    result = "Direct Loan Eligibility Information:\n"
                    for qa in eligibility_qa[:3]:
                        result += f"Q: {qa['question']}\n"
                        result += f"A: {qa['answer']}\n\n"
                    return result
                else:
                    return "No eligibility information found for Direct Loans"
            
            else:
                return f"Unknown data type: {data_type}. Available types: overview, interest_rates, loan_limits, eligibility"
                
        except Exception as e:
            logger.error(f"Error accessing Direct Loan data: {e}")
            return f"Error accessing Direct Loan data: {e}"

class LoanRepaymentTool(BaseTool):
    """Tool for loan repayment calculations and information"""
    
    name: str = "loan_repayment"
    description: str = "Calculate loan repayment amounts, get repayment plan information, and access Direct Loan repayment data"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, calculation_type: str = "info") -> str:
        """Get loan repayment information"""
        try:
            import json
            from pathlib import Path
            
            # Load numerical data for repayment info
            numerical_file = Path(self.processed_data_path) / "numerical_data.json"
            if numerical_file.exists():
                with open(numerical_file, 'r') as f:
                    data = json.load(f)
                
                # Filter for repayment related data
                repayment_data = [
                    item for item in data 
                    if 'repayment' in item.get('context', '').lower() or
                       'payment' in item.get('context', '').lower() or
                       'monthly' in item.get('context', '').lower()
                ]
            else:
                repayment_data = []
            
            if calculation_type == "info":
                if repayment_data:
                    result = "Direct Loan Repayment Information:\n"
                    for item in repayment_data[:5]:
                        result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                    return result
                else:
                    return "No repayment information found"
            
            elif calculation_type == "plans":
                return """Direct Loan Repayment Plans:
1. Standard Repayment Plan: Fixed monthly payments over 10 years
2. Graduated Repayment Plan: Payments start low and increase every 2 years
3. Extended Repayment Plan: Extended payment period up to 25 years
4. Income-Driven Repayment Plans:
   - Income-Based Repayment (IBR)
   - Pay As You Earn (PAYE)
   - Revised Pay As You Earn (REPAYE)
   - Income-Contingent Repayment (ICR)"""
            
            else:
                return f"Unknown calculation type: {calculation_type}. Available types: info, plans"
                
        except Exception as e:
            logger.error(f"Error accessing loan repayment data: {e}")
            return f"Error accessing loan repayment data: {e}"

class LoanSpecialist(BaseAgent):
    """Loan Specialist Agent for Direct Loan questions"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None,
                 rag_service = None) -> None:
        
        super().__init__(model_name, temperature, rag_service)
        
        # Add loan-specific tools
        self.loan_tools = [
            DirectLoanDataTool(),
            LoanRepaymentTool()
        ]
        
        # Combine all tools
        self.tools.extend(self.loan_tools)
        
        # Recreate agent with new tools
        self.agent = self._create_loan_agent()
        self.workflow = self._create_workflow()
    
    def _create_loan_agent(self) -> None:
        """Create the loan specialist agent with specialized tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Direct Loan Specialist for SmartBorrow, an expert in federal student loans.

You have specialized knowledge about:
- Direct Loan interest rates and limits
- Loan eligibility requirements
- Repayment plans and calculations
- Loan application processes

You have access to:
1. RAG system with processed financial aid data
2. Direct Loan specific numerical data (rates, limits, amounts)
3. Structured knowledge about loan concepts
4. Direct Loan specific Q&A pairs
5. Repayment plan information

Use the available tools to provide accurate, comprehensive answers about Direct Loans. Always provide specific numerical data when available and explain repayment options clearly.

Available tools:
- rag_query: Query the RAG system for general information
- numerical_data: Access processed numerical data points
- structured_knowledge: Access structured knowledge about concepts
- direct_loan_data: Access Direct Loan specific information
- loan_repayment: Get repayment plan information and calculations

Current question: {question}"""),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        return create_openai_functions_agent(self.llm, self.tools, prompt)
    
    def get_loan_specific_info(self, question: str) -> Dict[str, Any]:
        """Get loan-specific information for a question"""
        try:
            # Check if question is loan-related
            loan_keywords = ['loan', 'direct', 'interest', 'rate', 'repayment', 'payment', 'borrow']
            is_loan_related = any(keyword in question.lower() for keyword in loan_keywords)
            
            if not is_loan_related:
                return {"is_loan_related": False, "message": "Question not related to Direct Loans"}
            
            # Get loan-specific data
            direct_loan_tool = DirectLoanDataTool()
            loan_data = direct_loan_tool._run("overview")
            
            # Get repayment info if relevant
            repayment_keywords = ['repayment', 'payment', 'monthly', 'plan']
            repayment_info = ""
            if any(keyword in question.lower() for keyword in repayment_keywords):
                repayment_tool = LoanRepaymentTool()
                repayment_info = repayment_tool._run("plans")
            
            return {
                "is_loan_related": True,
                "loan_data": loan_data,
                "repayment_info": repayment_info,
                "specialized_tools": [tool.name for tool in self.loan_tools]
            }
            
        except Exception as e:
            logger.error(f"Error getting loan-specific info: {e}")
            return {"is_loan_related": False, "error": str(e)}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the loan specialist agent"""
        base_info = super().get_agent_info()
        base_info.update({
            "agent_type": "Loan Specialist",
            "specialized_tools": [tool.name for tool in self.loan_tools],
            "focus_area": "Direct Loans",
            "capabilities": [
                "Interest rate information",
                "Loan limit calculations",
                "Eligibility requirements",
                "Repayment plan guidance",
                "Loan application assistance"
            ]
        })
        return base_info

def main() -> None:
    """Test the loan specialist agent"""
    agent = LoanSpecialist()
    
    # Test loan-specific questions
    test_questions = [
        "What are the current interest rates for Direct Loans?",
        "What are the loan limits for undergraduate students?",
        "How do I apply for a Direct Loan?",
        "What repayment plans are available for Direct Loans?",
        "What is the maximum I can borrow in Direct Loans?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*80}")
        logger.info("Question: {question}")
        logger.info("{'='*80}")
        
        # Get loan-specific info
        loan_info = agent.get_loan_specific_info(question)
        if loan_info.get("is_loan_related"):
            logger.info("Loan-related question detected")
            logger.info("Available loan data: {len(loan_info.get('loan_data', ''))} characters")
        
        # Run the agent
        result = agent.run(question)
        
        logger.info("Response: {result['response']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Sources: {len(result.get('sources', []))}")

if __name__ == "__main__":
    main() 