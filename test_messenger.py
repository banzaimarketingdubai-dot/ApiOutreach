import asyncio
import sys

from app.services.messenger_checker import verify_messenger_availability

print(verify_messenger_availability("+380676200515"))
