## Torn Ranked War Analyzer

For the web game torn.com

Downloads attacks and revives from completed ranked wars and generates an html file containing graphs from the data to help visualize faction performance. Requires an API key with Faction API access.

Current charts/graphs:

- Overall basic stats chart
- Respect Gain and Loss by Faction (Line)
- War Attacks over Time by Faction (Line)
- Assists over Time by Faction (Line)
- Net Score per Player (Bar)
- Attacks Made and Received per Player (Overlapping Bar)
- Revives Received over Time (Line)
- Revives Received over Time by Player (Scatter)
- Revives Received by Player (Stacked Bar)

Note: Due to Torn's API limitations, the requests are rate limited to every 30 seconds, so downloading the attacks and revives can take some time. When the attacks and revives finish downloading, csv files are created and can be imported in the future for that specific war.

Install:
```
git clone 
pip install -r requirements.txt
```

Usage:

Run waranalyzer.py and follow the console prompts