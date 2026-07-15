import httpx
from app.core.config import settings
from loguru import logger

async def send_slack_alert(message: str):
    """
    Sends an alert notification block to the configured Slack channel.
    Falls back to system logs if the webhook URL is unconfigured.
    """
    if not settings.SLACK_WEBHOOK_URL:
        logger.info(f"[Slack Notifier Fallback] Alert: '{message}'")
        return False
        
    try:
        async with httpx.AsyncClient() as client:
            payload = {"text": f"🔔 *LoomSense AI Alert:* {message}"}
            resp = await client.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
            if resp.status_code == 200:
                logger.info("Slack alert successfully transmitted.")
                return True
            else:
                logger.error(f"Slack alert failed. Status: {resp.status_code}, Body: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error posting Slack notification: {str(e)}")
        return False
