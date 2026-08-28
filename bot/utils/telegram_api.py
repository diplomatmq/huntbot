import aiohttp
import json


class TelegramBotAPI:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def create_invoice_link(self, **kwargs):
        """Прямой вызов Telegram Bot API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/createInvoiceLink",
                json=kwargs,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return result.get("result")
                    else:
                        raise Exception(f"Telegram API error: {result.get('description')}")
                else:
                    raise Exception(f"HTTP error: {response.status}")
