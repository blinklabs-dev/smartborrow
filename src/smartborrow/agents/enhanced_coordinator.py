"""
Enhanced Coordinator Agent for SmartBorrow with Tavily Integration

This enhanced coordinator includes intelligent routing between RAG and web search
to provide the most current and accurate information.
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
from .tavily_web_search import create_tavily_web_search_tool

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class EnhancedCoordinatorState:
    """Enhanced state for coordinator workflow with web search"""
    messages: List[BaseMessage]
    question: str
    agent_responses: Dict[str, Any]
    selected_agents: List[str]
    web_search_results: Optional[str] = None
    rag_results: Optional[str] = None
    final_response: Optional[str] = None
    confidence: Optional[str] = None
    routing_info: Optional[Dict[str, Any]] = None
    search_strategy: Optional[str] = None

class IntelligentRouterTool(BaseTool):
    """Enhanced tool for intelligent routing between RAG and web search"""
    
    name: str = "intelligent_router"
    description: str = "Intelligently route questions to appropriate agents and determine if web search is needed"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, question: str) -> str:
        """Intelligently route question and determine search strategy"""
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
            
            # Define routing keywords with web search indicators
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
            
            # Define web search triggers
            web_search_triggers = [
                'current', 'latest', '2024', '2025', 'this year', 'now',
                'recent', 'updated', 'new', 'deadline', 'deadline',
                'interest rate', 'tuition', 'cost', 'price', 'scholarship',
                'harvard', 'stanford', 'mit', 'berkeley', 'university',
                'compare', 'comparison', 'vs', 'versus'
            ]
            
            # Analyze question for routing
            question_lower = question.lower()
            selected_agents = []
            needs_web_search = False
            search_strategy = "rag_only"
            
            # Check for web search triggers
            if any(trigger in question_lower for trigger in web_search_triggers):
                needs_web_search = True
                search_strategy = "hybrid"
            
            # Check for current/real-time indicators
            current_indicators = ['current', 'latest', '2024', '2025', 'this year']
            if any(indicator in question_lower for indicator in current_indicators):
                needs_web_search = True
                search_strategy = "web_primary"
            
            # Route to specialized agents
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
                    complaint_info = f"Category: {category}"
                    break
            
            routing_result = {
                "selected_agents": selected_agents,
                "needs_web_search": needs_web_search,
                "search_strategy": search_strategy,
                "complaint_info": complaint_info,
                "confidence": "high" if selected_agents else "medium"
            }
            
            return json.dumps(routing_result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in intelligent routing: {e}")
            return json.dumps({
                "selected_agents": ["base_agent"],
                "needs_web_search": False,
                "search_strategy": "rag_only",
                "error": str(e)
            })

class HybridResponseCombinerTool(BaseTool):
    """Tool for combining RAG and web search results"""
    
    name: str = "hybrid_response_combiner"
    description: str = "Combine and synthesize responses from RAG system and web search"
    
    def _run(self, rag_response: str, web_search_response: str, strategy: str = "hybrid") -> str:
        """Combine RAG and web search results intelligently"""
        try:
            if strategy == "web_primary":
                # Use web search as primary, RAG as backup
                if web_search_response and "No web search results found" not in web_search_response:
                    return f"Current Information (Web Search):\n{web_search_response}\n\nHistorical Context (RAG):\n{rag_response}"
                else:
                    return f"Historical Information (RAG):\n{rag_response}"
            
            elif strategy == "hybrid":
                # Combine both sources
                if web_search_response and "No web search results found" not in web_search_response:
                    return f"Current Information (Web Search):\n{web_search_response}\n\nHistorical Context (RAG):\n{rag_response}"
                else:
                    return f"Information (RAG):\n{rag_response}"
            
            else:  # rag_only
                return f"Information (RAG):\n{rag_response}"
                
        except Exception as e:
            logger.error(f"Error combining responses: {e}")
            return f"Error combining responses: {e}"

class EnhancedCoordinatorAgent:
    """Enhanced coordinator agent with intelligent RAG/web search routing"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None) -> None:
        
        # Initialize LLM
        self.model_name = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self.temperature = temperature or float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize specialized agents
        self.loan_specialist = LoanSpecialist()
        self.grant_specialist = GrantSpecialist()
        self.application_helper = ApplicationHelper()
        self.base_agent = BaseAgent()
        
        # Initialize web search tool
        self.web_search_tool = create_tavily_web_search_tool()
        
        # Initialize tools
        self.tools = [
            IntelligentRouterTool(),
            HybridResponseCombinerTool()
        ]
        
        # Create agent and workflow
        self.agent = self._create_agent()
        self.workflow = self._create_workflow()
    
    def _create_agent(self) -> None:
        """Create the enhanced coordinator agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an enhanced coordinator for SmartBorrow, a student loan and financial aid information system.

You have access to:
1. Specialized agents (loan specialist, grant specialist, application helper)
2. RAG system with processed financial aid data
3. Web search for current, real-time information
4. Intelligent routing between local and web sources

Your role is to:
1. Route questions to appropriate specialized agents
2. Determine when web search is needed for current information
3. Combine responses from multiple sources intelligently
4. Provide comprehensive, accurate answers

Available tools:
- intelligent_router: Route questions and determine search strategy
- hybrid_response_combiner: Combine RAG and web search results

Current question: {question}"""),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        return create_openai_functions_agent(self.llm, self.tools, prompt)
    
    def _create_workflow(self) -> None:
        """Create the enhanced LangGraph workflow"""
        
        def route_question(state: EnhancedCoordinatorState) -> EnhancedCoordinatorState:
            """Route question using intelligent router"""
            try:
                # Use intelligent router
                routing_result = self.agent.invoke({
                    "input": f"Route this question: {state.question}",
                    "question": state.question,
                    "agent_scratchpad": "",
                    "intermediate_steps": []
                })
                
                # Parse routing result
                import json
                routing_info = json.loads(routing_result.get("output", "{}"))
                
                state.selected_agents = routing_info.get("selected_agents", ["base_agent"])
                state.search_strategy = routing_info.get("search_strategy", "rag_only")
                state.routing_info = routing_info
                
                return state
                
            except Exception as e:
                logger.error(f"Error in route_question: {e}")
                state.selected_agents = ["base_agent"]
                state.search_strategy = "rag_only"
                return state
        
        def get_agent_responses(state: EnhancedCoordinatorState) -> EnhancedCoordinatorState:
            """Get responses from selected agents"""
            try:
                agent_responses = {}
                
                for agent_name in state.selected_agents:
                    if agent_name == "loan_specialist":
                        response = self.loan_specialist.run(state.question)
                    elif agent_name == "grant_specialist":
                        response = self.grant_specialist.run(state.question)
                    elif agent_name == "application_helper":
                        response = self.application_helper.run(state.question)
                    else:  # base_agent
                        response = self.base_agent.run(state.question)
                    
                    agent_responses[agent_name] = response
                
                state.agent_responses = agent_responses
                return state
                
            except Exception as e:
                logger.error(f"Error in get_agent_responses: {e}")
                return state
        
        def get_web_search_results(state: EnhancedCoordinatorState) -> EnhancedCoordinatorState:
            """Get web search results if needed"""
            try:
                if state.search_strategy in ["hybrid", "web_primary"]:
                    web_results = self.web_search_tool._run(state.question)
                    state.web_search_results = web_results
                else:
                    state.web_search_results = None
                
                return state
                
            except Exception as e:
                logger.error(f"Error in get_web_search_results: {e}")
                return state
        
        def combine_responses(state: EnhancedCoordinatorState) -> EnhancedCoordinatorState:
            """Combine all responses intelligently"""
            try:
                # Get RAG response from agent responses
                rag_response = ""
                for agent_name, response in state.agent_responses.items():
                    if isinstance(response, dict):
                        rag_response += f"\n{agent_name}: {response.get('response', '')}"
                    else:
                        rag_response += f"\n{agent_name}: {response}"
                
                # Combine with web search if available
                if state.web_search_results:
                    combined_response = self.agent.invoke({
                        "input": f"Combine RAG response: {rag_response}\nWeb search: {state.web_search_results}\nStrategy: {state.search_strategy}",
                        "question": state.question,
                        "agent_scratchpad": "",
                        "intermediate_steps": []
                    })
                    
                    state.final_response = combined_response.get("output", "")
                else:
                    state.final_response = rag_response
                
                state.confidence = "high" if state.web_search_results else "medium"
                return state
                
            except Exception as e:
                logger.error(f"Error in combine_responses: {e}")
                state.final_response = f"Error combining responses: {e}"
                return state
        
        # Create the workflow
        workflow = StateGraph(EnhancedCoordinatorState)
        
        # Add nodes
        workflow.add_node("route_question", route_question)
        workflow.add_node("get_agent_responses", get_agent_responses)
        workflow.add_node("get_web_search_results", get_web_search_results)
        workflow.add_node("combine_responses", combine_responses)
        
        # Add edges
        workflow.add_edge("route_question", "get_agent_responses")
        workflow.add_edge("get_agent_responses", "get_web_search_results")
        workflow.add_edge("get_web_search_results", "combine_responses")
        workflow.add_edge("combine_responses", END)
        
        # Set entry point
        workflow.set_entry_point("route_question")
        
        return workflow.compile()
    
    def run(self, question: str) -> Dict[str, Any]:
        """Run the enhanced coordinator with a question"""
        try:
            # Initialize state
            state = EnhancedCoordinatorState(
                messages=[HumanMessage(content=question)],
                question=question,
                agent_responses={},
                selected_agents=[],
                final_response=None,
                confidence=None,
                routing_info=None,
                search_strategy=None
            )
            
            # Run workflow
            result = self.workflow.invoke(state)
            
            return {
                "question": question,
                "response": result.final_response,
                "confidence": result.confidence,
                "selected_agents": result.selected_agents,
                "search_strategy": result.search_strategy,
                "routing_info": result.routing_info,
                "web_search_used": result.web_search_results is not None
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced coordinator: {e}")
            return {
                "question": question,
                "response": f"Error processing question: {e}",
                "confidence": "low",
                "error": str(e)
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the enhanced coordinator"""
        return {
            "agent_type": "enhanced_coordinator",
            "capabilities": [
                "Intelligent routing between specialized agents",
                "Web search integration for current information",
                "Hybrid response generation",
                "Confidence-based decision making"
            ],
            "available_agents": [
                "loan_specialist",
                "grant_specialist", 
                "application_helper",
                "base_agent"
            ],
            "search_strategies": [
                "rag_only",
                "hybrid",
                "web_primary"
            ],
            "web_search_enabled": self.web_search_tool.client is not None
        }
    
    def test_web_search_integration(self, question: str) -> Dict[str, Any]:
        """Test web search integration with a specific question"""
        try:
            # Test web search directly
            web_results = self.web_search_tool._run(question)
            
            # Test routing
            routing_result = self.agent.invoke({
                "input": f"Route this question: {question}",
                "question": question,
                "agent_scratchpad": "",
                "intermediate_steps": []
            })
            
            return {
                "question": question,
                "web_search_results": web_results,
                "routing_result": routing_result.get("output", ""),
                "web_search_available": self.web_search_tool.client is not None,
                "cache_stats": self.web_search_tool.get_cache_stats()
            }
            
        except Exception as e:
            logger.error(f"Error testing web search integration: {e}")
            return {
                "question": question,
                "error": str(e),
                "web_search_available": False
            }

def main() -> None:
    """Test the enhanced coordinator agent"""
    import asyncio
    
    async def test_enhanced_coordinator():
        coordinator = EnhancedCoordinatorAgent()
        
        # Test questions
        test_questions = [
            "What are the current interest rates for Direct Loans?",
            "How much does Harvard cost for 2024-2025?",
            "What are the recent changes to FAFSA?",
            "How do I qualify for a Pell Grant?"
        ]
        
        for question in test_questions:
            print(f"\n{'='*60}")
            print(f"Question: {question}")
            print(f"{'='*60}")
            
            result = coordinator.run(question)
            print(f"Response: {result['response'][:500]}...")
            print(f"Confidence: {result['confidence']}")
            print(f"Selected Agents: {result['selected_agents']}")
            print(f"Search Strategy: {result['search_strategy']}")
            print(f"Web Search Used: {result.get('web_search_used', False)}")
        
        # Test web search integration
        print(f"\n{'='*60}")
        print("Testing Web Search Integration")
        print(f"{'='*60}")
        
        test_result = coordinator.test_web_search_integration("current federal student loan interest rates 2024")
        print(f"Web Search Available: {test_result['web_search_available']}")
        print(f"Cache Stats: {test_result['cache_stats']}")
    
    asyncio.run(test_enhanced_coordinator())

if __name__ == "__main__":
    main() 