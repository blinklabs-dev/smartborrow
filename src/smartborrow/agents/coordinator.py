"""
Coordinator Agent for SmartBorrow Multi-Agent System

CoordinatorAgent with LangGraph workflow:
- Route questions using processed complaint categories
- Combine responses from specialized agents
- Orchestrate multi-agent interactions
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain.agents import create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv

from .base_agent import BaseAgent, AgentState
from .loan_specialist import LoanSpecialist
from .grant_specialist import GrantSpecialist
from .application_helper import ApplicationHelper

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class CoordinatorState:
    """State for coordinator workflow"""
    messages: List[BaseMessage]
    question: str
    agent_responses: Dict[str, Any]
    selected_agents: List[str]
    final_response: Optional[str] = None
    confidence: Optional[str] = None
    routing_info: Optional[Dict[str, Any]] = None

class QuestionRouterTool(BaseTool):
    """Tool for routing questions to appropriate agents"""
    
    name: str = "question_router"
    description: str = "Route questions to appropriate specialized agents based on content and complaint categories"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, question: str) -> str:
        """Route question to appropriate agents"""
        try:
            import json
            from pathlib import Path
            
            # Load complaint categories for routing
            categories_file = Path(self.processed_data_path) / "complaint_categories.json"
            if categories_file.exists():
                with open(categories_file, 'r') as f:
                    categories_data = json.load(f)
            else:
                categories_data = {}
            
            # Define routing keywords
            routing_keywords = {
                'loan_specialist': [
                    'loan', 'direct loan', 'interest rate', 'repayment', 'borrow',
                    'subsidized', 'unsubsidized', 'plus loan', 'consolidation'
                ],
                'grant_specialist': [
                    'grant', 'pell grant', 'eligibility', 'efc', 'expected family contribution',
                    'financial need', 'award', 'free money'
                ],
                'application_helper': [
                    'application', 'apply', 'fafsa', 'verification', 'process',
                    'deadline', 'requirement', 'document', 'step'
                ]
            }
            
            # Analyze question for routing
            question_lower = question.lower()
            selected_agents = []
            
            for agent_type, keywords in routing_keywords.items():
                if any(keyword in question_lower for keyword in keywords):
                    selected_agents.append(agent_type)
            
            # If no specific agent matches, use base agent
            if not selected_agents:
                selected_agents = ['base_agent']
            
            # Get complaint category info if relevant
            complaint_info = ""
            for category, data in categories_data.items():
                if any(keyword in question_lower for keyword in data.get('common_keywords', [])):
                    complaint_info = f"Question relates to {category} complaints ({data.get('percentage', 0):.1f}% of complaints)"
                    break
            
            result = f"Question Routing Analysis:\n"
            result += f"Selected agents: {', '.join(selected_agents)}\n"
            if complaint_info:
                result += f"Complaint context: {complaint_info}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error routing question: {e}")
            return f"Error routing question: {e}"

class ResponseCombinerTool(BaseTool):
    """Tool for combining responses from multiple agents"""
    
    name: str = "response_combiner"
    description: str = "Combine and synthesize responses from multiple specialized agents"
    
    def _run(self, agent_responses: str) -> str:
        """Combine agent responses"""
        try:
            # Parse agent responses (simplified for now)
            # In a real implementation, this would parse structured responses
            
            result = "Combined Response Analysis:\n"
            result += "Multiple agent responses detected. Synthesizing information...\n"
            result += "Consider the following specialized perspectives:\n"
            
            # This is a simplified version - in practice, you'd parse the actual responses
            if 'loan_specialist' in agent_responses:
                result += "- Loan Specialist: Direct loan information and repayment details\n"
            if 'grant_specialist' in agent_responses:
                result += "- Grant Specialist: Pell Grant eligibility and amounts\n"
            if 'application_helper' in agent_responses:
                result += "- Application Helper: Process guidance and requirements\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error combining responses: {e}")
            return f"Error combining responses: {e}"

class CoordinatorAgent:
    """Coordinator Agent that orchestrates specialized agents"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None) -> None:
        
        # Initialize LLM
        self.model_name = model_name or os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = temperature or float(os.getenv("AGENT_TEMPERATURE", "0.1"))
        
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize RAG service for agents
        from ..rag.rag_service import RAGService
        rag_service = RAGService()
        rag_service.initialize()
        
        # Initialize specialized agents with RAG service
        self.agents = {
            'base_agent': BaseAgent(model_name, temperature, rag_service),
            'loan_specialist': LoanSpecialist(model_name, temperature, rag_service),
            'grant_specialist': GrantSpecialist(model_name, temperature, rag_service),
            'application_helper': ApplicationHelper(model_name, temperature, rag_service)
        }
        
        # Initialize tools
        self.tools = [
            QuestionRouterTool(),
            ResponseCombinerTool()
        ]
        
        # Create workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> None:
        """Create the LangGraph workflow for coordination"""
        
        def route_question(state: CoordinatorState) -> CoordinatorState:
            """Route the question to appropriate agents"""
            try:
                # Use question router tool
                router_tool = QuestionRouterTool()
                routing_info = router_tool._run(state.question)
                
                # Determine which agents to use
                question_lower = state.question.lower()
                selected_agents = []
                
                if any(keyword in question_lower for keyword in ['loan', 'direct', 'interest', 'repayment']):
                    selected_agents.append('loan_specialist')
                
                if any(keyword in question_lower for keyword in ['grant', 'pell', 'eligibility', 'efc']):
                    selected_agents.append('grant_specialist')
                
                if any(keyword in question_lower for keyword in ['application', 'apply', 'fafsa', 'process']):
                    selected_agents.append('application_helper')
                
                # If no specific agent, use base agent
                if not selected_agents:
                    selected_agents = ['base_agent']
                
                state.selected_agents = selected_agents
                state.routing_info = {"routing_analysis": routing_info}
                
                return state
                
            except Exception as e:
                logger.error(f"Error in route_question: {e}")
                state.selected_agents = ['base_agent']
                return state
        
        def get_agent_responses(state: CoordinatorState) -> CoordinatorState:
            """Get responses from selected agents"""
            try:
                agent_responses = {}
                
                for agent_name in state.selected_agents:
                    if agent_name in self.agents:
                        agent = self.agents[agent_name]
                        response = agent.run(state.question)
                        agent_responses[agent_name] = response
                
                state.agent_responses = agent_responses
                return state
                
            except Exception as e:
                logger.error(f"Error in get_agent_responses: {e}")
                return state
        
        def combine_responses(state: CoordinatorState) -> CoordinatorState:
            """Combine responses from multiple agents"""
            try:
                if len(state.agent_responses) == 1:
                    # Single agent response
                    agent_name = list(state.agent_responses.keys())[0]
                    response = state.agent_responses[agent_name]
                    state.final_response = response.get('response', 'No response available')
                    state.confidence = response.get('confidence', 'unknown')
                else:
                    # Multiple agent responses - synthesize
                    responses = []
                    for agent_name, response in state.agent_responses.items():
                        responses.append(f"[{agent_name.upper()}]: {response.get('response', 'No response')}")
                    
                    # Create synthesis prompt
                    synthesis_prompt = f"""Synthesize the following responses from specialized agents:

Question: {state.question}

Agent Responses:
{chr(10).join(responses)}

Provide a comprehensive, well-structured answer that combines the specialized knowledge from all relevant agents. Be specific and accurate."""

                    # Get synthesis from LLM
                    synthesis_response = self.llm.invoke(synthesis_prompt)
                    state.final_response = synthesis_response.content
                    state.confidence = "high"  # Multiple agents consulted
                
                return state
                
            except Exception as e:
                logger.error(f"Error in combine_responses: {e}")
                state.final_response = "Error combining agent responses"
                return state
        

        
        # Create the workflow
        workflow = StateGraph(CoordinatorState)
        
        # Add nodes
        workflow.add_node("route", route_question)
        workflow.add_node("get_responses", get_agent_responses)
        workflow.add_node("combine", combine_responses)
        
        # Add edges
        workflow.add_edge("route", "get_responses")
        workflow.add_edge("get_responses", "combine")
        workflow.add_edge("combine", END)
        
        # Set entry point
        workflow.set_entry_point("route")
        
        return workflow.compile()
    
    def run(self, question: str) -> Dict[str, Any]:
        """Run the coordinator with a question"""
        try:
            # Initialize state
            state = CoordinatorState(
                messages=[HumanMessage(content=question)],
                question=question,
                agent_responses={},
                selected_agents=[],
                final_response=None,
                confidence=None,
                routing_info=None
            )
            
            # Run workflow
            result = self.workflow.invoke(state)
            # Handle both CoordinatorState and dict
            if isinstance(result, dict):
                answer = result.get("final_response") or result.get("response") or result.get("output") or str(result)
                confidence = result.get("confidence", "unknown")
                selected_agents = result.get("selected_agents", [])
                routing_info = result.get("routing_info", {})
                agent_responses = result.get("agent_responses", {})
            else:
                answer = getattr(result, "final_response", getattr(result, "response", str(result)))
                confidence = getattr(result, "confidence", "unknown")
                selected_agents = getattr(result, "selected_agents", [])
                routing_info = getattr(result, "routing_info", {})
                agent_responses = getattr(result, "agent_responses", {})
            
            return {
                "question": question,
                "response": answer,
                "confidence": confidence,
                "selected_agents": selected_agents,
                "routing_info": routing_info,
                "agent_responses": agent_responses
            }
            
        except Exception as e:
            logger.error(f"Error running coordinator: {e}")
            return {
                "question": question,
                "response": f"Error processing question: {e}",
                "confidence": "error",
                "selected_agents": [],
                "routing_info": {},
                "agent_responses": {}
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the coordinator and all agents"""
        info = {
            "coordinator_type": "Multi-Agent Coordinator",
            "model_name": self.model_name,
            "temperature": self.temperature,
            "available_agents": list(self.agents.keys()),
            "agent_details": {}
        }
        
        for agent_name, agent in self.agents.items():
            try:
                agent_info = agent.get_agent_info()
                info["agent_details"][agent_name] = agent_info
            except Exception as e:
                logger.error(f"Error getting info for {agent_name}: {e}")
                info["agent_details"][agent_name] = {"error": str(e)}
        
        return info
    
    def test_all_agents(self, question: str) -> Dict[str, Any]:
        """Test all agents with the same question"""
        results = {}
        
        for agent_name, agent in self.agents.items():
            try:
                result = agent.run(question)
                results[agent_name] = result
            except Exception as e:
                logger.error(f"Error testing {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}
        
        return results

def main() -> None:
    """Test the coordinator agent"""
    coordinator = CoordinatorAgent()
    
    # Test questions that should route to different agents
    test_questions = [
        "What are the current interest rates for Direct Loans?",
        "What is the maximum Pell Grant amount?",
        "How do I complete the FAFSA application?",
        "What are the loan limits and grant eligibility requirements?",
        "What are the most common student loan complaints?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*100}")
        logger.info("Question: {question}")
        logger.info("{'='*100}")
        
        # Run coordinator
        result = coordinator.run(question)
        
        logger.info("Selected agents: {result['selected_agents']}")
        logger.info("Response: {result['response']}")
        logger.info("Confidence: {result['confidence']}")
        
        if result.get('routing_info'):
            logger.info("Routing info: {result['routing_info']}")

if __name__ == "__main__":
    main() 