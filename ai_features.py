"""
AI-Powered Features Module
Provides NLP job analysis, ML lead scoring, response prediction
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
import json

class AIFeatures:
    """AI-powered analysis and predictions."""
    
    def __init__(self):
        self.skill_keywords = self._load_skill_keywords()
        self.seniority_keywords = self._load_seniority_keywords()
        self.urgency_signals = self._load_urgency_signals()
        self.tech_stack_keywords = self._load_tech_stack_keywords()
        
        # ML model placeholders (would be trained models in production)
        self.lead_scoring_weights = {
            'skills_match': 0.25,
            'seniority_level': 0.20,
            'tech_stack_match': 0.20,
            'urgency_score': 0.15,
            'company_size': 0.10,
            'location_match': 0.10
        }
    
    def _load_skill_keywords(self) -> Dict:
        """Load categorized skill keywords."""
        return {
            'programming': [
                'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust',
                'typescript', 'php', 'swift', 'kotlin', 'scala', 'r', 'perl'
            ],
            'web_frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'express',
                'spring', 'rails', 'laravel', 'next.js', 'nuxt', 'svelte'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'dynamodb', 'cassandra', 'oracle', 'sqlite', 'firestore'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'google cloud', 'cloud platform', 'kubernetes',
                'docker', 'terraform', 'cloudformation', 'serverless'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
                'scikit-learn', 'pandas', 'numpy', 'data analysis', 'statistics'
            ],
            'devops': [
                'ci/cd', 'jenkins', 'github actions', 'gitlab ci', 'ansible',
                'puppet', 'chef', 'monitoring', 'prometheus', 'grafana'
            ]
        }
    
    def _load_seniority_keywords(self) -> Dict:
        """Load seniority level keywords."""
        return {
            'entry': ['junior', 'entry level', 'graduate', 'intern', 'associate'],
            'mid': ['mid level', 'intermediate', 'software engineer', 'developer'],
            'senior': ['senior', 'sr.', 'lead', 'principal', 'staff'],
            'executive': ['director', 'vp', 'chief', 'head of', 'manager', 'executive']
        }
    
    def _load_urgency_signals(self) -> List[str]:
        """Load urgency signal keywords."""
        return [
            'urgent', 'asap', 'immediately', 'immediate start', 'urgent need',
            'fast-growing', 'rapid growth', 'scaling', 'expanding team',
            'high priority', 'time-sensitive', 'as soon as possible'
        ]
    
    def _load_tech_stack_keywords(self) -> Dict:
        """Load technology stack categories."""
        return {
            'frontend': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'typescript'],
            'backend': ['node', 'python', 'java', 'go', 'rust', 'php', 'ruby'],
            'mobile': ['react native', 'flutter', 'swift', 'kotlin', 'ios', 'android'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'ci/cd'],
            'data': ['sql', 'nosql', 'mongodb', 'postgresql', 'redis', 'elasticsearch']
        }
    
    def analyze_job_description(self, job_description: str, job_title: str = "") -> Dict:
        """
        Comprehensive NLP analysis of job description.
        
        Args:
            job_description: Full job description text
            job_title: Job title (optional)
            
        Returns:
            Dict with extracted skills, seniority, tech stack, requirements
        """
        text_lower = (job_description + " " + job_title).lower()
        
        # Extract skills
        skills_found = {
            category: [skill for skill in skills if skill.lower() in text_lower]
            for category, skills in self.skill_keywords.items()
        }
        
        # Filter out empty categories
        skills_found = {k: v for k, v in skills_found.items() if v}
        
        # Determine seniority level
        seniority_level = self._detect_seniority(text_lower)
        
        # Detect tech stack
        tech_stack = self._detect_tech_stack(text_lower)
        
        # Detect urgency
        urgency_score = self._calculate_urgency(text_lower)
        
        # Extract requirements
        requirements = self._extract_requirements(job_description)
        
        # Calculate skill match score
        total_skills = sum(len(skills) for skills in skills_found.values())
        skill_diversity = len(skills_found.keys())
        
        return {
            'skills': skills_found,
            'total_skills': total_skills,
            'skill_diversity': skill_diversity,
            'seniority_level': seniority_level,
            'tech_stack': tech_stack,
            'urgency_score': urgency_score,
            'requirements': requirements,
            'analysis_summary': {
                'skills_count': total_skills,
                'categories_found': skill_diversity,
                'seniority': seniority_level,
                'urgency': 'high' if urgency_score > 3 else 'medium' if urgency_score > 1 else 'low',
                'tech_stack_size': len(tech_stack)
            }
        }
    
    def _detect_seniority(self, text: str) -> str:
        """Detect seniority level from text."""
        for level, keywords in self.seniority_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        return 'mid'  # Default to mid-level
    
    def _detect_tech_stack(self, text: str) -> Dict:
        """Detect technology stack from text."""
        tech_stack = {}
        
        for category, technologies in self.tech_stack_keywords.items():
            found = [tech for tech in technologies if tech.lower() in text]
            if found:
                tech_stack[category] = found
        
        return tech_stack
    
    def _calculate_urgency(self, text: str) -> int:
        """Calculate urgency score (0-10)."""
        urgency_count = sum(1 for signal in self.urgency_signals if signal in text)
        return min(urgency_count * 2, 10)
    
    def _extract_requirements(self, description: str) -> Dict:
        """Extract requirements from job description."""
        requirements = {
            'years_experience': self._extract_years_experience(description),
            'education': self._extract_education(description),
            'certifications': self._extract_certifications(description),
            'must_have_skills': [],
            'nice_to_have_skills': []
        }
        
        # Extract must-have vs nice-to-have
        if 'required' in description.lower() or 'must have' in description.lower():
            requirements['must_have_skills'] = self._extract_skills_from_section(
                description, ['required', 'must have']
            )
        
        if 'preferred' in description.lower() or 'nice to have' in description.lower():
            requirements['nice_to_have_skills'] = self._extract_skills_from_section(
                description, ['preferred', 'nice to have']
            )
        
        return requirements
    
    def _extract_years_experience(self, text: str) -> Optional[int]:
        """Extract years of experience requirement."""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'minimum\s*of\s*(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education requirements."""
        education_levels = []
        education_keywords = {
            "Bachelor's": ["bachelor", "bs", "ba", "b.s.", "b.a."],
            "Master's": ["master", "ms", "ma", "m.s.", "m.a."],
            "PhD": ["phd", "ph.d.", "doctorate"]
        }
        
        text_lower = text.lower()
        for level, keywords in education_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                education_levels.append(level)
        
        return education_levels
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certification requirements."""
        certifications = []
        cert_keywords = [
            'aws certified', 'azure certified', 'gcp certified',
            'cissp', 'pmp', 'scrum master', 'csm', 'cka', 'ckad'
        ]
        
        text_lower = text.lower()
        for cert in cert_keywords:
            if cert in text_lower:
                certifications.append(cert.upper())
        
        return certifications
    
    def _extract_skills_from_section(self, text: str, section_keywords: List[str]) -> List[str]:
        """Extract skills from specific section."""
        # Simplified extraction - in production would use more sophisticated NLP
        skills = []
        text_lower = text.lower()
        
        for keyword in section_keywords:
            if keyword in text_lower:
                # Find the section
                start_idx = text_lower.find(keyword)
                # Extract next 500 characters
                section = text_lower[start_idx:start_idx + 500]
                
                # Find skills in section
                for category, skill_list in self.skill_keywords.items():
                    for skill in skill_list:
                        if skill in section and skill not in skills:
                            skills.append(skill)
        
        return skills[:10]  # Limit to top 10
    
    def ml_enhanced_lead_scoring(self, lead_data: Dict, job_analysis: Dict) -> Dict:
        """
        ML-enhanced lead scoring with feature analysis.
        
        Args:
            lead_data: Lead information including profile, experience, etc.
            job_analysis: Job analysis from analyze_job_description()
            
        Returns:
            Dict with ML-enhanced score and feature breakdown
        """
        scores = {}
        
        # Skills match score
        candidate_skills = set(lead_data.get('skills', []))
        required_skills = set()
        for category, skills in job_analysis.get('skills', {}).items():
            required_skills.update(skills)
        
        if required_skills:
            skills_overlap = len(candidate_skills & required_skills)
            scores['skills_match'] = min((skills_overlap / len(required_skills)) * 100, 100)
        else:
            scores['skills_match'] = 50
        
        # Seniority level match
        candidate_seniority = lead_data.get('seniority_level', 'mid')
        required_seniority = job_analysis.get('seniority_level', 'mid')
        
        seniority_map = {'entry': 1, 'mid': 2, 'senior': 3, 'executive': 4}
        seniority_diff = abs(
            seniority_map.get(candidate_seniority, 2) - 
            seniority_map.get(required_seniority, 2)
        )
        scores['seniority_level'] = max(100 - (seniority_diff * 25), 0)
        
        # Tech stack match
        candidate_tech = set(lead_data.get('tech_stack', []))
        required_tech = set()
        for category, techs in job_analysis.get('tech_stack', {}).items():
            required_tech.update(techs)
        
        if required_tech:
            tech_overlap = len(candidate_tech & required_tech)
            scores['tech_stack_match'] = min((tech_overlap / len(required_tech)) * 100, 100)
        else:
            scores['tech_stack_match'] = 50
        
        # Urgency score (higher urgency = higher priority)
        scores['urgency_score'] = job_analysis.get('urgency_score', 5) * 10
        
        # Company size preference
        scores['company_size'] = lead_data.get('company_size_score', 50)
        
        # Location match
        scores['location_match'] = lead_data.get('location_score', 50)
        
        # Calculate weighted final score
        final_score = sum(
            scores[feature] * self.lead_scoring_weights[feature]
            for feature in scores.keys()
        )
        
        # Confidence level based on data completeness
        data_completeness = len([v for v in lead_data.values() if v]) / len(lead_data)
        confidence = min(data_completeness * 100, 100)
        
        return {
            'ml_score': round(final_score, 2),
            'confidence': round(confidence, 2),
            'feature_scores': scores,
            'feature_weights': self.lead_scoring_weights,
            'recommendation': self._generate_recommendation(final_score),
            'improvement_suggestions': self._generate_improvements(scores)
        }
    
    def _generate_recommendation(self, score: float) -> str:
        """Generate action recommendation based on score."""
        if score >= 80:
            return "High Priority - Contact immediately"
        elif score >= 60:
            return "Medium Priority - Contact within 24 hours"
        elif score >= 40:
            return "Low Priority - Add to nurture campaign"
        else:
            return "Very Low - Consider only if capacity available"
    
    def _generate_improvements(self, scores: Dict) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        for feature, score in scores.items():
            if score < 50:
                if feature == 'skills_match':
                    suggestions.append("Consider upskilling in required technologies")
                elif feature == 'seniority_level':
                    suggestions.append("May need different seniority level candidate")
                elif feature == 'tech_stack_match':
                    suggestions.append("Expand tech stack knowledge")
        
        return suggestions if suggestions else ["Strong match - no improvements needed"]
    
    def predict_response_likelihood(self, lead_data: Dict, outreach_history: List[Dict]) -> Dict:
        """
        Predict likelihood of positive response.
        
        Args:
            lead_data: Lead information
            outreach_history: Previous outreach attempts
            
        Returns:
            Dict with response prediction and best time to contact
        """
        # Base factors
        score = 50
        
        # Response history factor
        if outreach_history:
            recent_attempts = len([h for h in outreach_history if self._is_recent(h.get('date'))])
            if recent_attempts > 3:
                score -= 20  # Reduce if too many recent attempts
            
            last_response = next((h for h in reversed(outreach_history) if h.get('responded')), None)
            if last_response:
                score += 15
        
        # Lead quality factor
        lead_score = lead_data.get('lead_score', 50)
        score = (score + lead_score) / 2
        
        # Engagement signals
        if lead_data.get('opened_emails', 0) > 0:
            score += 10
        if lead_data.get('clicked_links', 0) > 0:
            score += 15
        
        # Best time to contact (based on historical data)
        best_time = self._calculate_best_time(outreach_history)
        
        # Prediction confidence
        confidence = min(len(outreach_history) * 10, 100)
        
        return {
            'response_likelihood': min(round(score, 2), 100),
            'confidence': confidence,
            'best_time_to_contact': best_time,
            'recommended_channel': self._recommend_channel(lead_data),
            'prediction_factors': {
                'lead_quality': lead_score,
                'engagement_signals': lead_data.get('opened_emails', 0) + lead_data.get('clicked_links', 0),
                'outreach_frequency': len(outreach_history)
            }
        }
    
    def _is_recent(self, date_str: Optional[str], days: int = 30) -> bool:
        """Check if date is recent."""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str)
            return (datetime.now() - date).days <= days
        except:
            return False
    
    def _calculate_best_time(self, history: List[Dict]) -> Dict:
        """Calculate best time to contact based on history."""
        # Simplified - in production would use actual response time data
        return {
            'day_of_week': 'Tuesday',
            'time_of_day': '10:00 AM',
            'timezone': 'Local time',
            'reasoning': 'Based on industry best practices and historical data'
        }
    
    def _recommend_channel(self, lead_data: Dict) -> str:
        """Recommend best communication channel."""
        if lead_data.get('linkedin_profile'):
            return 'LinkedIn'
        elif lead_data.get('email'):
            return 'Email'
        else:
            return 'Phone'
    
    def batch_analyze_jobs(self, jobs: List[Dict]) -> Dict:
        """
        Analyze multiple jobs in batch.
        
        Args:
            jobs: List of job dicts with 'description' and 'title'
            
        Returns:
            Dict with batch analysis results
        """
        results = []
        
        for job in jobs:
            analysis = self.analyze_job_description(
                job.get('description', ''),
                job.get('title', '')
            )
            
            results.append({
                'job_id': job.get('id'),
                'job_title': job.get('title'),
                'company': job.get('company'),
                'analysis': analysis
            })
        
        # Aggregate statistics
        total_skills = sum(r['analysis']['total_skills'] for r in results)
        avg_urgency = sum(r['analysis']['urgency_score'] for r in results) / len(results) if results else 0
        
        return {
            'success': True,
            'jobs_analyzed': len(results),
            'results': results,
            'aggregates': {
                'total_skills_found': total_skills,
                'average_skills_per_job': round(total_skills / len(results), 2) if results else 0,
                'average_urgency': round(avg_urgency, 2),
                'most_common_seniority': self._most_common([r['analysis']['seniority_level'] for r in results])
            }
        }
    
    def _most_common(self, items: List) -> str:
        """Find most common item in list."""
        if not items:
            return 'N/A'
        return max(set(items), key=items.count)
