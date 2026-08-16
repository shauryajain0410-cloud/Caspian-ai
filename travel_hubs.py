"""
Approximate one-way travel time and cost from Guwahati (the default hub for
this bot's current user base — IITG students, per the form data) to popular
Northeast India destinations.

`confidence` marks how solid each number is:
    "verified"  - cross-checked against multiple live travel-site sources
    "estimate"  - a reasonable placeholder, NOT yet verified — replace with
                  real data (e.g. Google Maps Distance Matrix API) before
                  relying on it for real bookings.
"""

TRAVEL_INFO = {
    "shillong":    {"one_way_hours": 3.5,  "shared_cost": 650,  "confidence": "verified"},
    "cherrapunji": {"one_way_hours": 5.5,  "shared_cost": 900,  "confidence": "estimate"},
    "sohra":       {"one_way_hours": 5.5,  "shared_cost": 900,  "confidence": "estimate"},
    "kaziranga":   {"one_way_hours": 4.0,  "shared_cost": 500,  "confidence": "verified"},
    "pobitora":    {"one_way_hours": 1.5,  "shared_cost": 300,  "confidence": "estimate"},
    "kohima":      {"one_way_hours": 5.0,  "shared_cost": 700,  "confidence": "verified"},
    "dzukou":      {"one_way_hours": 6.0,  "shared_cost": 800,  "confidence": "estimate"},
    "dzokou":      {"one_way_hours": 6.0,  "shared_cost": 800,  "confidence": "estimate"},
    "haflong":     {"one_way_hours": 6.0,  "shared_cost": 700,  "confidence": "estimate"},
    "imphal":      {"one_way_hours": 10.0, "shared_cost": 1200, "confidence": "verified"},
    "manipur":     {"one_way_hours": 10.0, "shared_cost": 1200, "confidence": "verified"},
    "gangtok":     {"one_way_hours": 11.5, "shared_cost": 1200, "confidence": "verified"},
    "sikkim":      {"one_way_hours": 11.5, "shared_cost": 1200, "confidence": "verified"},
    "aizawl":      {"one_way_hours": 12.0, "shared_cost": 1200, "confidence": "estimate"},
    "mizoram":     {"one_way_hours": 12.0, "shared_cost": 1200, "confidence": "estimate"},
    "ziro":        {"one_way_hours": 9.0,  "shared_cost": 1000, "confidence": "estimate"},
    "arunachal":   {"one_way_hours": 9.0,  "shared_cost": 1000, "confidence": "estimate"},
    "tawang":      {"one_way_hours": 14.0, "shared_cost": 1500, "confidence": "verified"},
    "bhutan":      {"one_way_hours": 5.0,  "shared_cost": 800,  "confidence": "estimate"},
    "nagaland":    {"one_way_hours": 5.0,  "shared_cost": 700,  "confidence": "verified"},
    "meghalaya":   {"one_way_hours": 3.5,  "shared_cost": 650,  "confidence": "verified"},
    "assam":       {"one_way_hours": 2.0,  "shared_cost": 400,  "confidence": "estimate"},
}

DEFAULT_TRAVEL = {"one_way_hours": 6.0, "shared_cost": 800, "confidence": "estimate"}


def lookup_travel(destination_name):
    name = str(destination_name).lower()

    matches = [
        (keyword, info)
        for keyword, info in TRAVEL_INFO.items()
        if keyword in name
    ]

    if not matches:
        return DEFAULT_TRAVEL

# For multi-destination trips, use the longest travel time/cost
    return max(
    (info for _, info in matches),
    key=lambda x: x["one_way_hours"]
)


def min_free_days_needed(one_way_hours):
    """
    Bucket one-way travel time into how many total free days a trip needs
    before it's worth doing rather than being consumed by transit.
    """
    if one_way_hours <= 6:
        return 2
    if one_way_hours <= 10:
        return 3
    if one_way_hours <= 16:
        return 5
    return 7
