"""
Performance Tracker for SmartBorrow

Track improvements over time:
- Compare different system configurations
- Identify weak areas using complaint analysis
- Track performance trends
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

from .test_loader import TestLoader

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class PerformanceRecord:
    """Single performance record"""
    timestamp: str
    system_type: str  # 'rag' or 'agent'
    configuration: Dict[str, Any]
    metrics: Dict[str, float]
    dataset_name: str
    test_cases_count: int
    metadata: Dict[str, Any]

@dataclass
class PerformanceComparison:
    """Comparison between two performance records"""
    baseline: PerformanceRecord
    current: PerformanceRecord
    improvement: Dict[str, float]
    analysis: Dict[str, Any]

class PerformanceTracker:
    """Track and analyze performance improvements over time"""
    
    def __init__(self, 
                 evaluation_data_path: str = "data/evaluation",
                 processed_data_path: str = "data/processed") -> None:
        
        self.evaluation_data_path = Path(evaluation_data_path)
        self.processed_data_path = Path(processed_data_path)
        self.performance_history = []
        self.complaint_analysis = {}
        
        # Load existing performance data
        self.load_performance_history()
    
    def load_performance_history(self) -> None:
        """Load existing performance records from files"""
        try:
            history_file = self.evaluation_data_path / "performance_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.performance_history = [
                        PerformanceRecord(**record) for record in data
                    ]
                logger.info(f"Loaded {len(self.performance_history)} performance records")
            else:
                logger.info("No existing performance history found")
                
        except Exception as e:
            logger.error(f"Error loading performance history: {e}")
    
    def save_performance_history(self) -> None:
        """Save performance history to file"""
        try:
            history_file = self.evaluation_data_path / "performance_history.json"
            
            # Convert to serializable format
            serializable_history = [asdict(record) for record in self.performance_history]
            
            with open(history_file, 'w') as f:
                json.dump(serializable_history, f, indent=2)
            
            logger.info(f"Saved {len(self.performance_history)} performance records")
            
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")
    
    def add_performance_record(self, 
                              system_type: str,
                              configuration: Dict[str, Any],
                              metrics: Dict[str, float],
                              dataset_name: str,
                              test_cases_count: int,
                              metadata: Dict[str, Any] = None) -> None:
        """Add a new performance record"""
        try:
            record = PerformanceRecord(
                timestamp=datetime.now().isoformat(),
                system_type=system_type,
                configuration=configuration,
                metrics=metrics,
                dataset_name=dataset_name,
                test_cases_count=test_cases_count,
                metadata=metadata or {}
            )
            
            self.performance_history.append(record)
            self.save_performance_history()
            
            logger.info(f"Added performance record for {system_type} system")
            
        except Exception as e:
            logger.error(f"Error adding performance record: {e}")
    
    def get_performance_trends(self, 
                               system_type: str = None,
                               dataset_name: str = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        try:
            # Filter records
            filtered_records = self.performance_history
            
            if system_type:
                filtered_records = [r for r in filtered_records if r.system_type == system_type]
            
            if dataset_name:
                filtered_records = [r for r in filtered_records if r.dataset_name == dataset_name]
            
            # Filter by time
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_records = [
                r for r in filtered_records 
                if datetime.fromisoformat(r.timestamp) > cutoff_date
            ]
            
            if not filtered_records:
                return {'error': 'No records found for the specified criteria'}
            
            # Analyze trends
            trends = {
                'total_records': len(filtered_records),
                'time_period': f"{days_back} days",
                'system_type': system_type or 'all',
                'dataset_name': dataset_name or 'all',
                'metric_trends': {},
                'best_performance': {},
                'worst_performance': {}
            }
            
            # Analyze each metric
            all_metrics = set()
            for record in filtered_records:
                all_metrics.update(record.metrics.keys())
            
            for metric in all_metrics:
                metric_values = [
                    (record.timestamp, record.metrics.get(metric, 0))
                    for record in filtered_records
                    if metric in record.metrics
                ]
                
                if metric_values:
                    # Sort by timestamp
                    metric_values.sort(key=lambda x: x[0])
                    
                    # Calculate trend
                    values = [v for _, v in metric_values]
                    if len(values) > 1:
                        trend_direction = "improving" if values[-1] > values[0] else "declining"
                        avg_value = sum(values) / len(values)
                        max_value = max(values)
                        min_value = min(values)
                    else:
                        trend_direction = "stable"
                        avg_value = values[0] if values else 0
                        max_value = avg_value
                        min_value = avg_value
                    
                    trends['metric_trends'][metric] = {
                        'trend_direction': trend_direction,
                        'average_value': avg_value,
                        'max_value': max_value,
                        'min_value': min_value,
                        'data_points': len(values)
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {'error': str(e)}
    
    def compare_configurations(self, 
                              config1: Dict[str, Any],
                              config2: Dict[str, Any],
                              dataset_name: str = None) -> PerformanceComparison:
        """Compare performance between two configurations"""
        try:
            # Find records for each configuration
            config1_records = [
                r for r in self.performance_history
                if r.configuration == config1 and (dataset_name is None or r.dataset_name == dataset_name)
            ]
            
            config2_records = [
                r for r in self.performance_history
                if r.configuration == config2 and (dataset_name is None or r.dataset_name == dataset_name)
            ]
            
            if not config1_records or not config2_records:
                raise ValueError("No performance records found for the specified configurations")
            
            # Get latest records
            baseline = max(config1_records, key=lambda r: r.timestamp)
            current = max(config2_records, key=lambda r: r.timestamp)
            
            # Calculate improvement
            improvement = {}
            for metric in baseline.metrics:
                if metric in current.metrics:
                    improvement[metric] = current.metrics[metric] - baseline.metrics[metric]
            
            # Analyze results
            analysis = {
                'better_configuration': {},
                'significant_improvements': [],
                'areas_for_improvement': []
            }
            
            for metric, improvement_score in improvement.items():
                if improvement_score > 0.05:  # Significant improvement
                    analysis['significant_improvements'].append(metric)
                    analysis['better_configuration'][metric] = 'config2'
                elif improvement_score < -0.05:  # Significant degradation
                    analysis['areas_for_improvement'].append(metric)
                    analysis['better_configuration'][metric] = 'config1'
                else:
                    analysis['better_configuration'][metric] = 'similar'
            
            comparison = PerformanceComparison(
                baseline=baseline,
                current=current,
                improvement=improvement,
                analysis=analysis
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing configurations: {e}")
            raise
    
    def analyze_complaint_patterns(self) -> Dict[str, Any]:
        """Analyze complaint patterns to identify weak areas"""
        try:
            # Load complaint data
            complaint_file = self.processed_data_path / "complaint_categories.json"
            if not complaint_file.exists():
                return {'error': 'No complaint data found'}
            
            with open(complaint_file, 'r') as f:
                complaint_data = json.load(f)
            
            # Analyze complaint patterns
            analysis = {
                'total_complaints': sum(data.get('count', 0) for data in complaint_data.values()),
                'category_analysis': {},
                'common_issues': [],
                'performance_implications': []
            }
            
            for category, data in complaint_data.items():
                count = data.get('count', 0)
                percentage = data.get('percentage', 0)
                keywords = data.get('common_keywords', [])
                
                analysis['category_analysis'][category] = {
                    'count': count,
                    'percentage': percentage,
                    'keywords': keywords,
                    'severity': 'high' if percentage > 20 else 'medium' if percentage > 10 else 'low'
                }
                
                if percentage > 15:  # High complaint rate
                    analysis['common_issues'].append({
                        'category': category,
                        'percentage': percentage,
                        'keywords': keywords
                    })
            
            # Identify performance implications
            for category, data in analysis['category_analysis'].items():
                if data['severity'] == 'high':
                    analysis['performance_implications'].append({
                        'category': category,
                        'implication': f"High complaint rate ({data['percentage']:.1f}%) suggests system weakness in {category}",
                        'recommendation': f"Focus improvement efforts on {category} functionality"
                    })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing complaint patterns: {e}")
            return {'error': str(e)}
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {},
                'trends': {},
                'complaint_analysis': {},
                'recommendations': []
            }
            
            # Overall summary
            if self.performance_history:
                total_records = len(self.performance_history)
                rag_records = [r for r in self.performance_history if r.system_type == 'rag']
                agent_records = [r for r in self.performance_history if r.system_type == 'agent']
                
                report['summary'] = {
                    'total_records': total_records,
                    'rag_records': len(rag_records),
                    'agent_records': len(agent_records),
                    'date_range': {
                        'earliest': min(r.timestamp for r in self.performance_history),
                        'latest': max(r.timestamp for r in self.performance_history)
                    }
                }
            
            # Performance trends
            report['trends'] = {
                'rag_trends': self.get_performance_trends('rag'),
                'agent_trends': self.get_performance_trends('agent'),
                'overall_trends': self.get_performance_trends()
            }
            
            # Complaint analysis
            report['complaint_analysis'] = self.analyze_complaint_patterns()
            
            # Generate recommendations
            if report['trends']['rag_trends'].get('metric_trends'):
                rag_metrics = report['trends']['rag_trends']['metric_trends']
                for metric, trend in rag_metrics.items():
                    if trend['trend_direction'] == 'declining':
                        report['recommendations'].append(f"RAG system showing declining performance in {metric}")
            
            if report['trends']['agent_trends'].get('metric_trends'):
                agent_metrics = report['trends']['agent_trends']['metric_trends']
                for metric, trend in agent_metrics.items():
                    if trend['trend_direction'] == 'improving':
                        report['recommendations'].append(f"Agent system showing improving performance in {metric}")
            
            # Add complaint-based recommendations
            for implication in report['complaint_analysis'].get('performance_implications', []):
                report['recommendations'].append(implication['recommendation'])
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    def display_performance_summary(self) -> None:
        """Display performance summary in a formatted table"""
        try:
            if not self.performance_history:
                console.logger.info("[yellow]No performance data available[/yellow]")
                return
            
            # Create summary table
            table = Table(title="Performance Summary")
            table.add_column("System Type", style="cyan")
            table.add_column("Total Records", style="magenta")
            table.add_column("Latest Avg Faithfulness", style="green")
            table.add_column("Latest Avg Answer Relevancy", style="green")
            table.add_column("Trend", style="yellow")
            
            for system_type in ['rag', 'agent']:
                system_records = [r for r in self.performance_history if r.system_type == system_type]
                
                if system_records:
                    # Get latest records (last 7 days)
                    cutoff_date = datetime.now() - timedelta(days=7)
                    recent_records = [
                        r for r in system_records
                        if datetime.fromisoformat(r.timestamp) > cutoff_date
                    ]
                    
                    if recent_records:
                        # Calculate averages
                        faithfulness_scores = [r.metrics.get('faithfulness', 0) for r in recent_records]
                        relevancy_scores = [r.metrics.get('answer_relevancy', 0) for r in recent_records]
                        
                        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
                        avg_relevancy = sum(relevancy_scores) / len(relevancy_scores)
                        
                        # Determine trend
                        if len(system_records) > 1:
                            latest_faithfulness = faithfulness_scores[-1]
                            earliest_faithfulness = faithfulness_scores[0]
                            trend = "↗️" if latest_faithfulness > earliest_faithfulness else "↘️"
                        else:
                            trend = "➡️"
                        
                        table.add_row(
                            system_type.upper(),
                            str(len(system_records)),
                            f"{avg_faithfulness:.3f}",
                            f"{avg_relevancy:.3f}",
                            trend
                        )
            
            console.print(table)
            
        except Exception as e:
            console.logger.info("[red]Error displaying performance summary: {e}[/red]")
    
    def save_performance_report(self, report: Dict[str, Any], filename: str = None) -> None:
        """Save performance report to file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"performance_report_{timestamp}.json"
            
            output_file = self.evaluation_data_path / filename
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            console.logger.info("[green]Performance report saved to: {output_file}[/green]")
            return output_file
            
        except Exception as e:
            console.logger.info("[red]Error saving performance report: {e}[/red]")
            return None

def main() -> None:
    """Test the performance tracker"""
    tracker = PerformanceTracker()
    
    # Display current performance summary
    tracker.display_performance_summary()
    
    # Generate comprehensive report
    report = tracker.generate_performance_report()
    
    # Save report
    tracker.save_performance_report(report)
    
    console.logger.info("[bold green]Performance tracking completed![/bold green]")

if __name__ == "__main__":
    main() 