
import os
import requests
import json
from datetime import datetime

class AirtableService:
    def __init__(self):
        self.api_token = os.environ.get('AIRTABLE_TOKEN')
        self.base_id = 'appSnnIu0BhjI3E1p'
        self.table_name = 'Pizza Grants'
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name}'
    
    def log_pizza_grant(self, submission_data):
        """Log a pizza grant submission to Airtable"""
        if not self.api_token:
            print("Warning: AIRTABLE_TOKEN environment variable is not set")
            return None
            
        # Format data for Airtable
        fields = {
            'Username': submission_data.get('username'),
            'Project Name': submission_data.get('project_name'),
            'Project Description': submission_data.get('project_description'),
            'Hours': submission_data.get('project_hours'),
            'Grant Amount': submission_data.get('grant_amount'),
            'GitHub URL': submission_data.get('github_url'),
            'Live URL': submission_data.get('live_url'),
            'What Learned': submission_data.get('what_learned', ''),
            'Email': submission_data.get('email', ''),
            'Status': submission_data.get('status', 'pending'),
            'Submission Date': submission_data.get('submitted_at', datetime.now().isoformat()),
            'Club ID': submission_data.get('club_id'),
            'Shipping Address': json.dumps(submission_data.get('shipping_address', {}))
        }
        
        payload = {
            'records': [
                {
                    'fields': fields
                }
            ]
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                print(f"Error logging to Airtable: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception when logging to Airtable: {str(e)}")
            return None

# Singleton instance
airtable_service = AirtableService()
