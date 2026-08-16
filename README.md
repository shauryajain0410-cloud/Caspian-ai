# Northeast India Trip Planner Bot

A Telegram bot, built on the [Caspian SDK](https://github.com/TryCaspian/caspian-sdk),
that plans budget trips around Northeast India. Users chat with the bot about
their budget, free days, starting city, and interests, and get back a
cost-broken-down itinerary matched against real traveler data.

Built because we had the idea and the itinerary data, but no live database or
booking backend yet -- this agent fills that gap conversationally instead.

## How it works

1. **`bot.py`** -- connects to Telegram via Caspian's `CommClient`, and walks
   the user through a short conversation (budget -> free days -> city ->
   interest), storing per-user state in memory.
2. **`parse_utils.py`** -- turns messy free-text answers ("5k", "3000-4000",
   "Aug 28 to Aug 30", "3 days") into clean numeric budgets and day counts.
3. **`travel_hubs.py`** -- approximate one-way travel time and shared-taxi
   cost from Guwahati to each destination, plus how many free days a trip of
   that distance realistically needs.
4. **`dataset.py`** -- loads `clean_travel_data.csv`, a small set of real
   past-traveler trips (destination, budget, days, itinerary) into a
   DataFrame.
5. **`trip_planner.py`** -- the core matching logic: filters the dataset by
   interest, checks travel feasibility against the user's free days, checks
   cost against their budget, ranks the closest matches, and formats a
   reply with a full cost breakdown and itinerary.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your real values
python bot.py
```

You'll need:
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- A Caspian API key (from your Caspian dashboard)

## Data

`clean_travel_data.csv` holds real trip data (destination, budget, days,
group info, ratings, itinerary) used to match users to similar past trips.
`travel_hubs.py` marks each travel-time/cost estimate as `"verified"` or
`"estimate"` -- estimates should be replaced with real numbers (e.g. from a
maps/distance API) before this is used for real bookings.

## Known limitations

- Currently only supports trips starting from **Guwahati**.
- Interest categories are fixed: Adventure, Nature, Culture, Relaxation.
- Some travel-time/cost figures are placeholder estimates, not verified.
- No persistent database yet -- conversation state lives in memory and is
  lost on restart.
