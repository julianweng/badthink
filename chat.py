from langchain.llms import OpenAI
from langchain.schema.messages import SystemMessage, HumanMessage
from yaml import safe_load
import sendgrid
import os

from app import database
from financial import create_account, add_money, subtract_money

llm = OpenAI()
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))

instructions = """
You are a corporate policy enforcer. You check whether messages adhere to the following rules:

- Messages must not be disparaging to the boss.
- No complaints about working conditions
- Only positive emotions are allowed.
- Employees must only say yes.
- Clearly non-work messages, including but not limited to social events and the weather, are prohibited.

You will be given a message and only a message. Return a YAML response with:
- is_violation: true or false
- infraction_severity: 1 to 5
- reprimand: Passive-aggressive, threatening warning explaining the infraction

Keep in mind that the user has incurred {} infraction points in the past.

Here is the message:

"""


async def handle_chat(text, user):
    user_info = user["user"]

    if "Badthink" in text:
        return
    user = database["Users"].find_one({"_id": user_info["id"]})
    if user is None:
        await create_account(user_info["id"], user_info["profile"]["email"])
        user = database["Users"].find_one({"_id": user_info["id"]})

    offenses = user["infractions"]

    system_message = SystemMessage(content=instructions.format(offenses))

    human_message = HumanMessage(content=text)

    result = llm.predict_messages([system_message, human_message]).content

    # Trim everything before the first occurrence of "is_violation"
    try:
        index = result.find("is_violation")
        if index == -1:
            raise Exception("No is_violation found")
        result = result[index:]
        parsed = safe_load(result)

        if not parsed["is_violation"]:
            return None
        
        reprimand = parsed["reprimand"]

        s = await subtract_money(
            user_info["id"], parsed["infraction_severity"]*10, parsed["reprimand"]
        )
        if not s:
            print("oh no")
        
        offenses += parsed["infraction_severity"]
        database["Users"].update_one(
            {"_id": user_info["id"]}, {"$set": {"infractions": offenses}}
        )
        
        data = {
        "personalizations": [
            {
            "to": [
                {
                "email": user_info["profile"]["email"]
                }
            ],
            "subject": "Your Infraction"
            }
        ],
        "from": {
            "email": "noreply@badth.ink"
        },
        "content": [
            {
            "type": "text/plain",
            "value": f"You have been fined ${parsed['infraction_severity']*10} for the following infraction:\n\n{parsed['reprimand']}\n\n ~ Badthink Team"
            }
        ]
        }
        if parsed["infraction_severity"] >= 4:
            sg.client.mail.send.post(request_body=data)
            reprimand += "\n\nThis was a particularly egregious violation, so we have sent a notification via email as well."
        return reprimand
    except BaseException as e:
        print("OH NO!")
        print(result)
        print(e)
        return "Your message broke our policy enforcer. We have a zero-tolerance policy against hacking. A $1000 fee will be assessed."
