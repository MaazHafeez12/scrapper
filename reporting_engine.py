"""
Advanced Reporting & Exports Module
Generate PDF/Excel reports, scheduled reports, data exports, custom dashboards
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import csv
from io import StringIO, BytesIO

class ReportingEngine:
    """Advanced reporting and export system."""
    
    def __init__(self):
        self.scheduled_reports = []
        self.report_templates = self._load_report_templates()
        self.export_history = []
    
    def _load_report_templates(self) -> Dict:
        """Load pre-configured report templates."""
        return {
            'executive_summary': {
                'name': 'Executive Summary',
                'sections': ['overview', 'key_metrics', 'top_leads', 'revenue', 'trends'],
                'format': 'pdf',
                'frequency': 'weekly'
            },
            'lead_performance': {
                'name': 'Lead Performance Report',
                'sections': ['lead_sources', 'conversion_rates', 'lead_quality', 'pipeline'],
                'format': 'excel',
                'frequency': 'daily'
            },
            'campaign_analysis': {
                'name': 'Campaign Analysis',
                'sections': ['email_stats', 'engagement', 'ab_tests', 'roi'],
                'format': 'pdf',
                'frequency': 'monthly'
            },
            'sales_pipeline': {
                'name': 'Sales Pipeline Report',
                'sections': ['pipeline_stages', 'deal_velocity', 'forecast', 'bottlenecks'],
                'format': 'excel',
                'frequency': 'weekly'
            }
        }
    
    def generate_report(self,
                       report_type: str,
                       data: Dict,
                       format: str = 'json',
                       include_charts: bool = True) -> Dict:
        """
        Generate comprehensive report.
        
        Args:
            report_type: 'executive_summary', 'lead_performance', 'campaign_analysis', 'sales_pipeline', 'custom'
            data: Report data
            format: 'json', 'csv', 'excel', 'pdf'
            include_charts: Include visualizations
            
        Returns:
            Dict with report content or download link
        """
        report_id = f"report_{int(datetime.now().timestamp())}"
        
        if report_type in self.report_templates:
            template = self.report_templates[report_type]
            report_content = self._build_from_template(template, data)
        else:
            report_content = data
        
        # Add metadata
        report = {
            'report_id': report_id,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'format': format,
            'content': report_content
        }
        
        # Format output based on requested format
        if format == 'json':
            output = report
        elif format == 'csv':
            output = self._format_as_csv(report_content)
        elif format == 'excel':
            output = self._generate_excel_mock(report_content)
        elif format == 'pdf':
            output = self._generate_pdf_mock(report_content)
        else:
            output = report
        
        # Track export
        self.export_history.append({
            'report_id': report_id,
            'report_type': report_type,
            'format': format,
            'generated_at': report['generated_at']
        })
        
        return {
            'success': True,
            'report_id': report_id,
            'report_type': report_type,
            'format': format,
            'data': output,
            'download_url': f'/api/reports/download/{report_id}',
            'generated_at': report['generated_at']
        }
    
    def _build_from_template(self, template: Dict, data: Dict) -> Dict:
        """Build report from template."""
        report_content = {
            'title': template['name'],
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        for section in template['sections']:
            if section == 'overview':
                report_content['sections']['overview'] = {
                    'total_leads': data.get('total_leads', 0),
                    'active_campaigns': data.get('active_campaigns', 0),
                    'conversion_rate': data.get('conversion_rate', 0),
                    'revenue': data.get('revenue', 0)
                }
            elif section == 'key_metrics':
                report_content['sections']['key_metrics'] = {
                    'emails_sent': data.get('emails_sent', 0),
                    'open_rate': data.get('open_rate', 0),
                    'click_rate': data.get('click_rate', 0),
                    'reply_rate': data.get('reply_rate', 0),
                    'meetings_booked': data.get('meetings_booked', 0)
                }
            elif section == 'top_leads':
                report_content['sections']['top_leads'] = data.get('top_leads', [])
            elif section == 'revenue':
                report_content['sections']['revenue'] = {
                    'total': data.get('total_revenue', 0),
                    'by_source': data.get('revenue_by_source', {}),
                    'forecast': data.get('revenue_forecast', 0)
                }
            elif section == 'trends':
                report_content['sections']['trends'] = data.get('trends', {})
        
        return report_content
    
    def _format_as_csv(self, data: Dict) -> str:
        """Format report data as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Section', 'Metric', 'Value'])
        
        # Write data
        def write_section(section_name, section_data, prefix=''):
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, (dict, list)):
                        write_section(key, value, f"{prefix}{section_name}.")
                    else:
                        writer.writerow([f"{prefix}{section_name}", key, value])
            elif isinstance(section_data, list):
                for i, item in enumerate(section_data):
                    writer.writerow([f"{prefix}{section_name}", f"Item {i+1}", str(item)])
            else:
                writer.writerow([prefix[:-1] if prefix else section_name, '', section_data])
        
        if 'sections' in data:
            for section_name, section_data in data['sections'].items():
                write_section(section_name, section_data)
        else:
            write_section('data', data)
        
        return output.getvalue()
    
    def _generate_excel_mock(self, data: Dict) -> Dict:
        """Generate Excel report (mock - would use openpyxl in production)."""
        return {
            'format': 'excel',
            'workbook': 'BusinessDevelopmentReport.xlsx',
            'sheets': [
                {'name': 'Summary', 'rows': 50},
                {'name': 'Leads', 'rows': 200},
                {'name': 'Campaigns', 'rows': 25},
                {'name': 'Charts', 'charts': 5}
            ],
            'note': 'Mock Excel structure - would generate actual .xlsx file with openpyxl in production',
            'data_preview': data
        }
    
    def _generate_pdf_mock(self, data: Dict) -> Dict:
        """Generate PDF report (mock - would use reportlab in production)."""
        return {
            'format': 'pdf',
            'filename': 'BusinessDevelopmentReport.pdf',
            'pages': 15,
            'sections': list(data.get('sections', {}).keys()),
            'includes': ['charts', 'tables', 'executive_summary'],
            'note': 'Mock PDF structure - would generate actual PDF with reportlab in production',
            'data_preview': data
        }
    
    def schedule_report(self,
                       report_type: str,
                       frequency: str,
                       recipients: List[str],
                       format: str = 'pdf',
                       data_source: Dict = None) -> Dict:
        """
        Schedule recurring report.
        
        Args:
            report_type: Type of report to generate
            frequency: 'daily', 'weekly', 'monthly'
            recipients: Email addresses to send report to
            format: Report format
            data_source: Optional data source configuration
            
        Returns:
            Dict with scheduled report details
        """
        schedule_id = f"schedule_{int(datetime.now().timestamp())}"
        
        # Calculate next run time
        now = datetime.now()
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = now + timedelta(days=30)
        else:
            return {
                'success': False,
                'error': 'Invalid frequency. Use: daily, weekly, monthly'
            }
        
        scheduled_report = {
            'schedule_id': schedule_id,
            'report_type': report_type,
            'frequency': frequency,
            'recipients': recipients,
            'format': format,
            'data_source': data_source or {},
            'next_run': next_run.isoformat(),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        self.scheduled_reports.append(scheduled_report)
        
        return {
            'success': True,
            'schedule_id': schedule_id,
            'report_type': report_type,
            'frequency': frequency,
            'recipients': recipients,
            'next_run': next_run.isoformat(),
            'message': f'Report scheduled successfully'
        }
    
    def export_data(self,
                   data_type: str,
                   filters: Optional[Dict] = None,
                   format: str = 'csv',
                   fields: Optional[List[str]] = None) -> Dict:
        """
        Export specific data.
        
        Args:
            data_type: 'leads', 'campaigns', 'emails', 'contacts', 'deals'
            filters: Optional filters to apply
            format: Export format
            fields: Optional specific fields to include
            
        Returns:
            Dict with export details
        """
        export_id = f"export_{int(datetime.now().timestamp())}"
        
        # Mock data for demonstration
        mock_data = self._generate_mock_export_data(data_type, filters)
        
        # Filter fields if specified
        if fields:
            mock_data = self._filter_fields(mock_data, fields)
        
        # Format data
        if format == 'csv':
            export_content = self._format_export_csv(mock_data)
        elif format == 'json':
            export_content = mock_data
        elif format == 'excel':
            export_content = self._generate_excel_mock({'data': mock_data})
        else:
            export_content = mock_data
        
        return {
            'success': True,
            'export_id': export_id,
            'data_type': data_type,
            'format': format,
            'record_count': len(mock_data) if isinstance(mock_data, list) else 1,
            'data': export_content,
            'download_url': f'/api/reports/export/{export_id}',
            'exported_at': datetime.now().isoformat()
        }
    
    def _generate_mock_export_data(self, data_type: str, filters: Optional[Dict]) -> List[Dict]:
        """Generate mock data for export."""
        if data_type == 'leads':
            return [
                {
                    'id': f'lead_{i}',
                    'name': f'Lead {i}',
                    'email': f'lead{i}@example.com',
                    'company': f'Company {i}',
                    'score': 85 - i,
                    'status': 'active',
                    'created_at': (datetime.now() - timedelta(days=i)).isoformat()
                }
                for i in range(1, 26)  # 25 leads
            ]
        elif data_type == 'campaigns':
            return [
                {
                    'id': f'campaign_{i}',
                    'name': f'Campaign {i}',
                    'sent': 100 * i,
                    'opened': 30 * i,
                    'clicked': 10 * i,
                    'replied': 5 * i,
                    'status': 'active'
                }
                for i in range(1, 11)  # 10 campaigns
            ]
        else:
            return [{'id': i, 'data': f'Sample {data_type} {i}'} for i in range(1, 21)]
    
    def _filter_fields(self, data: List[Dict], fields: List[str]) -> List[Dict]:
        """Filter data to include only specified fields."""
        if not isinstance(data, list):
            return data
        
        return [
            {field: item.get(field) for field in fields if field in item}
            for item in data
        ]
    
    def _format_export_csv(self, data: List[Dict]) -> str:
        """Format export data as CSV."""
        if not data:
            return ''
        
        output = StringIO()
        
        # Get all unique keys from all records
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())
        
        fieldnames = sorted(all_keys)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def create_custom_dashboard(self,
                               dashboard_name: str,
                               widgets: List[Dict]) -> Dict:
        """
        Create custom dashboard configuration.
        
        Args:
            dashboard_name: Name for the dashboard
            widgets: List of widget configurations
            
        Returns:
            Dict with dashboard configuration
        """
        dashboard_id = f"dashboard_{int(datetime.now().timestamp())}"
        
        dashboard = {
            'dashboard_id': dashboard_id,
            'name': dashboard_name,
            'widgets': widgets,
            'layout': self._generate_dashboard_layout(widgets),
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'dashboard_id': dashboard_id,
            'name': dashboard_name,
            'widget_count': len(widgets),
            'dashboard': dashboard
        }
    
    def _generate_dashboard_layout(self, widgets: List[Dict]) -> List[Dict]:
        """Generate responsive dashboard layout."""
        layout = []
        
        for i, widget in enumerate(widgets):
            # Simple grid layout - 2 widgets per row
            row = i // 2
            col = i % 2
            
            layout.append({
                'widget_id': widget.get('id', f'widget_{i}'),
                'position': {
                    'row': row,
                    'col': col,
                    'width': 6,  # Half width (12-column grid)
                    'height': widget.get('height', 4)
                }
            })
        
        return layout
    
    def get_scheduled_reports(self, status: Optional[str] = None) -> Dict:
        """Get all scheduled reports."""
        reports = self.scheduled_reports
        
        if status:
            reports = [r for r in reports if r['status'] == status]
        
        return {
            'success': True,
            'report_count': len(reports),
            'reports': reports
        }
    
    def get_export_history(self, limit: int = 50) -> Dict:
        """Get export history."""
        recent_exports = self.export_history[-limit:] if len(self.export_history) > limit else self.export_history
        
        return {
            'success': True,
            'export_count': len(recent_exports),
            'exports': recent_exports
        }
    
    def get_available_templates(self) -> Dict:
        """Get available report templates."""
        return {
            'success': True,
            'template_count': len(self.report_templates),
            'templates': self.report_templates
        }
