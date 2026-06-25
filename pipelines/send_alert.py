#!/usr/bin/env python3
"""
Revolutionary Technology Company - Hospital IT Incident Alert System
Dispatches high-visibility markdown alerts to Slack or Microsoft Teams channels 
whenever a critical failure is flagged within the RTX 6000 Ada processing stack.
"""

import sys
import json
import requests
from datetime import datetime

# --------------------------------------------------------------------------
# CONFIGURATION BOUNDS
# Replace these strings with your actual institutional Slack or Teams Webhook URLs.
# --------------------------------------------------------------------------
WEBHOOK_URL = "https://slack.com"
# For MS Teams, swap with: "https://office.com..."

# Set destination format framework flag: "SLACK" or "TEAMS"
TARGET_PLATFORM = "SLACK" 

def dispatch_slack_alert(error_details: str):
    """Assembles a rich-text Block Kit payload optimized for Slack."""
    payload = {
        "text": "🚨 CRITICAL OUTAGE: Hospital MRI Processing Node Failure",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 CRITICAL: MRI GPU Processing Pipeline Failure",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Timestamp (UTC):*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"},
                    {"type": "mrkdwn", "text": f"*Target Compute Node:*\nRTX_6000_ADA_MAIN_NODE_01"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*System Error Log:* \n```\n{error_details}\n```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "⚠️ Action Required: Verify local Edge Router logs or restart docker containers immediately."}
                ]
            }
        ]
    }
    return payload

def dispatch_teams_alert(error_details: str):
    """Assembles an Adaptive Card JSON schema configuration optimized for MS Teams."""
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {"type": "TextBlock", "text": "🚨 CRITICAL: MRI GPU Pipeline Failure", "weight": "Bolder", "size": "Large", "color": "Attention"},
                        {"type": "TextBlock", "text": f"**Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", "wrap": True},
                        {"type": "TextBlock", "text": "**System Diagnostics Output:**", "weight": "Bolder"},
                        {"type": "TextBlock", "text": f"```\n{error_details}\n```", "wrap": True, "monospace": True},
                        {"type": "TextBlock", "text": "Action Required: Please evaluate internal network connection limits or host hardware health topology parameters.", "isSubtle": True, "wrap": True}
                    ]
                }
            }
        ]
    }
    return payload

def send_alert(error_message: str):
    """Dispatches the notification wrapper payload downstream to the target channel."""
    if "YOUR/HOSPITAL" in WEBHOOK_URL:
        print("[ALERT-SKIP] Default placeholder webhook URL located. Skipping transmission step.")
        return False

    if TARGET_PLATFORM.upper() == "SLACK":
        json_data = dispatch_slack_alert(error_message)
    else:
        json_data = dispatch_teams_alert(error_message)

    try:
        response = requests.post(
            WEBHOOK_URL, 
            json=json_data, 
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in:
            print("[ALERT-SUCCESS] Incident response broadcast successfully transmitted.")
            return True
        else:
            print(f"[ALERT-ERROR] Webhook platform endpoint returned code status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ALERT-CRITICAL] Network exception blocking alert pathway: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_alert.py 'Error log stack trace detailed description string'")
        sys.exit(1)
        
    send_alert(sys.argv[1])
