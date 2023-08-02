This is a personal project. This means you can use it as you like, but please note that I expect nothing of you, and promise nothing to you.

# What this repo contains

A set of tools facilitating interactions between source files (either Google Keep Notes via API, or local text files),
and a local xlsx file.

- BodyweightsToExcel retrieves bodyweights from source files and writes them to an xlsx file.
- WorkoutsToExcel does the same with workouts.
- KeepPruner deletes redundant source files.

For more details, consult their README files.

# How to use these scripts

- Glance over the code to see if it does what you want
- Set variables in utilities/params.py
- Do a trial run
- If it works, consider scheduling it, e.g. via cron job to run it regularly, and maybe forking it, if you'd like to adjust the code to your needs.

# Worth noting

- The library used for Google Keep API is unofficial, and **may break** at any time.
- The wiki documentation may be a bit dated, and I make no promises that the rest of the documentation is fully current.

These programs are distributed under the MIT license. They're free software, without warranty.
