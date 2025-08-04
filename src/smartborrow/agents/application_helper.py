"""
Application Helper Agent for SmartBorrow

ApplicationHelper using Applications_Guide processed data:
- Use procedure variations from synthetic_expander
- Step-by-step guidance with structured knowledge
- Application process assistance
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

class ApplicationGuideTool(BaseTool):
    """Tool for accessing application guide data"""
    
    name: str = "application_guide"
    description: str = "Access application guide information including step-by-step procedures, requirements, deadlines, and application processes"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, guide_type: str = "overview") -> str:
        """Get application guide information"""
        try:
            import json
            from pathlib import Path
            
            # Load procedure variations
            procedures_file = Path(self.processed_data_path) / "procedure_variations.json"
            if procedures_file.exists():
                with open(procedures_file, 'r') as f:
                    procedures_data = json.load(f)
                
                # Filter for application-related procedures
                application_procedures = [
                    proc for proc in procedures_data 
                    if 'application' in proc.get('category', '').lower() or
                       'apply' in proc.get('original', '').lower() or
                       'process' in proc.get('original', '').lower()
                ]
            else:
                application_procedures = []
            
            # Load structured knowledge
            knowledge_file = Path(self.processed_data_path) / "structured_knowledge.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r') as f:
                    knowledge_data = json.load(f)
                
                # Get application-related knowledge
                application_knowledge = {}
                for concept, data in knowledge_data.items():
                    if 'application' in concept.lower() or 'process' in concept.lower():
                        application_knowledge[concept] = data
            else:
                application_knowledge = {}
            
            if guide_type == "overview":
                result = f"Application Guide Overview:\n"
                result += f"- {len(application_procedures)} procedure variations\n"
                result += f"- {len(application_knowledge)} application concepts\n"
                
                if application_procedures:
                    result += f"\nKey procedure variations:\n"
                    for proc in application_procedures[:3]:
                        result += f"- {proc['type']}: {proc['original'][:80]}...\n"
                
                if application_knowledge:
                    result += f"\nApplication concepts:\n"
                    for concept in list(application_knowledge.keys())[:3]:
                        result += f"- {concept}\n"
                
                return result
            
            elif guide_type == "steps":
                if application_procedures:
                    result = "Application Process Steps:\n"
                    for i, proc in enumerate(application_procedures[:5], 1):
                        result += f"{i}. {proc['original']}\n"
                        if proc.get('variation'):
                            result += f"   Variation: {proc['variation']}\n"
                        result += "\n"
                    return result
                else:
                    return "No application steps found"
            
            elif guide_type == "requirements":
                if application_knowledge:
                    result = "Application Requirements:\n"
                    for concept, data in application_knowledge.items():
                        if data.get('requirements'):
                            result += f"\n{concept} Requirements:\n"
                            for req in data['requirements'][:3]:
                                result += f"- {req}\n"
                    return result
                else:
                    return "No application requirements found"
            
            elif guide_type == "deadlines":
                # Look for deadline-related numerical data
                numerical_file = Path(self.processed_data_path) / "numerical_data.json"
                if numerical_file.exists():
                    with open(numerical_file, 'r') as f:
                        numerical_data = json.load(f)
                    
                    deadline_data = [
                        item for item in numerical_data 
                        if 'deadline' in item.get('context', '').lower() or
                           'date' in item.get('context', '').lower() or
                           'due' in item.get('context', '').lower()
                    ]
                    
                    if deadline_data:
                        result = "Application Deadlines:\n"
                        for item in deadline_data:
                            result += f"- {item['value']} ({item['unit']}): {item['context']}\n"
                        return result
                
                return "No deadline information found"
            
            else:
                return f"Unknown guide type: {guide_type}. Available types: overview, steps, requirements, deadlines"
                
        except Exception as e:
            logger.error(f"Error accessing application guide: {e}")
            return f"Error accessing application guide: {e}"

class StepByStepGuideTool(BaseTool):
    """Tool for providing step-by-step application guidance"""
    
    name: str = "step_by_step_guide"
    description: str = "Provide step-by-step guidance for financial aid applications, FAFSA completion, and verification processes"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, application_type: str = "fafsa") -> str:
        """Get step-by-step guide for application type"""
        try:
            if application_type == "fafsa":
                return """FAFSA Application Step-by-Step Guide:

Step 1: Gather Required Documents
- Social Security Number
- Driver's license (if applicable)
- Tax returns and W-2 forms
- Bank statements and investment records
- Records of untaxed income

Step 2: Create FSA ID
- Go to fsaid.ed.gov
- Create username and password
- Complete identity verification

Step 3: Complete FAFSA Form
- Visit fafsa.gov
- Log in with FSA ID
- Fill out all required sections
- Include all schools you're considering

Step 4: Submit and Review
- Submit FAFSA application
- Review Student Aid Report (SAR)
- Make corrections if needed

Step 5: Follow Up
- Respond to any verification requests
- Complete additional forms if required
- Contact schools for additional aid"""
            
            elif application_type == "verification":
                return """Verification Process Step-by-Step Guide:

Step 1: Receive Verification Request
- Check your Student Aid Report (SAR)
- Review school's verification requirements
- Note deadline for submission

Step 2: Gather Required Documents
- Tax return transcripts
- W-2 forms
- Verification worksheet
- Additional documentation as requested

Step 3: Submit Documents
- Send to school's financial aid office
- Keep copies of all documents
- Use certified mail if required

Step 4: Follow Up
- Confirm receipt of documents
- Respond to additional requests
- Check status regularly

Step 5: Receive Final Award
- Review financial aid package
- Accept or decline offers
- Complete entrance counseling if required"""
            
            elif application_type == "appeal":
                return """Financial Aid Appeal Step-by-Step Guide:

Step 1: Understand Appeal Process
- Review school's appeal policy
- Identify valid reasons for appeal
- Gather supporting documentation

Step 2: Prepare Appeal Letter
- Explain your circumstances clearly
- Provide specific details
- Include supporting documents
- Be professional and respectful

Step 3: Submit Appeal
- Follow school's submission process
- Meet all deadlines
- Keep copies of everything

Step 4: Follow Up
- Check status regularly
- Respond to additional requests
- Be patient with the process

Step 5: Review Decision
- Understand the outcome
- Ask questions if needed
- Plan next steps accordingly"""
            
            else:
                return f"Unknown application type: {application_type}. Available types: fafsa, verification, appeal"
                
        except Exception as e:
            logger.error(f"Error accessing step-by-step guide: {e}")
            return f"Error accessing step-by-step guide: {e}"

class ApplicationHelper(BaseAgent):
    """Application Helper Agent for application process questions"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None,
                 rag_service = None) -> None:
        
        super().__init__(model_name, temperature, rag_service)
        
        # Add application-specific tools
        self.application_tools = [
            ApplicationGuideTool(),
            StepByStepGuideTool()
        ]
        
        # Combine all tools
        self.tools.extend(self.application_tools)
        
        # Recreate agent with new tools
        self.agent = self._create_application_agent()
        self.workflow = self._create_workflow()
    
    def _create_application_agent(self) -> None:
        """Create the application helper agent with specialized tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Application Helper for SmartBorrow, an expert in financial aid application processes.

You have specialized knowledge about:
- FAFSA application process
- Verification procedures
- Application deadlines and requirements
- Step-by-step guidance
- Common application issues

You have access to:
1. RAG system with processed financial aid data
2. Application guide data and procedure variations
3. Structured knowledge about application processes
4. Step-by-step guides for different application types
5. Deadline and requirement information

Use the available tools to provide clear, step-by-step guidance for application processes. Always provide specific deadlines and requirements when available.

Available tools:
- rag_query: Query the RAG system for general information
- numerical_data: Access processed numerical data points
- structured_knowledge: Access structured knowledge about concepts
- application_guide: Access application guide information
- step_by_step_guide: Provide step-by-step application guidance

Current question: {question}"""),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        return create_openai_functions_agent(self.llm, self.tools, prompt)
    
    def get_application_specific_info(self, question: str) -> Dict[str, Any]:
        """Get application-specific information for a question"""
        try:
            # Check if question is application-related
            application_keywords = ['application', 'apply', 'fafsa', 'verification', 'process', 'step', 'deadline', 'requirement']
            is_application_related = any(keyword in question.lower() for keyword in application_keywords)
            
            if not is_application_related:
                return {"is_application_related": False, "message": "Question not related to application processes"}
            
            # Get application-specific data
            application_guide_tool = ApplicationGuideTool()
            guide_data = application_guide_tool._run("overview")
            
            # Get step-by-step info if relevant
            step_keywords = ['step', 'process', 'how to', 'guide']
            step_info = ""
            if any(keyword in question.lower() for keyword in step_keywords):
                step_tool = StepByStepGuideTool()
                if 'fafsa' in question.lower():
                    step_info = step_tool._run("fafsa")
                elif 'verification' in question.lower():
                    step_info = step_tool._run("verification")
                elif 'appeal' in question.lower():
                    step_info = step_tool._run("appeal")
                else:
                    step_info = step_tool._run("fafsa")  # Default to FAFSA
            
            return {
                "is_application_related": True,
                "guide_data": guide_data,
                "step_info": step_info,
                "specialized_tools": [tool.name for tool in self.application_tools]
            }
            
        except Exception as e:
            logger.error(f"Error getting application-specific info: {e}")
            return {"is_application_related": False, "error": str(e)}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the application helper agent"""
        base_info = super().get_agent_info()
        base_info.update({
            "agent_type": "Application Helper",
            "specialized_tools": [tool.name for tool in self.application_tools],
            "focus_area": "Application Processes",
            "capabilities": [
                "FAFSA application guidance",
                "Verification process assistance",
                "Deadline information",
                "Step-by-step instructions",
                "Application requirement guidance"
            ]
        })
        return base_info

def main() -> None:
    """Test the application helper agent"""
    agent = ApplicationHelper()
    
    # Test application-specific questions
    test_questions = [
        "How do I complete the FAFSA application?",
        "What is the verification process?",
        "What are the deadlines for financial aid applications?",
        "What documents do I need for FAFSA?",
        "How do I appeal a financial aid decision?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*80}")
        logger.info("Question: {question}")
        logger.info("{'='*80}")
        
        # Get application-specific info
        app_info = agent.get_application_specific_info(question)
        if app_info.get("is_application_related"):
            logger.info("Application-related question detected")
            logger.info("Available guide data: {len(app_info.get('guide_data', ''))} characters")
        
        # Run the agent
        result = agent.run(question)
        
        logger.info("Response: {result['response']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Sources: {len(result.get('sources', []))}")

if __name__ == "__main__":
    main() 