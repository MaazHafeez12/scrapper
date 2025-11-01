"""
Professional Outreach Templates for Business Development
Automated email sequences, personalization engine, and response tracking
"""
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import random

@dataclass
class OutreachTemplate:
    """Template for outreach messages."""
    id: str
    name: str
    subject: str
    body: str
    follow_up_days: int
    template_type: str  # 'initial', 'follow_up', 'value_add', 'final'
    industry_specific: bool = False
    target_role: Optional[str] = None

class OutreachPersonalization:
    """Personalization engine for outreach messages."""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.personalization_data = {}
    
    def _load_templates(self) -> List[OutreachTemplate]:
        """Load predefined outreach templates."""
        templates = [
            # Initial Contact Templates
            OutreachTemplate(
                id="initial_tech_partner",
                name="Tech Partnership Introduction",
                subject="Partnership Opportunity - {company_name} Technology Initiatives",
                body="""Hi {contact_name},

I hope this message finds you well. I noticed {company_name} is actively hiring for {job_title} roles, which suggests exciting growth in your technology team.

I'm reaching out because we specialize in providing dedicated development teams and technical solutions that complement in-house engineering efforts. Instead of competing with your hiring process, we partner with companies like {company_name} to:

• Accelerate project delivery with specialized expertise
• Provide immediate technical capacity during scaling phases  
• Offer flexible engagement models that adapt to your needs

{company_specific_insight}

Would you be open to a brief 15-minute conversation about how we could support {company_name}'s technology initiatives? I'd love to learn more about your current priorities and share how we've helped similar {company_size} companies achieve their goals.

Best regards,
{sender_name}
{sender_title}
{company_name}
{contact_info}

P.S. {personalized_ps}""",
                follow_up_days=7,
                template_type="initial"
            ),
            
            OutreachTemplate(
                id="initial_startup_focus",
                name="Startup-Focused Partnership",
                subject="Scaling {company_name}'s Engineering Team - Partnership Opportunity",
                body="""Hi {contact_name},

As a {contact_title} at {company_name}, you're likely focused on scaling your engineering capabilities efficiently. I noticed you're hiring for {job_title} positions, which is a great sign of growth!

We work exclusively with high-growth startups to provide:
• Dedicated development teams that integrate seamlessly with your culture
• Specialized expertise in {tech_stack} and modern development practices
• Flexible scaling that matches your funding cycles and growth phases

{company_specific_insight}

What makes us different? We've helped {similar_company_count}+ startups like yours build scalable technical solutions without the overhead of traditional hiring.

I'd love to share a brief case study of how we helped [Similar Company] accelerate their product development by 40%. Would you have 10 minutes this week for a quick call?

Best,
{sender_name}
{sender_title}
{contact_info}""",
                follow_up_days=5,
                template_type="initial",
                target_role="startup"
            ),
            
            # Follow-up Templates
            OutreachTemplate(
                id="follow_up_value_add",
                name="Value-Add Follow-up",
                subject="Re: Partnership Opportunity + Free Resource for {company_name}",
                body="""Hi {contact_name},

I wanted to follow up on my previous message about supporting {company_name}'s technology initiatives. I understand you're incredibly busy, especially with ongoing {job_title} hiring.

In the spirit of being helpful regardless, I've attached a resource that might interest you:

{value_add_resource}

This came to mind because of {company_name}'s focus on {company_focus_area}. No strings attached - just thought it might be useful for your team.

If you'd ever like to explore how we could support your engineering efforts, I'm just an email away. Otherwise, I hope this resource proves valuable!

Best regards,
{sender_name}

P.S. {follow_up_ps}""",
                follow_up_days=10,
                template_type="follow_up"
            ),
            
            OutreachTemplate(
                id="follow_up_case_study",
                name="Case Study Follow-up",
                subject="How [Similar Company] Scaled Their {tech_focus} Team by 300%",
                body="""Hi {contact_name},

I hope you don't mind the follow-up. I wanted to share a quick success story that's relevant to {company_name}'s growth trajectory.

We recently helped [Similar Company], a {similar_company_size} company in the {industry} space, scale their {tech_focus} capabilities from 3 to 12 engineers in just 4 months - without the typical hiring headaches.

Key results:
• {metric_1}
• {metric_2}  
• {metric_3}

The approach was straightforward: instead of competing with their internal hiring, we provided dedicated teams that integrated directly with their existing processes.

Given {company_name}'s active hiring for {job_title} roles, this might be relevant to your scaling strategy. 

Would you be interested in a 10-minute overview of the approach? Happy to share more details if it's helpful.

Best,
{sender_name}
{contact_info}""",
                follow_up_days=14,
                template_type="follow_up"
            ),
            
            # Value-Add Templates
            OutreachTemplate(
                id="value_add_industry_insights",
                name="Industry Insights Share",
                subject="2024 {industry} Tech Hiring Trends - Insights for {company_name}",
                body="""Hi {contact_name},

I've been analyzing hiring trends in the {industry} space and thought you might find these insights interesting, especially given {company_name}'s active recruitment for {job_title} positions:

{industry_insights}

These trends suggest that companies like {company_name} who are scaling engineering teams are facing similar challenges around {challenge_area}.

If these insights resonate with your experience, I'd love to hear your perspective. We work with several {industry} companies and often share learnings across our partner network.

No agenda here - just thought this might be useful context for your planning.

Best regards,
{sender_name}
{sender_title}

P.S. If you'd ever like to discuss strategies for scaling technical teams efficiently, I'm always happy to chat!""",
                follow_up_days=21,
                template_type="value_add"
            ),
            
            # Final Touch Templates
            OutreachTemplate(
                id="final_soft_close",
                name="Soft Final Touch",
                subject="Last note - {company_name} partnership opportunity",
                body="""Hi {contact_name},

I don't want to keep bothering you, so this will be my last note about potential partnership opportunities with {company_name}.

I understand timing isn't always right, and that's completely fine. If circumstances change and you'd like to explore how dedicated development teams could support your scaling efforts, you know where to find me.

In the meantime, I wish you and the {company_name} team all the best with your {job_title} hiring and continued growth!

Feel free to reach out anytime if I can be helpful.

Best regards,
{sender_name}
{sender_title}
{contact_info}""",
                follow_up_days=30,
                template_type="final"
            )
        ]
        
        return templates
    
    def personalize_message(self, template: OutreachTemplate, lead_data: Dict, sender_data: Dict) -> Dict:
        """Personalize a template with lead and sender data."""
        try:
            # Extract personalization variables
            company_name = lead_data.get('company', 'Your Company')
            job_title = lead_data.get('title', 'technical roles')
            contact_name = lead_data.get('contact_name', 'there')
            contact_title = lead_data.get('contact_title', '')
            company_size = lead_data.get('company_size', 'growing')
            tech_stack = lead_data.get('tech_stack', 'modern technologies')
            platform = lead_data.get('platform', 'LinkedIn')
            lead_score = lead_data.get('lead_score', 50)
            
            # Sender information
            sender_name = sender_data.get('name', 'John Smith')
            sender_title = sender_data.get('title', 'Business Development')
            sender_company = sender_data.get('company', 'Tech Solutions Inc')
            sender_email = sender_data.get('email', 'contact@techsolutions.com')
            sender_phone = sender_data.get('phone', '+1 (555) 123-4567')
            
            # Generate dynamic content
            company_specific_insight = self._generate_company_insight(lead_data)
            personalized_ps = self._generate_personalized_ps(lead_data)
            value_add_resource = self._generate_value_add_resource(lead_data)
            industry_insights = self._generate_industry_insights(lead_data)
            
            # Contact info formatting
            contact_info = f"📧 {sender_email}\\n📱 {sender_phone}"
            
            # Personalization variables
            variables = {
                'company_name': company_name,
                'job_title': job_title,
                'contact_name': contact_name,
                'contact_title': contact_title,
                'company_size': company_size.lower(),
                'tech_stack': tech_stack,
                'platform': platform,
                'sender_name': sender_name,
                'sender_title': sender_title,
                'sender_company': sender_company,
                'contact_info': contact_info,
                'company_specific_insight': company_specific_insight,
                'personalized_ps': personalized_ps,
                'value_add_resource': value_add_resource,
                'industry_insights': industry_insights,
                'similar_company_count': random.randint(15, 30),
                'tech_focus': self._extract_tech_focus(tech_stack),
                'company_focus_area': self._generate_focus_area(lead_data),
                'follow_up_ps': self._generate_follow_up_ps(lead_data),
                'industry': self._extract_industry(lead_data),
                'similar_company_size': company_size.lower(),
                'metric_1': self._generate_metric(),
                'metric_2': self._generate_metric(),
                'metric_3': self._generate_metric(),
                'challenge_area': self._generate_challenge_area(lead_data)
            }
            
            # Apply personalization
            personalized_subject = template.subject.format(**variables)
            personalized_body = template.body.format(**variables)
            
            return {
                'template_id': template.id,
                'template_name': template.name,
                'subject': personalized_subject,
                'body': personalized_body,
                'follow_up_days': template.follow_up_days,
                'template_type': template.template_type,
                'personalization_score': self._calculate_personalization_score(lead_data, variables),
                'variables_used': list(variables.keys()),
                'send_timing': self._suggest_send_timing(lead_data),
                'follow_up_date': (datetime.now() + timedelta(days=template.follow_up_days)).strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            print(f"Error personalizing message: {e}")
            return {
                'error': str(e),
                'template_id': template.id
            }
    
    def _generate_company_insight(self, lead_data: Dict) -> str:
        """Generate company-specific insight based on lead data."""
        insights = [
            f"I noticed {lead_data.get('company', 'your company')} is focusing on {lead_data.get('tech_stack', 'modern technologies')}, which aligns perfectly with our expertise.",
            f"Your recent growth in {lead_data.get('title', 'technical roles')} suggests exciting product development ahead.",
            f"Given {lead_data.get('company', 'your company')}'s {lead_data.get('company_size', 'growing')} nature, you likely value partners who can scale with your needs.",
            f"I see {lead_data.get('company', 'your company')} is building out capabilities in {lead_data.get('tech_stack', 'key technologies')} - that's exactly where we excel."
        ]
        
        return random.choice(insights)
    
    def _generate_personalized_ps(self, lead_data: Dict) -> str:
        """Generate personalized P.S. based on lead data."""
        ps_options = [
            f"I'd be happy to share how we've helped other {lead_data.get('company_size', 'growing')} companies navigate similar growth phases.",
            f"Feel free to check out our case studies with companies using {lead_data.get('tech_stack', 'similar technologies')}.",
            f"If timing isn't right now, I understand - happy to reconnect when it makes more sense.",
            f"I'm also curious about your experience scaling {lead_data.get('tech_stack', 'technical')} teams."
        ]
        
        return random.choice(ps_options)
    
    def _generate_value_add_resource(self, lead_data: Dict) -> str:
        """Generate relevant value-add resource."""
        resources = [
            f"\"Scaling {lead_data.get('tech_stack', 'Technical')} Teams: A Growth Framework\" - A practical guide we developed for {lead_data.get('company_size', 'growing')} companies",
            f"\"Remote Team Integration Playbook\" - Since you're hiring for {lead_data.get('title', 'technical roles')}, this covers best practices for onboarding distributed talent",
            f"\"Technology ROI Calculator\" - Helps quantify the impact of different scaling approaches for technical teams",
            f"\"Hiring vs. Partnership Decision Matrix\" - A framework for determining the best approach to scale engineering capacity"
        ]
        
        return random.choice(resources)
    
    def _generate_industry_insights(self, lead_data: Dict) -> str:
        """Generate industry-specific insights."""
        base_insights = f"""
Key findings from our analysis of 200+ {lead_data.get('company_size', 'growing')} companies:

• Average time-to-hire for {lead_data.get('title', 'technical roles')} has increased 40% in 2024
• Companies using hybrid hiring + partnership models scale 60% faster
• {lead_data.get('tech_stack', 'Technical')} expertise is among the most in-demand skills
• Cost-per-hire continues rising while project timelines compress"""
        
        return base_insights.strip()
    
    def _extract_tech_focus(self, tech_stack: str) -> str:
        """Extract primary technology focus."""
        if 'python' in tech_stack.lower():
            return 'Python/Backend'
        elif 'react' in tech_stack.lower() or 'javascript' in tech_stack.lower():
            return 'Frontend/React'
        elif 'aws' in tech_stack.lower() or 'cloud' in tech_stack.lower():
            return 'Cloud/DevOps'
        else:
            return 'Full-Stack'
    
    def _generate_focus_area(self, lead_data: Dict) -> str:
        """Generate company focus area."""
        areas = [
            'technical innovation',
            'product development',
            'engineering excellence',
            'scalable architecture',
            'rapid growth',
            'market expansion'
        ]
        return random.choice(areas)
    
    def _generate_follow_up_ps(self, lead_data: Dict) -> str:
        """Generate follow-up P.S."""
        options = [
            f"I'm genuinely curious about {lead_data.get('company', 'your')} approach to scaling technical teams.",
            f"Always happy to share insights from working with other {lead_data.get('company_size', 'growing')} companies.",
            f"No pressure at all - just thought this might be relevant to your current initiatives."
        ]
        return random.choice(options)
    
    def _extract_industry(self, lead_data: Dict) -> str:
        """Extract or guess industry from lead data."""
        company = lead_data.get('company', '').lower()
        title = lead_data.get('title', '').lower()
        
        if any(word in company + title for word in ['fintech', 'finance', 'bank']):
            return 'fintech'
        elif any(word in company + title for word in ['health', 'medical', 'bio']):
            return 'healthtech'
        elif any(word in company + title for word in ['edu', 'learn', 'school']):
            return 'edtech'
        else:
            return 'technology'
    
    def _generate_metric(self) -> str:
        """Generate realistic success metrics."""
        metrics = [
            "40% faster time-to-market for new features",
            "60% reduction in technical hiring stress",
            "25% lower cost per delivered feature",
            "90% team satisfaction with partnership model",
            "50% improvement in delivery predictability",
            "35% faster sprint velocity"
        ]
        return random.choice(metrics)
    
    def _generate_challenge_area(self, lead_data: Dict) -> str:
        """Generate relevant challenge area."""
        challenges = [
            'finding qualified technical talent',
            'scaling development capacity quickly',
            'maintaining code quality during rapid growth',
            'balancing in-house vs external resources'
        ]
        return random.choice(challenges)
    
    def _calculate_personalization_score(self, lead_data: Dict, variables: Dict) -> int:
        """Calculate how well personalized the message is."""
        score = 50  # Base score
        
        # Add points for data availability
        if lead_data.get('company'):
            score += 10
        if lead_data.get('title'):
            score += 10
        if lead_data.get('contact_name') and lead_data.get('contact_name') != 'there':
            score += 15
        if lead_data.get('tech_stack') and lead_data.get('tech_stack') != 'General':
            score += 10
        if lead_data.get('company_size') and lead_data.get('company_size') != 'Unknown':
            score += 5
        
        return min(score, 100)
    
    def _suggest_send_timing(self, lead_data: Dict) -> Dict:
        """Suggest optimal send timing."""
        # Basic timing suggestions
        suggestions = {
            'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
            'best_hours': ['9:00 AM', '2:00 PM'],
            'avoid_days': ['Monday', 'Friday'],
            'timezone_note': 'Consider company location for timing'
        }
        
        # Adjust based on company size
        if lead_data.get('company_size') == 'Startup':
            suggestions['best_hours'] = ['10:00 AM', '3:00 PM', '7:00 PM']
            suggestions['timing_note'] = 'Startups often check email outside traditional hours'
        
        return suggestions
    
    def get_outreach_sequence(self, lead_data: Dict, sender_data: Dict) -> List[Dict]:
        """Generate complete outreach sequence for a lead."""
        sequence = []
        
        # Determine appropriate templates based on lead characteristics
        if lead_data.get('company_size') == 'Startup':
            initial_template = next(t for t in self.templates if t.id == 'initial_startup_focus')
        else:
            initial_template = next(t for t in self.templates if t.id == 'initial_tech_partner')
        
        # Build sequence
        template_sequence = [
            initial_template,
            next(t for t in self.templates if t.id == 'follow_up_value_add'),
            next(t for t in self.templates if t.id == 'follow_up_case_study'),
            next(t for t in self.templates if t.id == 'value_add_industry_insights'),
            next(t for t in self.templates if t.id == 'final_soft_close')
        ]
        
        for template in template_sequence:
            personalized = self.personalize_message(template, lead_data, sender_data)
            sequence.append(personalized)
        
        return sequence
    
    def get_template_recommendations(self, lead_data: Dict) -> List[str]:
        """Recommend best templates for a specific lead."""
        recommendations = []
        
        # Score-based recommendations
        lead_score = lead_data.get('lead_score', 50)
        company_size = lead_data.get('company_size', 'Unknown')
        
        if lead_score >= 80:
            recommendations.append("High-value lead: Use detailed case study approach")
        elif lead_score >= 60:
            recommendations.append("Strong lead: Focus on partnership benefits")
        else:
            recommendations.append("Develop lead: Start with value-add approach")
        
        if company_size == 'Startup':
            recommendations.append("Startup focus: Emphasize flexibility and growth support")
        elif company_size == 'Enterprise':
            recommendations.append("Enterprise focus: Highlight scalability and proven results")
        
        return recommendations

# Singleton instance
outreach_personalizer = OutreachPersonalization()