import aiohttp
import os
from app import database

key = os.environ.get("CAPITAL_ONE_API_KEY")

async def delete_account(customer_id):
    return
    
# Get an account
async def get_account(slack_id):
    user = database['Users'].find_one({"_id": slack_id})
    if user is None:
        return None
    account_id = user["account_id"]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://api.nessieisreal.com/accounts/{account_id}?key={key}") as response:

            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])

            if response.status == 404:
                return None
            response = await response.json()
            return response

async def create_account(slack_id, email):
    user = database['Users'].find_one({"_id": slack_id})
    if user is not None:
        return None
    # Create a new account
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://api.nessieisreal.com/customers?key={key}", json={
            "first_name": "Test",
            "last_name": "User",
            "address": {
                "street_number": "123",
                "street_name": "Fake St",
                "city": "Boston",
                "state": "MA",
                "zip": "02115"
            }
        }) as response:
            j = await response.json()
            customer_id = j["objectCreated"]["_id"]
        
        print("created customer")
        async with session.post(f"http://api.nessieisreal.com/customers/{customer_id}/accounts?key={key}", json={
            "type": "Checking",
            "nickname": "My Checking",
            "rewards": 0,
            "balance": 200
        }) as response:
            j = await response.json()
            account_id = j["objectCreated"]["_id"]
        
        database['Users'].insert_one({
            "_id": slack_id,
            "account_id": account_id,
            "customer_id": customer_id,
            "infractions": 0,
            "email": email,
        })
        # save user to mongodb
        return True

async def add_money(slack_id, amount, description):
    user = database['Users'].find_one({"_id": slack_id})
    if user is None:
        return None
    account_id = user["account_id"]
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://api.nessieisreal.com/accounts/{account_id}/deposits?key={key}", json={
            "medium": "balance",
            "amount": amount,
            "description": description,
            "status": "completed"
        }) as response:
            html = await response.text()
            print(html)


async def subtract_money(slack_id, amount, description):
    user = database['Users'].find_one({"_id": slack_id})
    if user is None:
        return None
    account_id = user["account_id"]
    print(account_id)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://api.nessieisreal.com/accounts/{account_id}/withdrawals?key={key}", json={
            "medium": "balance",
            "amount": amount,
            "description": description,
            "status": "completed"
        }) as response:
            html = await response.text()
            print(html)
            return True