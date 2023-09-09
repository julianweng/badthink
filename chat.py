from langchain.llms import OpenAI
from langchain.schema.messages import SystemMessage, HumanMessage
from yaml import safe_load

from app import database
from financial import create_account, add_money, subtract_money

llm = OpenAI()

instructions = """
You are a strict corporate policy enforcer. You check whether messages adhere to the following rules:

- Messages must not be disparaging to the boss.
- No complaints about working conditions
- Only positive emotions are allowed.
- Employees must only say yes.
- Clearly non-work messages, including but not limited to social events and the weather, are prohibited.

You will be given a message and only a message. Return a YAML response with:
- is_violation: true or false
- infraction_severity: 1 to 5
- reprimand: Passive-aggressive, threatening warning explaining the infraction

Keep in mind that the user has had {} infractions in the past.

Here is the message:

"""


async def handle_chat(text, user):
    user_info = user["user"]

    if "Badthink" in text:
        return
    user = database["Users"].find_one({"_id": user_info["id"]})
    if user is None:
        await create_account(user_info["id"], user_info["email"])
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

        s = await subtract_money(
            user_info["id"], parsed["infraction_severity"]*10, parsed["reprimand"]
        )
        if not s:
            print("oh no")

        return parsed["reprimand"]
    except BaseException as e:
        print("OH NO!")
        print(result)
        print(e)
        return "Your message broke our policy enforcer. We have a zero-tolerance policy against hacking. A $1000 fee will be assessed."
