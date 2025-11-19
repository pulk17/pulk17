import requests
import json
import sys
from datetime import datetime

username = sys.argv[1]

API_URL = "https://leetcode-stats-api.herokuapp.com/" + username

# Fetch stats
r = requests.get(API_URL)
data = r.json()

if "submissionCalendar" not in data:
    raise Exception("Unable to fetch LC activity. Username may be wrong.")

# submissionCalendar is a dict: timestamp → count
calendar = data["submissionCalendar"]

# Convert to snake generator format
grid = []
for ts, count in calendar.items():
    day = datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
    grid.append({
        "date": day,
        "count": count
    })

# Save to file
output = {
    "activity": grid, 
    "total_days": len(grid)
}

with open("data/activity.json", "w") as f:
    json.dump(output, f, indent=2)

print("✅ LeetCode activity saved → data/activity.json")
