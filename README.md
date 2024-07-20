# OSRS_Drop_CDF
![OSRS_LOGO](assets/LOGO.png)

## Purpose
This program allows you to explore the statistics of Old School Runescape monster drop rates. You can test different kill counts and percentages to see your estimated probabilities of going on or off rate!

## Changes In Progress
* Fix the histogram functionality where it will constantly update even if a slider is clicked on in the same position.
* Implement objects such as the Lunar Chest, Chest (Tombs of Amascut), etc. 

## Package Installation
It is HIGHLY recommended to use a virtual environment and use:
`pip install -r requirements.txt` 
to obtain the required packages and version as easily as possible.

## Important Note
The included file 'use-monsters-complete.json' needs to be pasted into your personal venv in osrsreboxed\docs folder and renamed to monsters-complete.json. This will ensure you have an updated list of monsters.

Please reach out to me if you have feedback, bug reports, etc! This project is my very first foray into Dash apps, and I have zero experience with teh OSRS Wiki APIs (feel free to fork and help out in that sense for getting the JSONs updated).
