"""
Evaluation Runner for SmartBorrow

Run evaluation using synthetic data:
- Test on easy, medium, hard difficulty levels
- Generate reports showing performance on each document type
- Save results to data/evaluation/
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

from .ragas_evaluator import RAGASEvaluator, ComparisonResult
from .test_loader import TestLoader

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
console = Console()

class EvaluationRunner:
    """Run comprehensive evaluation of SmartBorrow systems"""
    
    def __init__(self, 
                 processed_data_path: str = "data/processed",
                 evaluation_output_path: str = "data/evaluation") -> None:
        
        self.processed_data_path = Path(processed_data_path)
        self.evaluation_output_path = Path(evaluation_output_path)
        self.evaluation_output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.evaluator = RAGASEvaluator(processed_data_path, evaluation_output_path)
        self.test_loader = TestLoader(processed_data_path)
        
        # Results storage
        self.results = {}
        self.reports = {}
    
    def run_full_evaluation(self) -> Dict[str, ComparisonResult]:
        """Run complete evaluation on all datasets"""
        try:
            console.logger.info("[bold blue]Starting Full RAGAS Evaluation...[/bold blue]")
            
            # Initialize systems
            console.logger.info("Initializing systems...")
            self.evaluator.initialize_systems()
            
            # Get dataset statistics
            stats = self.test_loader.get_dataset_stats()
            console.logger.info("Dataset Statistics: {stats['total_test_cases']} total test cases")
            
            # Run evaluation on all datasets
            console.logger.info("Running evaluation on all datasets...")
            self.results = self.evaluator.evaluate_all_datasets()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"full_evaluation_{timestamp}.json"
            self.evaluator.save_results(self.results, filename)
            
            console.logger.info("[green]✓ Full evaluation completed![/green]")
            console.logger.info("Results saved to: {self.evaluation_output_path / filename}")
            
            return self.results
            
        except Exception as e:
            console.logger.info("[red]Error in full evaluation: {e}[/red]")
            logger.error(f"Error in full evaluation: {e}")
            return {}
    
    def run_difficulty_evaluation(self) -> Dict[str, ComparisonResult]:
        """Run evaluation on different difficulty levels"""
        try:
            console.logger.info("[bold blue]Running Difficulty-Level Evaluation...[/bold blue]")
            
            # Initialize systems
            self.evaluator.initialize_systems()
            
            # Get difficulty datasets
            difficulty_datasets = self.test_loader.create_difficulty_datasets()
            
            results = {}
            
            for difficulty, dataset in difficulty_datasets.items():
                console.logger.info("Evaluating {difficulty} difficulty ({len(dataset.test_cases)} test cases)...")
                
                try:
                    comparison = self.evaluator.compare_systems(dataset)
                    results[difficulty] = comparison
                    
                    # Display quick results
                    rag_metrics = comparison.rag_results.metrics
                    agent_metrics = comparison.agent_results.metrics
                    
                    console.logger.info("  RAG Metrics: {rag_metrics}")
                    console.logger.info("  Agent Metrics: {agent_metrics}")
                    console.logger.info("  Improvement: {comparison.improvement}")
                    
                except Exception as e:
                    console.logger.info("[red]Error evaluating {difficulty}: {e}[/red]")
                    continue
            
            # Save difficulty results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"difficulty_evaluation_{timestamp}.json"
            self.evaluator.save_results(results, filename)
            
            console.logger.info("[green]✓ Difficulty evaluation completed![/green]")
            return results
            
        except Exception as e:
            console.logger.info("[red]Error in difficulty evaluation: {e}[/red]")
            logger.error(f"Error in difficulty evaluation: {e}")
            return {}
    
    def run_category_evaluation(self) -> Dict[str, ComparisonResult]:
        """Run evaluation on different categories"""
        try:
            console.logger.info("[bold blue]Running Category-Based Evaluation...[/bold blue]")
            
            # Initialize systems
            self.evaluator.initialize_systems()
            
            # Get category datasets
            category_datasets = self.test_loader.create_category_datasets()
            
            results = {}
            
            for category, dataset in category_datasets.items():
                console.logger.info("Evaluating {category} category ({len(dataset.test_cases)} test cases)...")
                
                try:
                    comparison = self.evaluator.compare_systems(dataset)
                    results[category] = comparison
                    
                    # Display quick results
                    rag_metrics = comparison.rag_results.metrics
                    agent_metrics = comparison.agent_results.metrics
                    
                    console.logger.info("  RAG Metrics: {rag_metrics}")
                    console.logger.info("  Agent Metrics: {agent_metrics}")
                    console.logger.info("  Improvement: {comparison.improvement}")
                    
                except Exception as e:
                    console.logger.info("[red]Error evaluating {category}: {e}[/red]")
                    continue
            
            # Save category results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"category_evaluation_{timestamp}.json"
            self.evaluator.save_results(results, filename)
            
            console.logger.info("[green]✓ Category evaluation completed![/green]")
            return results
            
        except Exception as e:
            console.logger.info("[red]Error in category evaluation: {e}[/red]")
            logger.error(f"Error in category evaluation: {e}")
            return {}
    
    def generate_summary_report(self, results: Dict[str, ComparisonResult]) -> Dict[str, Any]:
        """Generate a summary report of evaluation results"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_datasets': len(results),
                'summary_metrics': {},
                'best_performing_system': {},
                'improvement_analysis': {},
                'recommendations': []
            }
            
            # Aggregate metrics across all datasets
            all_rag_metrics = {}
            all_agent_metrics = {}
            all_improvements = {}
            
            for dataset_name, comparison in results.items():
                # Aggregate RAG metrics
                for metric, score in comparison.rag_results.metrics.items():
                    if metric not in all_rag_metrics:
                        all_rag_metrics[metric] = []
                    all_rag_metrics[metric].append(score)
                
                # Aggregate Agent metrics
                for metric, score in comparison.agent_results.metrics.items():
                    if metric not in all_agent_metrics:
                        all_agent_metrics[metric] = []
                    all_agent_metrics[metric].append(score)
                
                # Aggregate improvements
                for metric, improvement in comparison.improvement.items():
                    if metric not in all_improvements:
                        all_improvements[metric] = []
                    all_improvements[metric].append(improvement)
            
            # Calculate averages
            for metric in all_rag_metrics:
                avg_rag = sum(all_rag_metrics[metric]) / len(all_rag_metrics[metric])
                avg_agent = sum(all_agent_metrics[metric]) / len(all_agent_metrics[metric])
                avg_improvement = sum(all_improvements[metric]) / len(all_improvements[metric])
                
                report['summary_metrics'][metric] = {
                    'rag_average': avg_rag,
                    'agent_average': avg_agent,
                    'average_improvement': avg_improvement
                }
                
                # Determine best performing system
                if avg_improvement > 0.05:
                    report['best_performing_system'][metric] = 'agent'
                elif avg_improvement < -0.05:
                    report['best_performing_system'][metric] = 'rag'
                else:
                    report['best_performing_system'][metric] = 'similar'
            
            # Generate recommendations
            agent_wins = sum(1 for system in report['best_performing_system'].values() if system == 'agent')
            rag_wins = sum(1 for system in report['best_performing_system'].values() if system == 'rag')
            
            if agent_wins > rag_wins:
                report['recommendations'].append("Agent system shows overall better performance")
            elif rag_wins > agent_wins:
                report['recommendations'].append("RAG system shows overall better performance")
            else:
                report['recommendations'].append("Both systems perform similarly")
            
            # Add specific recommendations based on metrics
            for metric, summary in report['summary_metrics'].items():
                if summary['average_improvement'] > 0.1:
                    report['recommendations'].append(f"Agent significantly outperforms RAG on {metric}")
                elif summary['average_improvement'] < -0.1:
                    report['recommendations'].append(f"RAG significantly outperforms Agent on {metric}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return {'error': str(e)}
    
    def display_results_table(self, results: Dict[str, ComparisonResult]) -> None:
        """Display results in a formatted table"""
        try:
            table = Table(title="RAGAS Evaluation Results")
            table.add_column("Dataset", style="cyan")
            table.add_column("System", style="magenta")
            table.add_column("Faithfulness", style="green")
            table.add_column("Answer Relevancy", style="green")
            table.add_column("Context Precision", style="green")
            table.add_column("Context Recall", style="green")
            table.add_column("Improvement", style="yellow")
            
            for dataset_name, comparison in results.items():
                # RAG results
                rag_metrics = comparison.rag_results.metrics
                table.add_row(
                    dataset_name,
                    "RAG",
                    f"{rag_metrics.get('faithfulness', 'N/A'):.3f}",
                    f"{rag_metrics.get('answer_relevancy', 'N/A'):.3f}",
                    f"{rag_metrics.get('context_precision', 'N/A'):.3f}",
                    f"{rag_metrics.get('context_recall', 'N/A'):.3f}",
                    ""
                )
                
                # Agent results
                agent_metrics = comparison.agent_results.metrics
                improvement = comparison.improvement
                avg_improvement = sum(improvement.values()) / len(improvement) if improvement else 0
                
                table.add_row(
                    dataset_name,
                    "Agent",
                    f"{agent_metrics.get('faithfulness', 'N/A'):.3f}",
                    f"{agent_metrics.get('answer_relevancy', 'N/A'):.3f}",
                    f"{agent_metrics.get('context_precision', 'N/A'):.3f}",
                    f"{agent_metrics.get('context_recall', 'N/A'):.3f}",
                    f"{avg_improvement:+.3f}"
                )
            
            console.print(table)
            
        except Exception as e:
            console.logger.info("[red]Error displaying results table: {e}[/red]")
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> None:
        """Save evaluation report to file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"evaluation_report_{timestamp}.json"
            
            output_file = self.evaluation_output_path / filename
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            console.logger.info("[green]Report saved to: {output_file}[/green]")
            return output_file
            
        except Exception as e:
            console.logger.info("[red]Error saving report: {e}[/red]")
            return None

def main() -> None:
    """Test the evaluation runner"""
    runner = EvaluationRunner()
    
    # Run full evaluation
    results = runner.run_full_evaluation()
    
    if results:
        # Generate and display summary
        summary = runner.generate_summary_report(results)
        runner.display_results_table(results)
        
        # Save report
        runner.save_report(summary)
        
        console.logger.info("[bold green]Evaluation completed successfully![/bold green]")

if __name__ == "__main__":
    main() 