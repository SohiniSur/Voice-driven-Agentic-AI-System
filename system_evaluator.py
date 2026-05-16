"""
Comprehensive Evaluation Framework for Voice Form Filling System
30 User Trial Study
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

class SystemEvaluator:
    """
    Comprehensive evaluation framework for voice form filling user study
    """
    
    def __init__(self, output_dir="evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.participants = []
        self.metrics = {
            'quantitative': [],
            'qualitative': [],
            'errors': []
        }
    
    
    # ============================================
    # QUANTITATIVE METRICS
    # ============================================
    
    def collect_quantitative_metrics(self, participant_id: str, data: dict):
        """
        Collect objective metrics for each trial
        
        Required data fields:
        - task_completion: bool
        - completion_time: float (seconds)
        - dialogue_turns: int
        - asr_errors: int
        - field_errors: int
        - corrections_needed: int
        - api_calls_used: int
        """
        
        metrics = {
            'participant_id': participant_id,
            'timestamp': datetime.now().isoformat(),
            
            # Primary Metrics
            'task_completed': data['task_completion'],
            'completion_time_seconds': data['completion_time'],
            'completion_time_minutes': data['completion_time'] / 60,
            
            # Efficiency Metrics
            'total_dialogue_turns': data['dialogue_turns'],
            'turns_per_field': data['dialogue_turns'] / data.get('num_fields', 10),
            'avg_time_per_field': data['completion_time'] / data.get('num_fields', 10),
            
            # Error Metrics
            'asr_errors': data['asr_errors'],
            'field_errors': data['field_errors'],
            'total_corrections': data['corrections_needed'],
            'error_recovery_success_rate': data.get('errors_recovered', 0) / max(data['field_errors'], 1),
            
            # System Metrics
            'api_calls_used': data['api_calls_used'],
            
            # Derived Metrics
            'success': 1 if data['task_completion'] else 0,
            'errors_per_field': (data['asr_errors'] + data['field_errors']) / data.get('num_fields', 10)
        }
        
        self.metrics['quantitative'].append(metrics)
        
        print(f"✓ Collected quantitative metrics for {participant_id}")
        return metrics
    
    
    def collect_sus_score(self, participant_id: str, responses: list):
        """
        Calculate System Usability Scale (SUS) score
        
        Args:
            responses: List of 10 responses (1-5 scale)
                Q1: I think I would like to use this system frequently
                Q2: I found the system unnecessarily complex
                Q3: I thought the system was easy to use
                Q4: I think I would need support to use this system
                Q5: I found the various functions well integrated
                Q6: I thought there was too much inconsistency
                Q7: I would imagine most people would learn quickly
                Q8: I found the system very cumbersome to use
                Q9: I felt very confident using the system
                Q10: I needed to learn a lot before I could use this
        
        Returns:
            SUS score (0-100)
        """
        
        if len(responses) != 10:
            raise ValueError("SUS requires exactly 10 responses")
        
        # Calculate SUS score
        score = 0
        
        # Odd items (1,3,5,7,9): contribution = response - 1
        for i in [0, 2, 4, 6, 8]:
            score += (responses[i] - 1)
        
        # Even items (2,4,6,8,10): contribution = 5 - response
        for i in [1, 3, 5, 7, 9]:
            score += (5 - responses[i])
        
        # Multiply by 2.5 to get score out of 100
        sus_score = score * 2.5
        
        # Find matching participant
        for metrics in self.metrics['quantitative']:
            if metrics['participant_id'] == participant_id:
                metrics['sus_score'] = sus_score
                break
        
        print(f"✓ SUS Score for {participant_id}: {sus_score:.1f}/100")
        return sus_score
    
    
    # ============================================
    # QUALITATIVE METRICS
    # ============================================
    
    def collect_qualitative_feedback(self, participant_id: str, feedback: dict):
        """
        Collect subjective feedback
        
        feedback dict should include:
        - overall_satisfaction: 1-5 scale
        - ease_of_use: 1-5 scale
        - voice_clarity: 1-5 scale
        - error_handling: 1-5 scale
        - trust_in_system: 1-5 scale
        - would_recommend: bool
        - liked_most: str
        - liked_least: str
        - suggestions: str
        - difficulties_faced: list[str]
        """
        
        qualitative = {
            'participant_id': participant_id,
            'timestamp': datetime.now().isoformat(),
            **feedback
        }
        
        self.metrics['qualitative'].append(qualitative)
        
        print(f"✓ Collected qualitative feedback for {participant_id}")
        return qualitative
    
    
    def collect_error_log(self, participant_id: str, errors: list):
        """
        Log all errors encountered during session
        
        Each error should be a dict with:
        - error_type: 'asr', 'validation', 'system', 'user_confusion'
        - field_name: str
        - description: str
        - resolved: bool
        - resolution_turns: int
        """
        
        for error in errors:
            error_entry = {
                'participant_id': participant_id,
                'timestamp': datetime.now().isoformat(),
                **error
            }
            self.metrics['errors'].append(error_entry)
        
        print(f"✓ Logged {len(errors)} errors for {participant_id}")
    
    
    # ============================================
    # DEMOGRAPHIC DATA
    # ============================================
    
    def add_participant(self, participant_data: dict):
        """
        Add participant demographic info
        
        Required fields:
        - participant_id: str
        - age: int
        - gender: str
        - education: str ('none', 'primary', 'secondary', 'higher')
        - location: str ('urban', 'rural')
        - primary_language: str
        - digital_literacy: str ('low', 'medium', 'high')
        - prior_voice_assistant_use: bool
        """
        
        self.participants.append(participant_data)
        print(f"✓ Added participant: {participant_data['participant_id']}")
    
    
    # ============================================
    # ANALYSIS & REPORTING
    # ============================================
    
    def analyze_results(self):
        """Generate comprehensive analysis"""
        
        df_quant = pd.DataFrame(self.metrics['quantitative'])
        df_qual = pd.DataFrame(self.metrics['qualitative'])
        df_errors = pd.DataFrame(self.metrics['errors'])
        df_participants = pd.DataFrame(self.participants)
        
        # Merge participant demographics
        df_full = df_quant.merge(df_participants, on='participant_id', how='left')
        
        analysis = {
            'overall_stats': self._analyze_overall(df_full),
            'by_demographic': self._analyze_by_demographic(df_full),
            'error_analysis': self._analyze_errors(df_errors),
            'sus_analysis': self._analyze_sus(df_full),
            'qualitative_summary': self._analyze_qualitative(df_qual)
        }
        
        return analysis
    
    
    def _analyze_overall(self, df):
        """Overall system performance"""
        
        return {
            'completion_rate': {
                'value': df['task_completed'].mean() * 100,
                'count': f"{df['task_completed'].sum()}/{len(df)}"
            },
            'avg_completion_time': {
                'mean': df['completion_time_minutes'].mean(),
                'std': df['completion_time_minutes'].std(),
                'median': df['completion_time_minutes'].median(),
                'min': df['completion_time_minutes'].min(),
                'max': df['completion_time_minutes'].max()
            },
            'avg_dialogue_turns': {
                'mean': df['total_dialogue_turns'].mean(),
                'std': df['total_dialogue_turns'].std(),
                'per_field': df['turns_per_field'].mean()
            },
            'error_rate': {
                'asr_errors_per_form': df['asr_errors'].mean(),
                'field_errors_per_form': df['field_errors'].mean(),
                'total_errors_per_form': (df['asr_errors'] + df['field_errors']).mean()
            },
            'sus_score': {
                'mean': df['sus_score'].mean() if 'sus_score' in df else None,
                'std': df['sus_score'].std() if 'sus_score' in df else None
            }
        }
    
    
    def _analyze_by_demographic(self, df):
        """Performance broken down by demographics"""
        
        analyses = {}
        
        demographic_vars = ['age_group', 'gender', 'education', 
                           'location', 'digital_literacy']
        
        # Create age groups
        if 'age' in df.columns:
            df['age_group'] = pd.cut(df['age'], 
                                    bins=[0, 40, 60, 100], 
                                    labels=['<40', '40-60', '60+'])
        
        for var in demographic_vars:
            if var in df.columns:
                grouped = df.groupby(var).agg({
                    'task_completed': 'mean',
                    'completion_time_minutes': 'mean',
                    'total_dialogue_turns': 'mean',
                    'sus_score': 'mean' if 'sus_score' in df else lambda x: None
                }).round(2)
                
                analyses[var] = grouped.to_dict()
        
        return analyses
    
    
    def _analyze_errors(self, df):
        """Error pattern analysis"""
        
        if df.empty:
            return {}
        
        return {
            'total_errors': len(df),
            'by_type': df['error_type'].value_counts().to_dict(),
            'by_field': df['field_name'].value_counts().to_dict(),
            'resolution_rate': df['resolved'].mean() * 100 if 'resolved' in df else None,
            'avg_resolution_turns': df['resolution_turns'].mean() if 'resolution_turns' in df else None
        }
    
    
    def _analyze_sus(self, df):
        """SUS score analysis"""
        
        if 'sus_score' not in df.columns:
            return None
        
        mean_sus = df['sus_score'].mean()
        
        # SUS interpretation
        if mean_sus >= 80:
            grade = 'A (Excellent)'
        elif mean_sus >= 70:
            grade = 'B (Good)'
        elif mean_sus >= 50:
            grade = 'C (OK)'
        elif mean_sus >= 25:
            grade = 'D (Poor)'
        else:
            grade = 'F (Awful)'
        
        return {
            'mean': mean_sus,
            'std': df['sus_score'].std(),
            'median': df['sus_score'].median(),
            'grade': grade,
            'percentile_ranking': {
                '80+': (df['sus_score'] >= 80).sum(),
                '70-80': ((df['sus_score'] >= 70) & (df['sus_score'] < 80)).sum(),
                '50-70': ((df['sus_score'] >= 50) & (df['sus_score'] < 70)).sum(),
                '<50': (df['sus_score'] < 50).sum()
            }
        }
    
    
    def _analyze_qualitative(self, df):
        """Qualitative feedback summary"""
        
        if df.empty:
            return {}
        
        return {
            'avg_satisfaction': df['overall_satisfaction'].mean() if 'overall_satisfaction' in df else None,
            'would_recommend': df['would_recommend'].mean() * 100 if 'would_recommend' in df else None,
            'common_difficulties': self._extract_common_themes(df['difficulties_faced'].tolist() if 'difficulties_faced' in df else []),
            'liked_most_themes': self._extract_common_themes(df['liked_most'].tolist() if 'liked_most' in df else []),
            'improvement_suggestions': self._extract_common_themes(df['suggestions'].tolist() if 'suggestions' in df else [])
        }
    
    
    def _extract_common_themes(self, text_list):
        """Extract common themes from text responses"""
        # Simple frequency count of words (you could use NLP for better analysis)
        if not text_list:
            return []
        
        all_words = []
        for text in text_list:
            if isinstance(text, str):
                words = text.lower().split()
                all_words.extend(words)
        
        from collections import Counter
        common = Counter(all_words).most_common(10)
        return [word for word, count in common if len(word) > 3]
    
    
    # ============================================
    # VISUALIZATION
    # ============================================
    
    def generate_plots(self):
        """Generate all visualization plots"""
        
        df_quant = pd.DataFrame(self.metrics['quantitative'])
        df_participants = pd.DataFrame(self.participants)
        df_full = df_quant.merge(df_participants, on='participant_id', how='left')
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Completion Rate
        ax1 = fig.add_subplot(gs[0, 0])
        completion_data = df_full['task_completed'].value_counts()
        ax1.pie(completion_data, labels=['Completed', 'Failed'], autopct='%1.1f%%',
               colors=['#2ecc71', '#e74c3c'])
        ax1.set_title('Task Completion Rate')
        
        # Plot 2: Completion Time Distribution
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(df_full['completion_time_minutes'], bins=15, color='steelblue', edgecolor='black')
        ax2.axvline(df_full['completion_time_minutes'].mean(), color='red', 
                   linestyle='--', label=f'Mean: {df_full["completion_time_minutes"].mean():.1f}min')
        ax2.set_xlabel('Completion Time (minutes)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Completion Time Distribution')
        ax2.legend()
        
        # Plot 3: SUS Scores
        if 'sus_score' in df_full.columns:
            ax3 = fig.add_subplot(gs[0, 2])
            ax3.hist(df_full['sus_score'], bins=10, color='coral', edgecolor='black')
            ax3.axvline(df_full['sus_score'].mean(), color='red', linestyle='--',
                       label=f'Mean: {df_full["sus_score"].mean():.1f}')
            ax3.set_xlabel('SUS Score')
            ax3.set_ylabel('Frequency')
            ax3.set_title('System Usability Scale (SUS) Scores')
            ax3.legend()
        
        # Plot 4: Errors by Type
        ax4 = fig.add_subplot(gs[1, 0])
        error_means = df_full[['asr_errors', 'field_errors']].mean()
        ax4.bar(range(len(error_means)), error_means, color=['#3498db', '#e67e22'])
        ax4.set_xticks(range(len(error_means)))
        ax4.set_xticklabels(['ASR Errors', 'Field Errors'])
        ax4.set_ylabel('Average per Form')
        ax4.set_title('Average Errors per Form')
        
        # Plot 5: Performance by Age Group
        if 'age' in df_full.columns:
            ax5 = fig.add_subplot(gs[1, 1])
            df_full['age_group'] = pd.cut(df_full['age'], bins=[0, 40, 60, 100], 
                                          labels=['<40', '40-60', '60+'])
            age_completion = df_full.groupby('age_group')['task_completed'].mean() * 100
            ax5.bar(range(len(age_completion)), age_completion, color='purple', alpha=0.7)
            ax5.set_xticks(range(len(age_completion)))
            ax5.set_xticklabels(age_completion.index)
            ax5.set_ylabel('Completion Rate (%)')
            ax5.set_title('Completion Rate by Age Group')
            ax5.set_ylim([0, 105])
        
        # Plot 6: Dialogue Efficiency
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.scatter(df_full['total_dialogue_turns'], df_full['completion_time_minutes'],
                   alpha=0.6, s=100, c=df_full['task_completed'], cmap='RdYlGn')
        ax6.set_xlabel('Total Dialogue Turns')
        ax6.set_ylabel('Completion Time (minutes)')
        ax6.set_title('Dialogue Efficiency')
        
        # Plot 7: Performance by Digital Literacy
        if 'digital_literacy' in df_full.columns:
            ax7 = fig.add_subplot(gs[2, 0])
            literacy_time = df_full.groupby('digital_literacy')['completion_time_minutes'].mean()
            ax7.bar(range(len(literacy_time)), literacy_time, color='teal', alpha=0.7)
            ax7.set_xticks(range(len(literacy_time)))
            ax7.set_xticklabels(literacy_time.index)
            ax7.set_ylabel('Avg Time (minutes)')
            ax7.set_title('Completion Time by Digital Literacy')
        
        # Plot 8: Urban vs Rural
        if 'location' in df_full.columns:
            ax8 = fig.add_subplot(gs[2, 1])
            location_stats = df_full.groupby('location').agg({
                'task_completed': 'mean',
                'completion_time_minutes': 'mean'
            })
            x = np.arange(len(location_stats))
            width = 0.35
            ax8.bar(x - width/2, location_stats['task_completed'] * 100, width, 
                   label='Completion %', color='green', alpha=0.7)
            ax8_twin = ax8.twinx()
            ax8_twin.bar(x + width/2, location_stats['completion_time_minutes'], width,
                        label='Time (min)', color='orange', alpha=0.7)
            ax8.set_xticks(x)
            ax8.set_xticklabels(location_stats.index)
            ax8.set_ylabel('Completion Rate (%)', color='green')
            ax8_twin.set_ylabel('Time (minutes)', color='orange')
            ax8.set_title('Urban vs Rural Performance')
        
        # Plot 9: API Calls Distribution
        ax9 = fig.add_subplot(gs[2, 2])
        ax9.hist(df_full['api_calls_used'], bins=15, color='gold', edgecolor='black')
        ax9.axvline(df_full['api_calls_used'].mean(), color='red', linestyle='--',
                   label=f'Mean: {df_full["api_calls_used"].mean():.0f}')
        ax9.set_xlabel('API Calls Used')
        ax9.set_ylabel('Frequency')
        ax9.set_title('API Calls Distribution')
        ax9.legend()
        
        plt.suptitle('Voice Form Filling System - Evaluation Results (N=30)', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        # Save figure
        filepath = self.output_dir / 'evaluation_plots.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plots to: {filepath}")
        
        plt.show()
    
    
    # ============================================
    # REPORTING
    # ============================================
    
    def generate_report(self):
        """Generate comprehensive evaluation report"""
        
        analysis = self.analyze_results()
        
        report = f"""
{'='*80}
VOICE FORM FILLING SYSTEM - EVALUATION REPORT
User Study with 30 Participants
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

1. OVERALL PERFORMANCE
{'='*80}

Task Completion Rate: {analysis['overall_stats']['completion_rate']['value']:.1f}% 
                      ({analysis['overall_stats']['completion_rate']['count']})

Average Completion Time: {analysis['overall_stats']['avg_completion_time']['mean']:.1f} ± {analysis['overall_stats']['avg_completion_time']['std']:.1f} minutes
                        (Range: {analysis['overall_stats']['avg_completion_time']['min']:.1f} - {analysis['overall_stats']['avg_completion_time']['max']:.1f} min)

Average Dialogue Turns: {analysis['overall_stats']['avg_dialogue_turns']['mean']:.1f} ± {analysis['overall_stats']['avg_dialogue_turns']['std']:.1f} turns
                       ({analysis['overall_stats']['avg_dialogue_turns']['per_field']:.1f} turns per field)

Error Rates:
  - ASR Errors: {analysis['overall_stats']['error_rate']['asr_errors_per_form']:.1f} per form
  - Field Errors: {analysis['overall_stats']['error_rate']['field_errors_per_form']:.1f} per form
  - Total Errors: {analysis['overall_stats']['error_rate']['total_errors_per_form']:.1f} per form

"""
        
        if analysis['overall_stats']['sus_score']['mean']:
            report += f"""
2. SYSTEM USABILITY SCALE (SUS)
{'='*80}

Mean SUS Score: {analysis['overall_stats']['sus_score']['mean']:.1f}/100
Grade: {analysis['sus_analysis']['grade']}
Interpretation: """
            
            mean_sus = analysis['overall_stats']['sus_score']['mean']
            if mean_sus >= 80:
                report += "Excellent - Users love the system\n"
            elif mean_sus >= 70:
                report += "Good - System is usable with minor issues\n"
            elif mean_sus >= 50:
                report += "OK - Significant improvements needed\n"
            else:
                report += "Poor - Major usability problems\n"
        
        report += f"""

3. DEMOGRAPHIC BREAKDOWN
{'='*80}

Performance by Age Group:
"""
        if 'age_group' in analysis['by_demographic']:
            for age_group, metrics in analysis['by_demographic']['age_group'].items():
                report += f"  {age_group}: {metrics.get('task_completed', 0)*100:.1f}% completion, "
                report += f"{metrics.get('completion_time_minutes', 0):.1f} min avg\n"
        
        report += f"""
Performance by Digital Literacy:
"""
        if 'digital_literacy' in analysis['by_demographic']:
            for literacy, metrics in analysis['by_demographic']['digital_literacy'].items():
                report += f"  {literacy}: {metrics.get('task_completed', 0)*100:.1f}% completion, "
                report += f"{metrics.get('completion_time_minutes', 0):.1f} min avg\n"
        
        report += f"""

4. ERROR ANALYSIS
{'='*80}

Total Errors Logged: {analysis['error_analysis'].get('total_errors', 0)}

Errors by Type:
"""
        if 'by_type' in analysis['error_analysis']:
            for error_type, count in analysis['error_analysis']['by_type'].items():
                report += f"  - {error_type}: {count} ({count/analysis['error_analysis']['total_errors']*100:.1f}%)\n"
        
        report += f"""
Most Problematic Fields:
"""
        if 'by_field' in analysis['error_analysis']:
            for field, count in list(analysis['error_analysis']['by_field'].items())[:5]:
                report += f"  - {field}: {count} errors\n"
        
        report += f"""
Error Resolution Rate: {analysis['error_analysis'].get('resolution_rate', 0):.1f}%
Average Resolution Time: {analysis['error_analysis'].get('avg_resolution_turns', 0):.1f} dialogue turns

{'='*80}
END OF REPORT
{'='*80}
"""
        
        # Save report
        report_file = self.output_dir / 'evaluation_report.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n✓ Saved report to: {report_file}")
        
        return report
    
    
    def export_all_data(self):
        """Export all collected data to CSV files"""
        
        # Quantitative metrics
        df_quant = pd.DataFrame(self.metrics['quantitative'])
        quant_file = self.output_dir / 'quantitative_metrics.csv'
        df_quant.to_csv(quant_file, index=False)
        print(f"✓ Exported quantitative metrics: {quant_file}")
        
        # Qualitative feedback
        df_qual = pd.DataFrame(self.metrics['qualitative'])
        qual_file = self.output_dir / 'qualitative_feedback.csv'
        df_qual.to_csv(qual_file, index=False)
        print(f"✓ Exported qualitative feedback: {qual_file}")
        
        # Error logs
        df_errors = pd.DataFrame(self.metrics['errors'])
        error_file = self.output_dir / 'error_logs.csv'
        df_errors.to_csv(error_file, index=False)
        print(f"✓ Exported error logs: {error_file}")
        
        # Participant demographics
        df_participants = pd.DataFrame(self.participants)
        participant_file = self.output_dir / 'participants.csv'
        df_participants.to_csv(participant_file, index=False)
        print(f"✓ Exported participant data: {participant_file}")
        
        # Combined data
        df_full = df_quant.merge(df_participants, on='participant_id', how='left')
        combined_file = self.output_dir / 'combined_data.csv'
        df_full.to_csv(combined_file, index=False)
        print(f"✓ Exported combined data: {combined_file}")


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    evaluator = SystemEvaluator()
    
    # Example: Adding 3 participants for demonstration
    for i in range(1, 4):
        # Add participant demographic
        evaluator.add_participant({
            'participant_id': f'P{i:03d}',
            'age': 65 + i*5,
            'gender': 'Male' if i % 2 == 0 else 'Female',
            'education': 'primary',
            'location': 'rural' if i % 2 == 0 else 'urban',
            'primary_language': 'Bengali',
            'digital_literacy': 'low',
            'prior_voice_assistant_use': False
        })
        
        # Collect quantitative metrics
        evaluator.collect_quantitative_metrics(
            participant_id=f'P{i:03d}',
            data={
                'task_completion': True,
                'completion_time': 300 + i*30,
                'dialogue_turns': 25 + i*2,
                'asr_errors': 3 + i,
                'field_errors': 2,
                'corrections_needed': 4,
                'errors_recovered': 3,
                'api_calls_used': 58 + i*5,
                'num_fields': 10
            }
        )
        
        # Collect SUS score
        sus_responses = [4, 2, 4, 2, 4, 2, 4, 2, 4, 1]  # Example responses
        evaluator.collect_sus_score(f'P{i:03d}', sus_responses)
        
        # Collect qualitative feedback
        evaluator.collect_qualitative_feedback(
            participant_id=f'P{i:03d}',
            feedback={
                'overall_satisfaction': 4,
                'ease_of_use': 4,
                'voice_clarity': 3,
                'error_handling': 4,
                'trust_in_system': 4,
                'would_recommend': True,
                'liked_most': 'Easy to use with voice',
                'liked_least': 'Sometimes misheard my name',
                'suggestions': 'Make it faster',
                'difficulties_faced': ['name recognition', 'date format']
            }
        )
    
    # Generate analysis
    print("\n" + "="*80)
    print("GENERATING ANALYSIS...")
    print("="*80)
    
    evaluator.generate_report()
    evaluator.generate_plots()
    evaluator.export_all_data()
    
    print("\n✓ Evaluation complete!")
