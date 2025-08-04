"""
Grant Specialist Agent for SmartBorrow

GrantSpecialist using Pell_Grant processed data:
- Handle eligibility calculations with extracted numerical data
- Use grant-specific FAQ from processed complaints
- Specialized knowledge for Pell Grant questions
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

class PellGrantDataTool(BaseTool):
    """Tool for accessing Pell Grant specific data"""
    
    name: str = "pell_grant_data"
    description: str = "Access Pell Grant specific information including amounts, eligibility requirements, EFC calculations, and grant-specific data"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, data_type: str = "overview") -> str:
        """Get Pell Grant specific data"""
        try:
            import json
            from pathlib import Path
            
            # Load numerical data
            numerical_file = Path(self.processed_data_path) / "numerical_data.json"
            if numerical_file.exists():
                with open(numerical_file, 'r') as f:
                    numerical_data = json.load(f)
                
                # Filter for Pell Grant related data
                pell_grant_data = [
                    item for item in numerical_data 
                    if 'pell' in item.get('context', '').lower() or 
                       'grant' in item.get('context', '').lower() or
                       item.get('category') == 'pell_grant'
                ]
            else:
                pell_grant_data = []
            
            # Load Q&A pairs
            qa_file = Path(self.processed_data_path) / "synthetic_qa_pairs.json"
            if qa_file.exists():
                with open(qa_file, 'r') as f:
                    qa_data = json.load(f)
                
                # Filter for Pell Grant Q&A pairs
                pell_grant_qa = [
                    qa for qa in qa_data 
                    if qa.get('category') == 'pell_grant' or
                       'pell' in qa.get('question', '').lower() or
                       'grant' in qa.get('question', '').lower()
                ]
            else:
                pell_grant_qa = []
            
            # Load complaint FAQs
            faq_file = Path(self.processed_data_path) / "complaint_faqs.json"
            if faq_file.exists():
                with open(faq_file, 'r') as f:
                    faq_data = json.load(f)
                
                # Filter for grant-related complaints
                grant_faqs = [
                    faq for faq in faq_data 
                    if 'grant' in faq.get('category', '').lower() or
                       'pell' in faq.get('question', '').lower()
                ]
            else:
                grant_faqs = []
            
            if data_type == "overview":
                result = f"Pell Grant Data Overview:\n"
                result += f"- {len(pell_grant_data)} numerical data points\n"
                result += f"- {len(pell_grant_qa)} Q&A pairs\n"
                result += f"- {len(grant_faqs)} grant-related FAQs\n"
                
                if pell_grant_data:
                    result += f"\nKey numerical data:\n"
                    for item in pell_grant_data[:5]:
                        result += f"- {item['value']} ({item['unit']}): {item['context'][:80]}...\n"
                
                if pell_grant_qa:
                    result += f"\nSample Q&A pairs:\n"
                    for qa in pell_grant_qa[:3]:
                        result += f"Q: {qa['question']}\n"
                        result += f"A: {qa['answer'][:100]}...\n\n"
                
                return result
            
            elif data_type == "amounts":
                amount_data = [item for item in pell_grant_data if 'amount' in item.get('context', '').lower() or 'maximum' in item.get('context', '').lower()]
                if amount_data:
                    result = "Pell Grant Amounts:\n"
                    for item in amount_data:
                        result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                    return result
                else:
                    return "No amount data found for Pell Grants"
            
            elif data_type == "eligibility":
                # Get eligibility Q&A pairs
                eligibility_qa = [qa for qa in pell_grant_qa if 'eligibility' in qa.get('question', '').lower() or 'qualify' in qa.get('question', '').lower()]
                if eligibility_qa:
                    result = "Pell Grant Eligibility Information:\n"
                    for qa in eligibility_qa[:3]:
                        result += f"Q: {qa['question']}\n"
                        result += f"A: {qa['answer']}\n\n"
                    return result
                else:
                    return "No eligibility information found for Pell Grants"
            
            elif data_type == "efc":
                efc_data = [item for item in pell_grant_data if 'efc' in item.get('context', '').lower() or 'expected family contribution' in item.get('context', '').lower()]
                if efc_data:
                    result = "Expected Family Contribution (EFC) Information:\n"
                    for item in efc_data:
                        result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                    return result
                else:
                    return "No EFC data found for Pell Grants"
            
            else:
                return f"Unknown data type: {data_type}. Available types: overview, amounts, eligibility, efc"
                
        except Exception as e:
            logger.error(f"Error accessing Pell Grant data: {e}")
            return f"Error accessing Pell Grant data: {e}"

class EligibilityCalculatorTool(BaseTool):
    """Tool for eligibility calculations and EFC estimates"""
    
    name: str = "eligibility_calculator"
    description: str = "Calculate Pell Grant eligibility, estimate EFC, and provide eligibility guidance based on processed data"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, calculation_type: str = "info") -> str:
        """Get eligibility calculation information"""
        try:
            import json
            from pathlib import Path
            
            # Load structured knowledge for eligibility info
            knowledge_file = Path(self.processed_data_path) / "structured_knowledge.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r') as f:
                    knowledge_data = json.load(f)
                
                # Get Pell Grant knowledge
                pell_knowledge = knowledge_data.get('pell_grant', {})
            else:
                pell_knowledge = {}
            
            if calculation_type == "info":
                if pell_knowledge:
                    result = "Pell Grant Eligibility Information:\n"
                    
                    if pell_knowledge.get('definition'):
                        result += f"Definition: {pell_knowledge['definition']}\n\n"
                    
                    if pell_knowledge.get('requirements'):
                        result += f"Requirements:\n"
                        for req in pell_knowledge['requirements'][:5]:
                            result += f"- {req}\n"
                        result += "\n"
                    
                    if pell_knowledge.get('procedures'):
                        result += f"Application Procedures:\n"
                        for proc in pell_knowledge['procedures'][:3]:
                            result += f"- {proc}\n"
                    
                    return result
                else:
                    return "No eligibility information found"
            
            elif calculation_type == "efc_guide":
                return """Expected Family Contribution (EFC) Calculation Guide:

The EFC is calculated using the Federal Methodology (FM) formula and considers:
1. Parent's income and assets
2. Student's income and assets
3. Family size
4. Number of family members in college

Key Factors:
- Lower EFC = Higher Pell Grant eligibility
- EFC of 0 = Maximum Pell Grant
- EFC above threshold = No Pell Grant eligibility

To estimate your EFC:
1. Complete the FAFSA application
2. Use the FAFSA4caster tool
3. Consult with your school's financial aid office"""
            
            elif calculation_type == "thresholds":
                return """Pell Grant Eligibility Thresholds:

- EFC of 0: Maximum Pell Grant amount
- EFC of 1-5,846: Partial Pell Grant (amount decreases as EFC increases)
- EFC above 5,846: No Pell Grant eligibility

Additional Requirements:
- Must be enrolled in an eligible program
- Must be working toward first bachelor's degree
- Must meet citizenship requirements
- Must maintain satisfactory academic progress"""
            
            else:
                return f"Unknown calculation type: {calculation_type}. Available types: info, efc_guide, thresholds"
                
        except Exception as e:
            logger.error(f"Error accessing eligibility data: {e}")
            return f"Error accessing eligibility data: {e}"

class GrantSpecialist(BaseAgent):
    """Grant Specialist Agent for Pell Grant questions"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None,
                 rag_service = None) -> None:
        
        super().__init__(model_name, temperature, rag_service)
        
        # Add grant-specific tools
        self.grant_tools = [
            PellGrantDataTool(),
            EligibilityCalculatorTool()
        ]
        
        # Combine all tools
        self.tools.extend(self.grant_tools)
        
        # Recreate agent with new tools
        self.agent = self._create_grant_agent()
        self.workflow = self._create_workflow()
    
    def _create_grant_agent(self) -> None:
        """Create the grant specialist agent with specialized tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Pell Grant Specialist for SmartBorrow, an expert in federal student grants.

You have specialized knowledge about:
- Pell Grant amounts and maximums
- Eligibility requirements and EFC calculations
- Grant application processes
- Grant-specific complaints and issues

You have access to:
1. RAG system with processed financial aid data
2. Pell Grant specific numerical data (amounts, thresholds)
3. Structured knowledge about grant concepts
4. Pell Grant specific Q&A pairs
5. Grant-related complaint FAQs
6. Eligibility calculation tools

Use the available tools to provide accurate, comprehensive answers about Pell Grants. Always provide specific numerical data when available and explain eligibility requirements clearly.

Available tools:
- rag_query: Query the RAG system for general information
- numerical_data: Access processed numerical data points
- structured_knowledge: Access structured knowledge about concepts
- pell_grant_data: Access Pell Grant specific information
- eligibility_calculator: Calculate eligibility and EFC information

Current question: {question}"""),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        return create_openai_functions_agent(self.llm, self.tools, prompt)
    
    def get_grant_specific_info(self, question: str) -> Dict[str, Any]:
        """Get grant-specific information for a question"""
        try:
            # Check if question is grant-related
            grant_keywords = ['grant', 'pell', 'eligibility', 'efc', 'amount', 'maximum']
            is_grant_related = any(keyword in question.lower() for keyword in grant_keywords)
            
            if not is_grant_related:
                return {"is_grant_related": False, "message": "Question not related to Pell Grants"}
            
            # Get grant-specific data
            pell_grant_tool = PellGrantDataTool()
            grant_data = pell_grant_tool._run("overview")
            
            # Get eligibility info if relevant
            eligibility_keywords = ['eligibility', 'qualify', 'efc', 'expected family contribution']
            eligibility_info = ""
            if any(keyword in question.lower() for keyword in eligibility_keywords):
                eligibility_tool = EligibilityCalculatorTool()
                eligibility_info = eligibility_tool._run("thresholds")
            
            return {
                "is_grant_related": True,
                "grant_data": grant_data,
                "eligibility_info": eligibility_info,
                "specialized_tools": [tool.name for tool in self.grant_tools]
            }
            
        except Exception as e:
            logger.error(f"Error getting grant-specific info: {e}")
            return {"is_grant_related": False, "error": str(e)}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the grant specialist agent"""
        base_info = super().get_agent_info()
        base_info.update({
            "agent_type": "Grant Specialist",
            "specialized_tools": [tool.name for tool in self.grant_tools],
            "focus_area": "Pell Grants",
            "capabilities": [
                "Grant amount information",
                "Eligibility calculations",
                "EFC estimation guidance",
                "Application assistance",
                "Grant-specific complaint resolution"
            ]
        })
        return base_info

def main() -> None:
    """Test the grant specialist agent"""
    agent = GrantSpecialist()
    
    # Test grant-specific questions
    test_questions = [
        "What is the maximum Pell Grant amount?",
        "How do I qualify for a Pell Grant?",
        "What is the EFC threshold for Pell Grant eligibility?",
        "How is my Expected Family Contribution calculated?",
        "What are the requirements for Pell Grant eligibility?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*80}")
        logger.info("Question: {question}")
        logger.info("{'='*80}")
        
        # Get grant-specific info
        grant_info = agent.get_grant_specific_info(question)
        if grant_info.get("is_grant_related"):
            logger.info("Grant-related question detected")
            logger.info("Available grant data: {len(grant_info.get('grant_data', ''))} characters")
        
        # Run the agent
        result = agent.run(question)
        
        logger.info("Response: {result['response']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Sources: {len(result.get('sources', []))}")

if __name__ == "__main__":
    main() 