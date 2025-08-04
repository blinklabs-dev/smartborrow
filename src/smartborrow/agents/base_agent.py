"""
Base Agent for SmartBorrow Multi-Agent System

BaseAgent with LangGraph StateMachine that provides tools for:
- Querying the RAG system
- Accessing processed numerical data
- Using structured knowledge from content_enricher
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv

from ..rag.rag_service import RAGService
from .tavily_web_search import create_tavily_web_search_tool

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """State for agent workflow"""
    messages: List[BaseMessage]
    question: str
    context: Dict[str, Any]
    numerical_data: List[Dict[str, Any]]
    structured_knowledge: Dict[str, Any]
    response: Optional[str] = None
    confidence: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None

class RAGQueryTool(BaseTool):
    """Tool for querying the RAG system"""
    
    name: str = "rag_query"
    description: str = "Query the RAG system for information about student loans, grants, and financial aid"
    rag_service: RAGService = None
    
    def __init__(self, rag_service: RAGService = None) -> None:
        super().__init__()
        self.rag_service = rag_service
    
    def _run(self, query: str) -> str:
        """Run the RAG query"""
        try:
            result = self.rag_service.query(query)
            return result.get("answer", "No answer found")
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"Error querying RAG system: {e}"

class NumericalDataTool(BaseTool):
    """Tool for accessing processed numerical data"""
    
    name: str = "numerical_data"
    description: str = "Access numerical data points like interest rates, amounts, limits, and deadlines"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, category: str = "all") -> str:
        """Get numerical data for a specific category"""
        try:
            import json
            from pathlib import Path
            
            numerical_file = Path(self.processed_data_path) / "numerical_data.json"
            if not numerical_file.exists():
                return "No numerical data found in the processed data directory."
            
            with open(numerical_file, 'r') as f:
                data = json.load(f)
            
            if category == "all":
                return f"Found {len(data)} numerical data points across all categories in the processed financial aid data."
            
            # Filter by category
            filtered_data = [item for item in data if item.get('category') == category]
            
            if not filtered_data:
                return f"No numerical data found for category: {category}. Available categories include: interest rates, loan limits, grant amounts, deadlines, etc."
            
            # Format the data with better structure
            result = f"Found {len(filtered_data)} data points for {category}:\n\n"
            for i, item in enumerate(filtered_data[:5], 1):  # Limit to first 5 for readability
                value = item.get('value', 'N/A')
                unit = item.get('unit', '')
                context = item.get('context', '')
                
                result += f"{i}. {value} {unit}\n"
                if context:
                    result += f"   Context: {context[:150]}{'...' if len(context) > 150 else ''}\n"
                result += "\n"
            
            if len(filtered_data) > 5:
                result += f"... and {len(filtered_data) - 5} more data points."
            
            return result
            
        except Exception as e:
            logger.error(f"Error accessing numerical data: {e}")
            return f"Error accessing numerical data: {e}"

class StructuredKnowledgeTool(BaseTool):
    """Tool for accessing structured knowledge"""
    
    name: str = "structured_knowledge"
    description: str = "Access structured knowledge about concepts, definitions, requirements, and procedures"
    processed_data_path: str = "data/processed"
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        super().__init__()
        self.processed_data_path = processed_data_path
    
    def _run(self, concept: str = "all") -> str:
        """Get structured knowledge for a specific concept"""
        try:
            import json
            from pathlib import Path
            
            knowledge_file = Path(self.processed_data_path) / "structured_knowledge.json"
            if not knowledge_file.exists():
                return "No structured knowledge found"
            
            with open(knowledge_file, 'r') as f:
                data = json.load(f)
            
            if concept == "all":
                concepts = list(data.keys())
                return f"Available concepts: {', '.join(concepts)}"
            
            if concept not in data:
                return f"Concept '{concept}' not found. Available: {', '.join(data.keys())}"
            
            concept_data = data[concept]
            result = f"Knowledge for '{concept}':\n"
            
            if concept_data.get('definition'):
                result += f"Definition: {concept_data['definition']}\n\n"
            
            if concept_data.get('requirements'):
                result += f"Requirements:\n"
                for req in concept_data['requirements'][:3]:
                    result += f"- {req}\n"
                result += "\n"
            
            if concept_data.get('procedures'):
                result += f"Procedures:\n"
                for proc in concept_data['procedures'][:3]:
                    result += f"- {proc}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error accessing structured knowledge: {e}")
            return f"Error accessing structured knowledge: {e}"

class BaseAgent:
    """Base agent with LangGraph StateMachine"""
    
    def __init__(self, 
                 model_name: str = None,
                 temperature: float = None,
                 rag_service: RAGService = None) -> None:
        
        # Initialize LLM
        self.model_name = model_name or os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = temperature or float(os.getenv("AGENT_TEMPERATURE", "0.1"))
        
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize RAG service
        self.rag_service = rag_service or RAGService()
        if not self.rag_service.is_initialized:
            self.rag_service.initialize()
        
        # Initialize tools
        self.tools = [
            RAGQueryTool(self.rag_service),
            NumericalDataTool(),
            StructuredKnowledgeTool(),
            create_tavily_web_search_tool()  # Add web search capability
        ]
        

        
        # Create agent
        self.agent = self._create_agent()
        
        # Create workflow
        self.workflow = self._create_workflow()
    
    def _create_agent(self) -> None:
        """Create the agent with tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for SmartBorrow, a student loan and financial aid information system.

You have access to:
1. A RAG system with processed financial aid data
2. Numerical data points (interest rates, amounts, limits)
3. Structured knowledge (definitions, requirements, procedures)
4. Web search for current, real-time information

Use the available tools to provide accurate, comprehensive answers. Always cite your sources and provide specific numerical data when available.

For questions about current information (interest rates, deadlines, policy updates), use web search to get the most up-to-date information.

Available tools:
- rag_query: Query the RAG system for information
- numerical_data: Access processed numerical data points
- structured_knowledge: Access structured knowledge about concepts
- tavily_web_search: Search the web for current information

Current question: {question}"""),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        return create_openai_functions_agent(self.llm, self.tools, prompt)
    
    def _create_workflow(self) -> None:
        """Create the LangGraph workflow"""
        
        def call_agent(state: AgentState) -> AgentState:
            """Call the agent"""
            try:
                # Use RAG service directly for better answers
                if self.rag_service and self.rag_service.is_initialized:
                    rag_result = self.rag_service.query(state.question)
                    answer = rag_result.get("answer", "No answer available")
                    confidence = rag_result.get("confidence", "unknown")
                    sources = rag_result.get("sources", [])
                    
                    # Update state with RAG response
                    state.response = answer
                    state.confidence = confidence
                    state.sources = sources
                    return state
                else:
                    # Fallback to agent tools if RAG not available
                    response = self.agent.invoke({
                        "input": state.question,
                        "question": state.question,
                        "agent_scratchpad": "",
                        "intermediate_steps": []
                    })
                    
                    # Extract answer from various response types
                    if isinstance(response, dict):
                        answer = response.get("output") or response.get("answer") or str(response)
                    elif hasattr(response, "content"):
                        answer = response.content
                    else:
                        answer = str(response)
                    
                    # Clean up the answer if it's too verbose
                    if len(answer) > 1000:
                        answer = answer[:1000] + "..."
                    
                    state.response = answer
                    return state
                    
            except Exception as e:
                logger.error(f"Error in call_agent: {e}")
                state.response = f"Error processing question: {e}"
                return state
        
        # Create the workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", call_agent)
        
        # Add edges
        workflow.add_edge("agent", END)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        return workflow.compile()
    
    def run(self, question: str) -> Dict[str, Any]:
        """Run the agent with a question"""
        try:
            # Initialize state
            state = AgentState(
                messages=[HumanMessage(content=question)],
                question=question,
                context={},
                numerical_data=[],
                structured_knowledge={}
            )
            
            # Run workflow
            result = self.workflow.invoke(state)
            # Handle both AgentState and dict
            if isinstance(result, dict):
                answer = result.get("response") or result.get("output") or str(result)
                confidence = result.get("confidence", "unknown")
                sources = result.get("sources", [])
                context = result.get("context", {})
            else:
                answer = getattr(result, "response", str(result))
                confidence = getattr(result, "confidence", "unknown")
                sources = getattr(result, "sources", [])
                context = getattr(result, "context", {})
            
            return {
                "question": question,
                "response": answer,
                "confidence": confidence,
                "sources": sources,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "question": question,
                "response": f"Error processing question: {e}",
                "confidence": "error",
                "sources": [],
                "context": {}
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "tools": [tool.name for tool in self.tools],
            "rag_initialized": self.rag_service.is_initialized
        }

def main() -> None:
    """Test the base agent"""
    agent = BaseAgent()
    
    # Test questions
    test_questions = [
        "What is the maximum Pell Grant amount?",
        "What are the current interest rates for Direct Loans?",
        "How do I qualify for a Pell Grant?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*60}")
        logger.info("Question: {question}")
        logger.info("{'='*60}")
        
        result = agent.run(question)
        
        logger.info("Response: {result['response']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Sources: {len(result.get('sources', []))}")

if __name__ == "__main__":
    main() 