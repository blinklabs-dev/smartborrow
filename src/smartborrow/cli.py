"""Command-line interface for SmartBorrow AI Platform.

Provides a comprehensive CLI for managing the SmartBorrow system including
RAG operations, agent testing, evaluation, and application launching.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .core.config import get_settings
from .rag.rag_service import RAGService
from .agents.coordinator import CoordinatorAgent
from .evaluation.evaluation_runner import EvaluationRunner
from .evaluation.performance_tracker import PerformanceTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="SmartBorrow AI Platform CLI")
console = Console()


@app.command()
def info() -> None:
    """Display SmartBorrow system information."""
    settings = get_settings()
    
    table = Table(title="SmartBorrow AI Platform - System Information")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Environment", settings.environment)
    table.add_row("LLM Model", settings.default_llm_model)
    table.add_row("Embedding Model", settings.default_embedding_model)
    table.add_row("Chunk Size", str(settings.default_chunk_size))
    table.add_row("API Port", str(settings.api_port))
    
    console.print(table)


@app.command()
def setup() -> None:
    """Run initial setup and validation."""
    console.logger.info("[bold green]SmartBorrow AI Platform Setup[/bold green]")
    
    settings = get_settings()
    
    # Check API keys
    if not settings.openai_api_key:
        console.logger.info("[yellow]Warning: OpenAI API key not configured[/yellow]")
    else:
        console.logger.info("[green]✓ OpenAI API key configured[/green]")
    
    if not settings.langchain_api_key:
        console.logger.info("[yellow]Warning: LangChain API key not configured[/yellow]")
    else:
        console.logger.info("[green]✓ LangChain API key configured[/green]")
    
    console.logger.info("[bold green]Setup complete![/bold green]")


@app.command()
def build_rag() -> None:
    """Build RAG system from processed data."""
    console.logger.info("[bold blue]Building SmartBorrow RAG System...[/bold blue]")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        console.logger.info("Initializing RAG service...")
        if rag_service.initialize():
            console.logger.info("[green]✓ RAG system built successfully![/green]")
            
            # Get stats
            stats = rag_service.get_service_stats()
            total_docs = stats.get('vectorstore_stats', {}).get('total_documents', 0)
            console.logger.info("Vector store created with {total_docs} documents")
        else:
            console.logger.info("[red]✗ Failed to build RAG system[/red]")
            
    except Exception as e:
        logger.error(f"Error building RAG system: {e}")
        console.logger.info("[red]Error building RAG system: {e}[/red]")


@app.command()
def query_rag(
    question: str = typer.Argument(..., help="Question to ask the RAG system"),
    search_type: str = typer.Option("hybrid", help="Search type to use")
) -> None:
    """Query the RAG system with improved smart search."""
    console.logger.info("[bold blue]Querying SmartBorrow Smart Search System...[/bold blue]")
    console.logger.info("Question: {question}")
    console.logger.info("Search Type: {search_type}")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        if not rag_service.initialize():
            console.logger.info("[red]✗ Failed to initialize RAG service[/red]")
            return
        
        # Query the system with smart search
        result = rag_service.smart_search(question, search_type=search_type, format_response=True)
        
        # Display results
        if result.get("error"):
            console.logger.info("[red]Error: {result['error']}[/red]")
        else:
            # Create answer panel with better formatting
            answer_text = Text(result["answer"], style="white")
            answer_panel = Panel(answer_text, title="Smart Search Answer", border_style="green")
            console.print(answer_panel)
            
            # Display metadata in a table
            metadata_table = Table(title="Search Metadata")
            metadata_table.add_column("Property", style="cyan")
            metadata_table.add_column("Value", style="green")
            
            metadata_table.add_row("Search Type", search_type)
            metadata_table.add_row("Confidence", result.get("confidence", "unknown"))
            metadata_table.add_row("Documents Used", str(result.get("documents_used", 0)))
            metadata_table.add_row("Sources", str(len(result.get("sources", []))))
            
            # Add hybrid-specific metadata
            if search_type == "hybrid":
                metadata_table.add_row("Semantic Docs", str(result.get("semantic_docs", 0)))
                metadata_table.add_row("Keyword Docs", str(result.get("keyword_docs", 0)))
                metadata_table.add_row("Numerical Docs", str(result.get("numerical_docs", 0)))
            
            console.print(metadata_table)
            
            # Display sources if available
            if result.get("sources"):
                sources_table = Table(title="Sources")
                sources_table.add_column("Document Type", style="cyan")
                sources_table.add_column("Category", style="green")
                sources_table.add_column("Confidence", style="yellow")
                sources_table.add_column("Concept", style="blue")
                
                for source in result["sources"][:3]:  # Show first 3 sources
                    sources_table.add_row(
                        source.get("document_type", "unknown").title(),
                        source.get("category", "unknown"),
                        str(source.get("confidence", 0.8)),
                        source.get("concept", "N/A")
                    )
                
                console.print(sources_table)
            
            # Display numerical summary if available
            if result.get("numerical_summary"):
                numerical_panel = Panel(
                    Text(result["numerical_summary"], style="blue"),
                    title="📊 Numerical Summary",
                    border_style="blue"
                )
                console.print(numerical_panel)
        
    except Exception as e:
        logger.error(f"Error querying RAG system: {e}")
        console.logger.info("[red]Error querying RAG system: {e}[/red]")


@app.command()
def smart_search(
    question: str = typer.Argument(..., help="Question to ask"),
    search_type: str = typer.Option("hybrid", help="Search type to use")
) -> None:
    """Enhanced smart search with multiple retrieval strategies."""
    console.logger.info("[bold blue]SmartBorrow Enhanced Search...[/bold blue]")
    console.logger.info("Question: {question}")
    console.logger.info("Search Type: {search_type}")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        if not rag_service.initialize():
            console.logger.info("[red]✗ Failed to initialize RAG service[/red]")
            return
        
        # Run smart search
        result = rag_service.smart_search(question, search_type=search_type, format_response=True)
        
        # Display results
        if result.get("error"):
            console.logger.info("[red]Error: {result['error']}[/red]")
        else:
            # Create answer panel
            answer_text = Text(result["answer"], style="white")
            answer_panel = Panel(answer_text, title="Smart Search Answer", border_style="green")
            console.print(answer_panel)
            
            # Display search performance metrics
            metrics_table = Table(title="Search Performance")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")
            
            metrics_table.add_row("Search Type", search_type)
            metrics_table.add_row("Confidence", result.get("confidence", "unknown"))
            metrics_table.add_row("Documents Used", str(result.get("documents_used", 0)))
            metrics_table.add_row("Sources", str(len(result.get("sources", []))))
            
            if search_type == "hybrid":
                metrics_table.add_row("Semantic Docs", str(result.get("semantic_docs", 0)))
                metrics_table.add_row("Keyword Docs", str(result.get("keyword_docs", 0)))
                metrics_table.add_row("Numerical Docs", str(result.get("numerical_docs", 0)))
            
            console.print(metrics_table)
            
            # Display sources
            if result.get("sources"):
                sources_table = Table(title="Sources")
                sources_table.add_column("Type", style="cyan")
                sources_table.add_column("Category", style="green")
                sources_table.add_column("Confidence", style="yellow")
                
                for source in result["sources"][:3]:
                    sources_table.add_row(
                        source.get("document_type", "unknown").title(),
                        source.get("category", "unknown"),
                        str(source.get("confidence", 0.8))
                    )
                
                console.print(sources_table)
        
    except Exception as e:
        logger.error(f"Error in smart search: {e}")
        console.logger.info("[red]Error in smart search: {e}[/red]")


@app.command()
def compare_search_methods(
    question: str = typer.Argument(..., help="Question to compare methods for")
) -> None:
    """Compare different search methods for a question."""
    console.logger.info("[bold blue]Comparing Search Methods...[/bold blue]")
    console.logger.info("Question: {question}")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        if not rag_service.initialize():
            console.logger.info("[red]✗ Failed to initialize RAG service[/red]")
            return
        
        # Test different search methods
        search_methods = ["hybrid", "semantic", "keyword", "numerical"]
        results = {}
        
        for method in search_methods:
            console.logger.info("\n[blue]Testing {method} search...[/blue]")
            result = rag_service.smart_search(question, search_type=method, format_response=False)
            results[method] = result
        
        # Display comparison
        comparison_table = Table(title="Search Method Comparison")
        comparison_table.add_column("Method", style="cyan")
        comparison_table.add_column("Confidence", style="green")
        comparison_table.add_column("Documents", style="yellow")
        comparison_table.add_column("Sources", style="blue")
        comparison_table.add_column("Answer Length", style="magenta")
        
        for method, result in results.items():
            if not result.get("error"):
                answer_length = len(result.get("answer", ""))
                comparison_table.add_row(
                    method.title(),
                    result.get("confidence", "unknown"),
                    str(result.get("documents_used", 0)),
                    str(len(result.get("sources", []))),
                    str(answer_length)
                )
        
        console.print(comparison_table)
        
        # Find best method
        best_method = max(results.items(), key=lambda x: 
            (x[1].get("confidence") == "high", len(x[1].get("sources", [])))
        )[0]
        
        console.logger.info("\n[green]Best performing method: {best_method}[/green]")
        
    except Exception as e:
        logger.error(f"Error comparing search methods: {e}")
        console.logger.info("[red]Error comparing search methods: {e}[/red]")


@app.command()
def test_agents(
    question: str = typer.Argument(..., help="Question to test with agents")
) -> None:
    """Test multi-agent system."""
    console.logger.info("[bold blue]Testing SmartBorrow Multi-Agent System...[/bold blue]")
    console.logger.info("Question: {question}")
    
    try:
        # Initialize coordinator agent
        coordinator = CoordinatorAgent()
        
        # Get agent information
        agent_info = coordinator.get_agent_info()
        console.logger.info("[green]✓ Multi-agent system initialized with {len(agent_info['available_agents'])} agents[/green]")
        
        # Run the coordinator
        result = coordinator.run(question)
        
        # Display results
        if result.get("error"):
            console.logger.info("[red]Error: {result['error']}[/red]")
        else:
            # Create answer panel with better formatting
            response_text = result["response"]
            
            # Clean up the response if it's a raw tool log
            if "tool=" in response_text and "tool_input=" in response_text:
                if "numerical_data" in response_text:
                    response_text = "Retrieved numerical data about interest rates. Please check the data/processed/numerical_data.json file for specific rates."
                elif "direct_loan_data" in response_text:
                    response_text = "Retrieved Direct Loan specific information. Please check the processed data for detailed loan information."
                elif "pell_grant_data" in response_text:
                    response_text = "Retrieved Pell Grant specific information. Please check the processed data for detailed grant information."
                else:
                    response_text = "Processed your question using specialized tools. The system accessed relevant financial aid data."
            
            answer_text = Text(response_text, style="white")
            answer_panel = Panel(answer_text, title="Multi-Agent Response", border_style="green")
            console.print(answer_panel)
            
            # Display metadata
            metadata_table = Table(title="Agent Coordination Metadata")
            metadata_table.add_column("Property", style="cyan")
            metadata_table.add_column("Value", style="green")
            
            metadata_table.add_row("Selected Agents", ", ".join(result.get("selected_agents", [])))
            metadata_table.add_row("Confidence", result.get("confidence", "unknown"))
            metadata_table.add_row("Agents Consulted", str(len(result.get("agent_responses", {}))))
            
            console.print(metadata_table)
            
            # Display agent details if multiple agents were used
            if len(result.get("agent_responses", {})) > 1:
                agents_table = Table(title="Agent Contributions")
                agents_table.add_column("Agent", style="cyan")
                agents_table.add_column("Response Length", style="green")
                agents_table.add_column("Confidence", style="yellow")
                
                for agent_name, agent_response in result.get("agent_responses", {}).items():
                    response_length = len(agent_response.get("response", ""))
                    confidence = agent_response.get("confidence", "unknown")
                    agents_table.add_row(agent_name, str(response_length), confidence)
                
                console.print(agents_table)
        
    except Exception as e:
        logger.error(f"Error testing multi-agent system: {e}")
        console.logger.info("[red]Error testing multi-agent system: {e}[/red]")


@app.command()
def evaluate_system() -> None:
    """Run RAGAS evaluation using processed test data."""
    console.logger.info("[bold blue]Running SmartBorrow RAGAS Evaluation...[/bold blue]")
    
    try:
        # Initialize evaluation runner
        runner = EvaluationRunner()
        
        # Run fast evaluation (limited dataset)
        console.logger.info("Starting fast evaluation (limited dataset)...")
        results = runner.run_difficulty_evaluation()  # Only difficulty datasets
        
        if results:
            # Generate and display summary
            summary = runner.generate_summary_report(results)
            runner.display_results_table(results)
            
            # Save report
            runner.save_report(summary)
            
            console.logger.info("[green]✓ Evaluation completed successfully![/green]")
            
            # Display performance tracking
            console.logger.info("\n[bold blue]Performance Tracking Summary:[/bold blue]")
            tracker = PerformanceTracker()
            tracker.display_performance_summary()
            
        else:
            console.logger.info("[red]✗ No evaluation results generated[/red]")
            
    except Exception as e:
        logger.error(f"Error running evaluation: {e}")
        console.logger.info("[red]Error running evaluation: {e}[/red]")


@app.command()
def launch_app() -> None:
    """Launch the SmartBorrow Intelligent Interface."""
    console.logger.info("[bold blue]Launching SmartBorrow Intelligent Interface...[/bold blue]")
    
    try:
        # Get the path to the smart interface
        app_file = Path(__file__).parent / "ui" / "smart_interface.py"
        
        if not app_file.exists():
            console.logger.info("[red]❌ Smart interface not found: {app_file}[/red]")
            return
        
        console.logger.info("🎓 Opening intelligent student loan guidance platform...")
        console.logger.info("🔄 Starting Streamlit server...")
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_file),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except Exception as e:
        logger.error(f"Failed to launch app: {e}")
        console.logger.info("[red]❌ Failed to launch app: {e}[/red]")


@app.command()
def launch_wizard() -> None:
    """Launch the Financial Aid Wizard."""
    console.logger.info("[bold blue]Launching Financial Aid Wizard...[/bold blue]")
    
    try:
        # Get the path to the wizard
        wizard_file = Path(__file__).parent / "ui" / "wizards" / "financial_aid_wizard.py"
        
        if not wizard_file.exists():
            console.logger.info("[red]❌ Wizard not found: {wizard_file}[/red]")
            return
        
        console.logger.info("📋 Opening step-by-step financial aid application wizard...")
        console.logger.info("🔄 Starting Streamlit server...")
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(wizard_file),
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
        
    except Exception as e:
        logger.error(f"Failed to launch wizard: {e}")
        console.logger.info("[red]❌ Failed to launch wizard: {e}[/red]")


@app.command()
def launch_planner() -> None:
    """Launch the Smart Financial Planner."""
    console.logger.info("[bold blue]Launching Smart Financial Planner...[/bold blue]")
    
    try:
        # Get the path to the planner
        planner_file = Path(__file__).parent / "ui" / "calculators" / "smart_financial_planner.py"
        
        if not planner_file.exists():
            console.logger.info("[red]❌ Planner not found: {planner_file}[/red]")
            return
        
        console.logger.info("💰 Opening interactive financial planning tools...")
        console.logger.info("🔄 Starting Streamlit server...")
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(planner_file),
            "--server.port", "8503",
            "--server.address", "localhost"
        ])
        
    except Exception as e:
        logger.error(f"Failed to launch planner: {e}")
        console.logger.info("[red]❌ Failed to launch planner: {e}[/red]")


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
