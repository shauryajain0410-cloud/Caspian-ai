import os

from dotenv import load_dotenv

load_dotenv()

from trip_planner import generate_trip
from parse_utils import parse_budget, parse_free_window

from caspian_sdk import CommClient

user_state = {}
client = CommClient()

customer = client.create_customer("Trip Planner")
agent = client.create_agent("Travel Agent")

# connection = client.connect_email(
#     customer["id"],
#     agent["id"],
#     username="tripplanner2_shaurya_02",
# )
# print(f"Email Address: {connection['address']}")

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not telegram_token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set -- check your .env file.")

telegram = client.connect_telegram(telegram_token, customer["id"], agent["id"])

print("Telegram Connected!")

WELCOME = """Hey there! \U0001F44B I'm your Northeast India trip planner.

Tell me a bit about your trip and I'll find you some great options, with a full cost breakdown and itinerary.

Let's start -- what's your budget? \U0001F4B0"""


@client.on_message
def handle(message):
    user_id = message.sender["address"]

    if user_id not in user_state:
        user_state[user_id] = {"step": "budget"}
        message.reply(WELCOME)
        return

    state = user_state[user_id]

    if state["step"] == "budget":
        budget = parse_budget(message.text)
        if budget is None:
            message.reply("I couldn't quite catch that -- mind giving me a number, like 5000 or 5k? \U0001F642")
            return
        state["budget"] = budget
        state["step"] = "free_window"
        message.reply(
            "Nice! And when are you free? You can say something like "
            "\"Aug 28 to Aug 30\", or just tell me how many days, like \"3\"."
        )
        return

    if state["step"] == "free_window":
        window = parse_free_window(message.text)
        if window is None:
            message.reply(
                "Hmm, I couldn't figure that out -- try something like "
                "\"Aug 28-30\" or just a number of days, like \"3\"."
            )
            return
        state["free_days"] = window["free_days"]
        state["free_window"] = window
        state["step"] = "city"
        message.reply(f"Got it -- {window['free_days']:.0f} day(s) to play with! Which city are you starting from?")
        return

    if state["step"] == "city":
        if "guwahati" not in message.text.lower():
            message.reply("For now, I can only plan trips starting from Guwahati.")
            return

        state["city"] = "Guwahati"
        state["step"] = "interest"
        message.reply("Perfect. Last one -- what kind of trip are you after? (Adventure / Nature / Culture / Relaxation)")
        return

    if state["step"] == "interest":
        state["interest"] = message.text
        details = {
            "budget": state["budget"],
            "free_days": state["free_days"],
            "city": state["city"],
            "interest": state["interest"],
        }
        message.reply(generate_trip(details))
        del user_state[user_id]
        return

    message.reply(WELCOME)


print("Agent is running...")
client.listen()
