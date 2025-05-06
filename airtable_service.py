
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
        # Use URL-encoded table name for spaces
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name.replace(" ", "%20")}'
    
    def list_tables(self):
        """List all tables in the base to help with troubleshooting"""
        if not self.api_token:
            print("Warning: AIRTABLE_TOKEN environment variable is not set")
            return None
            
        try:
            base_url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
            response = requests.get(
                base_url,
                headers=self.headers
            )
            
            if response.status_code == 200:
                tables = response.json().get('tables', [])
                table_names = [table.get('name') for table in tables]
                print(f"Available tables in base {self.base_id}: {table_names}")
                return table_names
            else:
                print(f"Error listing tables: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception when listing tables: {str(e)}")
            return None
    
    def log_pizza_grant(self, submission_data):
        """Log a pizza grant submission to Airtable"""
        if not self.api_token:
            print("Warning: AIRTABLE_TOKEN environment variable is not set")
            return None
            
        # Try to list tables first to validate access and see available tables
        tables = self.list_tables()
        
        # Format data for Airtable - ensure field names match exactly what's in Airtable
        fields = {
            'Name': submission_data.get('username'),  # Commonly used field name in Airtable
            'Username': submission_data.get('username'),
            'Project Name': submission_data.get('project_name'),
            'Project': submission_data.get('project_name'),  # Alternative field name
            'Project Description': submission_data.get('project_description'),
            'Description': submission_data.get('project_description'),  # Alternative field name
            'Hours': submission_data.get('project_hours'),
            'Grant Amount': submission_data.get('grant_amount'),
            'Amount': submission_data.get('grant_amount'),  # Alternative field name
            'GitHub URL': submission_data.get('github_url'),
            'GitHub': submission_data.get('github_url'),  # Alternative field name
            'Live URL': submission_data.get('live_url'),
            'URL': submission_data.get('live_url'),  # Alternative field name
            'What Learned': submission_data.get('what_learned', ''),
            'Learning': submission_data.get('what_learned', ''),  # Alternative field name
            'Email': submission_data.get('email', ''),
            'Status': submission_data.get('status', 'pending'),
            'Submission Date': submission_data.get('submitted_at', datetime.now().isoformat()),
            'Date': submission_data.get('submitted_at', datetime.now().isoformat()),  # Alternative field name
            'Club ID': submission_data.get('club_id'),
            'Club': submission_data.get('club_id'),  # Alternative field name
            'Shipping Address': json.dumps(submission_data.get('shipping_address', {})),
            'Address': json.dumps(submission_data.get('shipping_address', {}))  # Alternative field name
        }
        
        payload = {
            'records': [
                {
                    'fields': fields
                }
            ]
        }
        
        try:
            # First try with the configured table name
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"Successfully logged to Airtable table: {self.table_name}")
                return response.json()
            else:
                print(f"Error logging to Airtable: {response.status_code} - {response.text}")
                
                # If tables were found, try with first available table as fallback
                if tables and len(tables) > 0:
                    fallback_table = tables[0]
                    print(f"Attempting fallback to table: {fallback_table}")
                    fallback_url = f"https://api.airtable.com/v0/{self.base_id}/{fallback_table.replace(' ', '%20')}"
                    
                    fallback_response = requests.post(
                        fallback_url,
                        headers=self.headers,
                        json=payload
                    )
                    
                    if fallback_response.status_code == 200 or fallback_response.status_code == 201:
                        print(f"Successfully logged to fallback table: {fallback_table}")
                        # Update the table name for future requests
                        self.table_name = fallback_table
                        self.base_url = fallback_url
                        return fallback_response.json()
                    else:
                        print(f"Fallback table also failed: {fallback_response.status_code} - {fallback_response.text}")
                
                return None
                
        except Exception as e:
            print(f"Exception when logging to Airtable: {str(e)}")
            return None

# Singleton instance
airtable_service = AirtableService()
