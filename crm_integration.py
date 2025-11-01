"""
CRM Integration Module
Provides Salesforce, HubSpot, and Pipedrive integration with two-way sync
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import json

class CRMIntegration:
    """Unified CRM integration interface."""
    
    def __init__(self):
        self.salesforce_config = {}
        self.hubspot_config = {}
        self.pipedrive_config = {}
        
        self.sync_log = []
        self.crm_records = {}
    
    # ===== SALESFORCE INTEGRATION =====
    
    def configure_salesforce(self, 
                            instance_url: str,
                            access_token: str,
                            api_version: str = 'v57.0') -> Dict:
        """
        Configure Salesforce connection.
        
        Args:
            instance_url: Salesforce instance URL (e.g., https://yourinstance.salesforce.com)
            access_token: OAuth access token
            api_version: API version (default: v57.0)
            
        Returns:
            Dict with configuration status
        """
        self.salesforce_config = {
            'instance_url': instance_url,
            'access_token': access_token,
            'api_version': api_version,
            'base_url': f"{instance_url}/services/data/{api_version}"
        }
        
        return {
            'success': True,
            'message': 'Salesforce configured successfully',
            'instance': instance_url
        }
    
    def salesforce_create_lead(self, lead_data: Dict) -> Dict:
        """
        Create lead in Salesforce.
        
        Args:
            lead_data: Dict with FirstName, LastName, Company, Email, etc.
            
        Returns:
            Dict with Salesforce lead ID
        """
        if not self.salesforce_config:
            return {'success': False, 'error': 'Salesforce not configured'}
        
        url = f"{self.salesforce_config['base_url']}/sobjects/Lead"
        headers = {
            'Authorization': f"Bearer {self.salesforce_config['access_token']}",
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=lead_data)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_sync('salesforce', 'create_lead', lead_data.get('Email'), 'success')
            
            return {
                'success': True,
                'salesforce_id': result['id'],
                'message': 'Lead created in Salesforce'
            }
        except Exception as e:
            self._log_sync('salesforce', 'create_lead', lead_data.get('Email'), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def salesforce_update_lead(self, lead_id: str, updates: Dict) -> Dict:
        """Update lead in Salesforce."""
        if not self.salesforce_config:
            return {'success': False, 'error': 'Salesforce not configured'}
        
        url = f"{self.salesforce_config['base_url']}/sobjects/Lead/{lead_id}"
        headers = {
            'Authorization': f"Bearer {self.salesforce_config['access_token']}",
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.patch(url, headers=headers, json=updates)
            response.raise_for_status()
            
            self._log_sync('salesforce', 'update_lead', lead_id, 'success')
            
            return {
                'success': True,
                'message': 'Lead updated in Salesforce'
            }
        except Exception as e:
            self._log_sync('salesforce', 'update_lead', lead_id, 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def salesforce_get_leads(self, filters: Dict = None) -> Dict:
        """Get leads from Salesforce."""
        if not self.salesforce_config:
            return {'success': False, 'error': 'Salesforce not configured'}
        
        # Build SOQL query
        query = "SELECT Id, FirstName, LastName, Email, Company, Status FROM Lead"
        if filters:
            # Add WHERE clause based on filters
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = '{value}'")
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
        
        query += " LIMIT 100"
        
        url = f"{self.salesforce_config['base_url']}/query"
        headers = {
            'Authorization': f"Bearer {self.salesforce_config['access_token']}"
        }
        params = {'q': query}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'leads': result.get('records', []),
                'count': result.get('totalSize', 0)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ===== HUBSPOT INTEGRATION =====
    
    def configure_hubspot(self, api_key: str) -> Dict:
        """
        Configure HubSpot connection.
        
        Args:
            api_key: HubSpot API key
            
        Returns:
            Dict with configuration status
        """
        self.hubspot_config = {
            'api_key': api_key,
            'base_url': 'https://api.hubapi.com'
        }
        
        return {
            'success': True,
            'message': 'HubSpot configured successfully'
        }
    
    def hubspot_create_contact(self, contact_data: Dict) -> Dict:
        """
        Create contact in HubSpot.
        
        Args:
            contact_data: Dict with email, firstname, lastname, company, etc.
            
        Returns:
            Dict with HubSpot contact ID
        """
        if not self.hubspot_config:
            return {'success': False, 'error': 'HubSpot not configured'}
        
        url = f"{self.hubspot_config['base_url']}/crm/v3/objects/contacts"
        headers = {
            'Authorization': f"Bearer {self.hubspot_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        # Format data for HubSpot
        payload = {
            'properties': contact_data
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_sync('hubspot', 'create_contact', contact_data.get('email'), 'success')
            
            return {
                'success': True,
                'hubspot_id': result['id'],
                'message': 'Contact created in HubSpot'
            }
        except Exception as e:
            self._log_sync('hubspot', 'create_contact', contact_data.get('email'), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def hubspot_create_deal(self, deal_data: Dict) -> Dict:
        """
        Create deal in HubSpot.
        
        Args:
            deal_data: Dict with dealname, dealstage, amount, etc.
            
        Returns:
            Dict with HubSpot deal ID
        """
        if not self.hubspot_config:
            return {'success': False, 'error': 'HubSpot not configured'}
        
        url = f"{self.hubspot_config['base_url']}/crm/v3/objects/deals"
        headers = {
            'Authorization': f"Bearer {self.hubspot_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'properties': deal_data
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_sync('hubspot', 'create_deal', deal_data.get('dealname'), 'success')
            
            return {
                'success': True,
                'hubspot_deal_id': result['id'],
                'message': 'Deal created in HubSpot'
            }
        except Exception as e:
            self._log_sync('hubspot', 'create_deal', deal_data.get('dealname'), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def hubspot_get_contacts(self, limit: int = 100) -> Dict:
        """Get contacts from HubSpot."""
        if not self.hubspot_config:
            return {'success': False, 'error': 'HubSpot not configured'}
        
        url = f"{self.hubspot_config['base_url']}/crm/v3/objects/contacts"
        headers = {
            'Authorization': f"Bearer {self.hubspot_config['api_key']}"
        }
        params = {'limit': limit}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'contacts': result.get('results', []),
                'count': len(result.get('results', []))
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ===== PIPEDRIVE INTEGRATION =====
    
    def configure_pipedrive(self, api_token: str, company_domain: str) -> Dict:
        """
        Configure Pipedrive connection.
        
        Args:
            api_token: Pipedrive API token
            company_domain: Your Pipedrive company domain
            
        Returns:
            Dict with configuration status
        """
        self.pipedrive_config = {
            'api_token': api_token,
            'base_url': f'https://{company_domain}.pipedrive.com/api/v1'
        }
        
        return {
            'success': True,
            'message': 'Pipedrive configured successfully',
            'domain': company_domain
        }
    
    def pipedrive_create_person(self, person_data: Dict) -> Dict:
        """
        Create person in Pipedrive.
        
        Args:
            person_data: Dict with name, email, phone, org_id, etc.
            
        Returns:
            Dict with Pipedrive person ID
        """
        if not self.pipedrive_config:
            return {'success': False, 'error': 'Pipedrive not configured'}
        
        url = f"{self.pipedrive_config['base_url']}/persons"
        params = {'api_token': self.pipedrive_config['api_token']}
        
        try:
            response = requests.post(url, params=params, json=person_data)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_sync('pipedrive', 'create_person', person_data.get('email'), 'success')
            
            return {
                'success': True,
                'pipedrive_id': result['data']['id'],
                'message': 'Person created in Pipedrive'
            }
        except Exception as e:
            self._log_sync('pipedrive', 'create_person', person_data.get('email'), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def pipedrive_create_deal(self, deal_data: Dict) -> Dict:
        """
        Create deal in Pipedrive.
        
        Args:
            deal_data: Dict with title, value, person_id, org_id, stage_id, etc.
            
        Returns:
            Dict with Pipedrive deal ID
        """
        if not self.pipedrive_config:
            return {'success': False, 'error': 'Pipedrive not configured'}
        
        url = f"{self.pipedrive_config['base_url']}/deals"
        params = {'api_token': self.pipedrive_config['api_token']}
        
        try:
            response = requests.post(url, params=params, json=deal_data)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_sync('pipedrive', 'create_deal', deal_data.get('title'), 'success')
            
            return {
                'success': True,
                'pipedrive_deal_id': result['data']['id'],
                'message': 'Deal created in Pipedrive'
            }
        except Exception as e:
            self._log_sync('pipedrive', 'create_deal', deal_data.get('title'), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def pipedrive_update_deal(self, deal_id: int, updates: Dict) -> Dict:
        """Update deal in Pipedrive."""
        if not self.pipedrive_config:
            return {'success': False, 'error': 'Pipedrive not configured'}
        
        url = f"{self.pipedrive_config['base_url']}/deals/{deal_id}"
        params = {'api_token': self.pipedrive_config['api_token']}
        
        try:
            response = requests.put(url, params=params, json=updates)
            response.raise_for_status()
            
            self._log_sync('pipedrive', 'update_deal', str(deal_id), 'success')
            
            return {
                'success': True,
                'message': 'Deal updated in Pipedrive'
            }
        except Exception as e:
            self._log_sync('pipedrive', 'update_deal', str(deal_id), 'error')
            return {
                'success': False,
                'error': str(e)
            }
    
    def pipedrive_get_deals(self, status: str = 'all_not_deleted') -> Dict:
        """Get deals from Pipedrive."""
        if not self.pipedrive_config:
            return {'success': False, 'error': 'Pipedrive not configured'}
        
        url = f"{self.pipedrive_config['base_url']}/deals"
        params = {
            'api_token': self.pipedrive_config['api_token'],
            'status': status
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'deals': result.get('data', []),
                'count': len(result.get('data', []))
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ===== TWO-WAY SYNC =====
    
    def sync_to_crm(self, 
                    crm_type: str,
                    record_type: str,
                    data: Dict) -> Dict:
        """
        Universal sync to any configured CRM.
        
        Args:
            crm_type: 'salesforce', 'hubspot', or 'pipedrive'
            record_type: 'lead', 'contact', 'deal', 'person'
            data: Record data
            
        Returns:
            Dict with sync status
        """
        if crm_type == 'salesforce':
            if record_type == 'lead':
                return self.salesforce_create_lead(data)
            else:
                return {'success': False, 'error': f'Unsupported record type for Salesforce: {record_type}'}
        
        elif crm_type == 'hubspot':
            if record_type == 'contact':
                return self.hubspot_create_contact(data)
            elif record_type == 'deal':
                return self.hubspot_create_deal(data)
            else:
                return {'success': False, 'error': f'Unsupported record type for HubSpot: {record_type}'}
        
        elif crm_type == 'pipedrive':
            if record_type == 'person':
                return self.pipedrive_create_person(data)
            elif record_type == 'deal':
                return self.pipedrive_create_deal(data)
            else:
                return {'success': False, 'error': f'Unsupported record type for Pipedrive: {record_type}'}
        
        else:
            return {'success': False, 'error': f'Unsupported CRM: {crm_type}'}
    
    def bulk_sync(self, 
                  crm_type: str,
                  records: List[Dict]) -> Dict:
        """
        Sync multiple records to CRM.
        
        Args:
            crm_type: Target CRM
            records: List of records with 'type' and 'data' fields
            
        Returns:
            Dict with bulk sync results
        """
        results = {
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for record in records:
            result = self.sync_to_crm(
                crm_type=crm_type,
                record_type=record['type'],
                data=record['data']
            )
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append(result)
        
        return {
            'success': True,
            'total': len(records),
            'synced': results['success'],
            'failed': results['failed'],
            'details': results['details']
        }
    
    def get_sync_log(self, limit: int = 50) -> Dict:
        """Get recent sync activity log."""
        recent_logs = self.sync_log[-limit:] if len(self.sync_log) > limit else self.sync_log
        
        return {
            'success': True,
            'log_count': len(recent_logs),
            'logs': recent_logs
        }
    
    def _log_sync(self, crm: str, action: str, identifier: str, status: str):
        """Internal method to log sync operations."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'crm': crm,
            'action': action,
            'identifier': identifier,
            'status': status
        }
        self.sync_log.append(log_entry)
