import logging
import os

# logging.basicConfig(level=logging.DEBUG)

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
app_handler = AsyncSlackRequestHandler(app)

mongodb_client = MongoClient(os.environ.get("ATLAS_URI"))
database = mongodb_client[os.environ.get("DB_NAME")]

from chat import handle_chat
from financial import create_account, get_account, add_money


@app.command("/money")
async def money_command(ack, say, command):
    ack("Fetching account...")
    account = await get_account(command["user_id"])
    if account is None:
        await ack("You do not have an account. Creating one...")
        await create_account(command["user_id"])
        account = await get_account(command["user_id"])
    await ack("You have $" + str(account["balance"]) + " in your account.")

@app.command("/work")
async def work_command(ack, say, command):
    account = await get_account(command["user_id"])
    if account is None:
        await ack("You do not have an account. Creating one...")
        await create_account(command["user_id"])
    await add_money(command["user_id"], 20, "Worked")
    await ack("Expect your paycheck in 2-3 business days.")

@app.command("/create-account")
async def create_account_command(ack, say, command):
    ack("Creating account...")
    account = await create_account(command["user_id"], command["user_name"])
    if not account:
        await ack("You already have an account.")
    else:
        await ack("Account created.")


@app.event("app_mention")
async def handle_app_mentions(context, say, logger):
    assert context.get("foo") == "FOO"
    await say("Hi! I'm here to make sure you are at your most productive!")


@app.message()
async def handle_message(message, client, say):
    if message["user"] == "U05RME1DRDG":
        return
    text = message["text"]
    info = await app.client.users_info(user=message["user"])
    result = await handle_chat(text, info)
    if result is not None:
        await say(result)


from fastapi import FastAPI, Request, Depends

api = FastAPI()

def get_foo():
    yield "FOO"


@api.post("/slack/events")
async def endpoint(req: Request, foo: str = Depends(get_foo)):
    return await app_handler.handle(req, {"foo": foo})


# pip install -r requirements.txt
# export SLACK_SIGNING_SECRET=***
# export SLACK_BOT_TOKEN=xoxb-***
# uvicorn async_app_custom_props:api --reload --port 3000 --log-level warning
