import pandas as pd

from dataset import df
from travel_hubs import lookup_travel, min_free_days_needed

# NOTE: these keywords are matched against your destination column text, not
# state names -- your dataset uses place names ("Dzokou", "Aizawl", "TAWANG")
# rather than state names, so mapping to "nagaland"/"manipur" (as the
# original code did) never matched anything and silently returned zero
# results for "culture". Update this map as your dataset grows.
INTEREST_MAP = {
    "adventure": ["shillong", "meghalaya", "cherrapunji", "cherapunji", "laitlum",
                  "dawki", "tawang", "arunachal", "ziro", "dzukou", "dzokou"],
    "nature": ["sikkim", "gangtok", "darjeeling", "kaziranga", "pobitora", "meghalaya"],
    "culture": ["dzukou", "dzokou", "aizawl", "mizoram", "tawang"],
    "relaxation": ["assam", "kaziranga", "pobitora", "dima hasao", "haflong", "garbhanga", "sikkim"],
}

# Rough Rs/day for stay + food + local transport at homestay/budget-travel
# level, based on researched NE India backpacker costs. Not destination-
# specific yet -- swap in real per-destination numbers as they're gathered.
DAILY_STAY_FOOD_ESTIMATE = 1000


def generate_trip(details):
    """
    details:
        budget    - numeric, total trip budget in INR
        free_days - numeric, total days the user is free (travel included)
        city      - starting city (informational for now; travel-hub data
                    below is Guwahati-based)
        interest  - one of INTEREST_MAP keys (case-insensitive)
    """
    interest = str(details.get("interest", "")).strip().lower()
    places = INTEREST_MAP.get(interest)

    if not places:
        return (
            "Hmm, I don't have that interest in my list yet \U0001F648 "
            "Could you pick one of: Adventure, Nature, Culture, or Relaxation?"
        )

    frames = [
    df[df["destination"].str.lower().str.contains(place.lower(), na=False)]
    for place in places
]

    frames = [f for f in frames if not f.empty]

    if not frames:
        return "I couldn't find any trips for that interest yet -- mind trying a different one?"

    matches = pd.concat(frames).drop_duplicates().copy()
    matches["budget"] = pd.to_numeric(matches["budget"], errors="coerce")
    matches["days"] = pd.to_numeric(matches["days"], errors="coerce")
    matches = matches.dropna(subset=["budget", "days"])

    try:
        budget = float(details["budget"])
        free_days = float(details["free_days"])
    except (TypeError, ValueError):
        return "Sorry, I couldn't quite catch your budget or your free days -- mind trying again?"

    # Attach travel feasibility per row, based on the destination name.
    matches["one_way_hours"] = matches["destination"].apply(lambda d: lookup_travel(d)["one_way_hours"])
    matches["min_days_needed"] = matches["one_way_hours"].apply(min_free_days_needed)

    feasible = matches[matches["min_days_needed"] <= free_days]
    if feasible.empty:
        closest = matches.sort_values("min_days_needed").iloc[0]
        return (
            f"With {free_days:.0f} day(s) free, most {interest} trips I know of need more time just to "
            f"get there and back comfortably -- the closest fit is {closest['destination'].strip()}, "
            f"which really wants about {closest['min_days_needed']:.0f} days including travel. "
            "Want to try a longer window, or a different interest closer to home?"
        )

    feasible = feasible.copy()
    feasible["estimated_total"] = (
    feasible["destination"].apply(lambda d: lookup_travel(d)["shared_cost"]) * 2
    + DAILY_STAY_FOOD_ESTIMATE * feasible["days"]
)

    affordable = feasible[feasible["estimated_total"] <= budget]
    if affordable.empty:
        return f"Nothing in that budget of Rs.{budget:.0f} yet for a {interest} trip -- want to try nudging it up a bit?"

    affordable = affordable[affordable["days"] <= free_days]
    if affordable.empty:
        return f"I found trips in budget, but not ones that fit inside {free_days:.0f} day(s) -- try allowing a bit more time?"

    affordable = affordable.copy()
    affordable["score"] = (
        (budget - affordable["budget"]).abs()
        + (free_days - affordable["days"]).abs() * 100
    )

    top_trips = affordable.sort_values("score").head(3).copy()

    response = f"Found some great {interest} trips that fit your {free_days:.0f} day(s) and budget! \U0001F392\n\n"

    for _, trip in top_trips.iterrows():
        destination = str(trip["destination"]).strip()
        travel = lookup_travel(destination)
        round_trip_cost = travel["shared_cost"] * 2
        stay_food_days = max(trip["days"], 1)
        stay_food_cost = DAILY_STAY_FOOD_ESTIMATE * stay_food_days
        estimate_flag = " (rough estimate -- please verify before booking)" if travel["confidence"] == "estimate" else ""

        response += (
            f"\U0001F4CD {destination} -- about {travel['one_way_hours']:.1f} hrs each way from Guwahati\n"
            f"Similar travelers spent ~Rs.{trip['budget']:.0f} over {trip['days']:.0f} day(s)\n\n"
            f"Rough cost breakdown{estimate_flag}:\n"
            f"  Travel (round trip, shared taxi): ~Rs.{round_trip_cost:.0f}\n"
            f"  Stay + food + local costs (~Rs.{DAILY_STAY_FOOD_ESTIMATE}/day x {trip['days']:.0f}): ~Rs.{stay_food_cost:.0f}\n"
            f"  Estimated total: ~Rs.{round_trip_cost + stay_food_cost:.0f}\n\n"
            f"Itinerary:\n{trip['itinerary']}\n\n"
            "---------------\n\n"
        )

    response += "Want me to go deeper on any of these, or show you a couple more options?"
    return response
