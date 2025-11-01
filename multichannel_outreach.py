"""
Multi-Channel Outreach Module
SMS (Twilio), WhatsApp Business API, Slack integration for comprehensive outreach
"""

from datetime import datetime
from typing import Dict, List, Optional
import json

class MultiChannelOutreach:
    """Multi-channel communication system."""
    
    def __init__(self):
        self.twilio_config = {}
        self.whatsapp_config = {}
        self.slack_config = {}
        
        self.message_history = []
        self.channel_stats = {
            'sms': {'sent': 0, 'delivered': 0, 'failed': 0, 'replied': 0},
            'whatsapp': {'sent': 0, 'delivered': 0, 'failed': 0, 'replied': 0},
            'slack': {'sent': 0, 'delivered': 0, 'failed': 0, 'replied': 0},
            'email': {'sent': 0, 'delivered': 0, 'failed': 0, 'replied': 0}
        }
    
    # ===== TWILIO SMS INTEGRATION =====
    
    def configure_twilio(self, account_sid: str, auth_token: str, phone_number: str) -> Dict:
        """
        Configure Twilio for SMS.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            phone_number: Your Twilio phone number
            
        Returns:
            Dict with configuration status
        """
        self.twilio_config = {
            'account_sid': account_sid,
            'auth_token': auth_token,
            'phone_number': phone_number,
            'configured_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'provider': 'twilio',
            'phone_number': phone_number,
            'message': 'Twilio SMS configured successfully'
        }
    
    def send_sms(self, to_number: str, message: str, lead_id: Optional[str] = None) -> Dict:
        """
        Send SMS via Twilio.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message content
            lead_id: Optional lead identifier
            
        Returns:
            Dict with send status
        """
        if not self.twilio_config:
            return self._mock_sms_send(to_number, message, lead_id)
        
        # In production, would use Twilio API:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(body=message, from_=phone_number, to=to_number)
        
        return self._mock_sms_send(to_number, message, lead_id)
    
    def _mock_sms_send(self, to_number: str, message: str, lead_id: Optional[str]) -> Dict:
        """Mock SMS send for demonstration."""
        message_id = f"sms_{int(datetime.now().timestamp() * 1000)}"
        
        message_record = {
            'message_id': message_id,
            'channel': 'sms',
            'to': to_number,
            'message': message,
            'lead_id': lead_id,
            'status': 'sent',
            'sent_at': datetime.now().isoformat(),
            'provider': 'twilio'
        }
        
        self.message_history.append(message_record)
        self.channel_stats['sms']['sent'] += 1
        self.channel_stats['sms']['delivered'] += 1  # Mock delivery
        
        return {
            'success': True,
            'message_id': message_id,
            'channel': 'sms',
            'to': to_number,
            'status': 'sent',
            'provider': 'twilio',
            'note': 'Mock SMS - configure Twilio credentials for real SMS'
        }
    
    def send_sms_bulk(self, recipients: List[Dict]) -> Dict:
        """
        Send bulk SMS messages.
        
        Args:
            recipients: List of dicts with 'phone', 'message', 'lead_id'
            
        Returns:
            Dict with bulk send results
        """
        results = []
        
        for recipient in recipients:
            result = self.send_sms(
                to_number=recipient['phone'],
                message=recipient['message'],
                lead_id=recipient.get('lead_id')
            )
            results.append(result)
        
        successful = len([r for r in results if r['success']])
        
        return {
            'success': True,
            'total': len(recipients),
            'successful': successful,
            'failed': len(recipients) - successful,
            'results': results
        }
    
    # ===== WHATSAPP BUSINESS API INTEGRATION =====
    
    def configure_whatsapp(self, access_token: str, phone_number_id: str, business_account_id: str) -> Dict:
        """
        Configure WhatsApp Business API.
        
        Args:
            access_token: WhatsApp Business API access token
            phone_number_id: Phone number ID from WhatsApp
            business_account_id: Business account ID
            
        Returns:
            Dict with configuration status
        """
        self.whatsapp_config = {
            'access_token': access_token,
            'phone_number_id': phone_number_id,
            'business_account_id': business_account_id,
            'configured_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'provider': 'whatsapp',
            'phone_number_id': phone_number_id,
            'message': 'WhatsApp Business API configured successfully'
        }
    
    def send_whatsapp(self, to_number: str, message: str, lead_id: Optional[str] = None) -> Dict:
        """
        Send WhatsApp message.
        
        Args:
            to_number: Recipient WhatsApp number
            message: Message content
            lead_id: Optional lead identifier
            
        Returns:
            Dict with send status
        """
        if not self.whatsapp_config:
            return self._mock_whatsapp_send(to_number, message, lead_id)
        
        # In production, would use WhatsApp Business API
        return self._mock_whatsapp_send(to_number, message, lead_id)
    
    def _mock_whatsapp_send(self, to_number: str, message: str, lead_id: Optional[str]) -> Dict:
        """Mock WhatsApp send."""
        message_id = f"whatsapp_{int(datetime.now().timestamp() * 1000)}"
        
        message_record = {
            'message_id': message_id,
            'channel': 'whatsapp',
            'to': to_number,
            'message': message,
            'lead_id': lead_id,
            'status': 'sent',
            'sent_at': datetime.now().isoformat(),
            'provider': 'whatsapp_business'
        }
        
        self.message_history.append(message_record)
        self.channel_stats['whatsapp']['sent'] += 1
        self.channel_stats['whatsapp']['delivered'] += 1
        
        return {
            'success': True,
            'message_id': message_id,
            'channel': 'whatsapp',
            'to': to_number,
            'status': 'sent',
            'provider': 'whatsapp_business',
            'note': 'Mock WhatsApp - configure WhatsApp Business API for real messages'
        }
    
    def send_whatsapp_template(self, to_number: str, template_name: str, parameters: List[str]) -> Dict:
        """
        Send WhatsApp template message (for marketing).
        
        Args:
            to_number: Recipient number
            template_name: Pre-approved template name
            parameters: Template parameters
            
        Returns:
            Dict with send status
        """
        message_id = f"whatsapp_template_{int(datetime.now().timestamp() * 1000)}"
        
        return {
            'success': True,
            'message_id': message_id,
            'channel': 'whatsapp',
            'to': to_number,
            'template': template_name,
            'status': 'sent',
            'note': 'Mock template message - configure WhatsApp Business API'
        }
    
    # ===== SLACK INTEGRATION =====
    
    def configure_slack(self, bot_token: str, workspace_id: str) -> Dict:
        """
        Configure Slack integration.
        
        Args:
            bot_token: Slack bot OAuth token
            workspace_id: Slack workspace ID
            
        Returns:
            Dict with configuration status
        """
        self.slack_config = {
            'bot_token': bot_token,
            'workspace_id': workspace_id,
            'configured_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'provider': 'slack',
            'workspace_id': workspace_id,
            'message': 'Slack configured successfully'
        }
    
    def send_slack_message(self, channel: str, message: str, lead_id: Optional[str] = None) -> Dict:
        """
        Send Slack message.
        
        Args:
            channel: Slack channel ID or name
            message: Message content
            lead_id: Optional lead identifier
            
        Returns:
            Dict with send status
        """
        if not self.slack_config:
            return self._mock_slack_send(channel, message, lead_id)
        
        # In production, would use Slack SDK:
        # from slack_sdk import WebClient
        # client = WebClient(token=bot_token)
        # response = client.chat_postMessage(channel=channel, text=message)
        
        return self._mock_slack_send(channel, message, lead_id)
    
    def _mock_slack_send(self, channel: str, message: str, lead_id: Optional[str]) -> Dict:
        """Mock Slack send."""
        message_id = f"slack_{int(datetime.now().timestamp() * 1000)}"
        
        message_record = {
            'message_id': message_id,
            'channel': 'slack',
            'to': channel,
            'message': message,
            'lead_id': lead_id,
            'status': 'sent',
            'sent_at': datetime.now().isoformat(),
            'provider': 'slack'
        }
        
        self.message_history.append(message_record)
        self.channel_stats['slack']['sent'] += 1
        self.channel_stats['slack']['delivered'] += 1
        
        return {
            'success': True,
            'message_id': message_id,
            'channel': 'slack',
            'to': channel,
            'status': 'sent',
            'provider': 'slack',
            'note': 'Mock Slack - configure Slack bot token for real messages'
        }
    
    def send_slack_dm(self, user_id: str, message: str) -> Dict:
        """Send direct message on Slack."""
        return self.send_slack_message(channel=user_id, message=message)
    
    # ===== MULTI-CHANNEL CAMPAIGN =====
    
    def create_multichannel_campaign(self,
                                    campaign_name: str,
                                    channels: List[str],
                                    message_templates: Dict[str, str],
                                    recipients: List[Dict]) -> Dict:
        """
        Create multi-channel campaign.
        
        Args:
            campaign_name: Campaign name
            channels: List of channels to use ['email', 'sms', 'whatsapp', 'slack']
            message_templates: Dict mapping channel to message template
            recipients: List of recipient configs with channel contact info
            
        Returns:
            Dict with campaign details
        """
        campaign_id = f"campaign_{int(datetime.now().timestamp())}"
        
        campaign = {
            'campaign_id': campaign_id,
            'name': campaign_name,
            'channels': channels,
            'message_templates': message_templates,
            'recipients': recipients,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'name': campaign_name,
            'channels': channels,
            'recipient_count': len(recipients),
            'total_messages': len(recipients) * len(channels),
            'campaign': campaign
        }
    
    def send_multichannel_message(self,
                                  recipient: Dict,
                                  channels: List[str],
                                  messages: Dict[str, str]) -> Dict:
        """
        Send message across multiple channels to single recipient.
        
        Args:
            recipient: Recipient contact info (email, phone, slack_user_id)
            channels: Channels to use
            messages: Channel-specific messages
            
        Returns:
            Dict with send results per channel
        """
        results = {}
        
        for channel in channels:
            if channel == 'sms' and recipient.get('phone'):
                results['sms'] = self.send_sms(
                    to_number=recipient['phone'],
                    message=messages.get('sms', messages.get('default', '')),
                    lead_id=recipient.get('lead_id')
                )
            elif channel == 'whatsapp' and recipient.get('phone'):
                results['whatsapp'] = self.send_whatsapp(
                    to_number=recipient['phone'],
                    message=messages.get('whatsapp', messages.get('default', '')),
                    lead_id=recipient.get('lead_id')
                )
            elif channel == 'slack' and recipient.get('slack_user_id'):
                results['slack'] = self.send_slack_dm(
                    user_id=recipient['slack_user_id'],
                    message=messages.get('slack', messages.get('default', ''))
                )
        
        successful_channels = [ch for ch, result in results.items() if result.get('success')]
        
        return {
            'success': True,
            'channels_sent': successful_channels,
            'total_channels': len(channels),
            'results': results
        }
    
    def get_channel_stats(self) -> Dict:
        """Get statistics per channel."""
        # Calculate rates
        stats_with_rates = {}
        
        for channel, stats in self.channel_stats.items():
            delivery_rate = (stats['delivered'] / stats['sent'] * 100) if stats['sent'] > 0 else 0
            reply_rate = (stats['replied'] / stats['delivered'] * 100) if stats['delivered'] > 0 else 0
            
            stats_with_rates[channel] = {
                **stats,
                'delivery_rate': round(delivery_rate, 2),
                'reply_rate': round(reply_rate, 2)
            }
        
        return {
            'success': True,
            'channel_stats': stats_with_rates,
            'total_messages': sum(s['sent'] for s in self.channel_stats.values()),
            'best_performing_channel': max(
                stats_with_rates.items(),
                key=lambda x: x[1]['reply_rate']
            )[0] if any(s['sent'] > 0 for s in self.channel_stats.values()) else None
        }
    
    def get_message_history(self, 
                           channel: Optional[str] = None,
                           lead_id: Optional[str] = None,
                           limit: int = 50) -> Dict:
        """
        Get message history with optional filters.
        
        Args:
            channel: Filter by channel
            lead_id: Filter by lead
            limit: Maximum messages to return
            
        Returns:
            Dict with message history
        """
        filtered_messages = self.message_history
        
        if channel:
            filtered_messages = [m for m in filtered_messages if m['channel'] == channel]
        
        if lead_id:
            filtered_messages = [m for m in filtered_messages if m.get('lead_id') == lead_id]
        
        # Get most recent
        filtered_messages = filtered_messages[-limit:] if len(filtered_messages) > limit else filtered_messages
        
        return {
            'success': True,
            'message_count': len(filtered_messages),
            'messages': filtered_messages
        }
    
    def track_reply(self, message_id: str, reply_content: str) -> Dict:
        """Track reply to sent message."""
        # Find original message
        for message in self.message_history:
            if message['message_id'] == message_id:
                message['reply_received'] = True
                message['reply_content'] = reply_content
                message['reply_at'] = datetime.now().isoformat()
                
                # Update stats
                channel = message['channel']
                self.channel_stats[channel]['replied'] += 1
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'message': 'Reply tracked successfully'
                }
        
        return {
            'success': False,
            'error': 'Message not found'
        }
    
    def get_best_channel_for_lead(self, lead_engagement: Dict) -> Dict:
        """
        Recommend best channel based on lead's historical engagement.
        
        Args:
            lead_engagement: Lead's engagement history per channel
            
        Returns:
            Dict with recommendation
        """
        # Calculate engagement score per channel
        channel_scores = {}
        
        for channel, engagement in lead_engagement.items():
            score = 0
            score += engagement.get('opened', 0) * 1
            score += engagement.get('clicked', 0) * 2
            score += engagement.get('replied', 0) * 5
            
            channel_scores[channel] = score
        
        if not channel_scores:
            return {
                'success': True,
                'recommended_channel': 'email',
                'reason': 'No engagement data - defaulting to email'
            }
        
        best_channel = max(channel_scores.items(), key=lambda x: x[1])
        
        return {
            'success': True,
            'recommended_channel': best_channel[0],
            'engagement_score': best_channel[1],
            'all_scores': channel_scores,
            'reason': f'Highest engagement score ({best_channel[1]}) on {best_channel[0]}'
        }
