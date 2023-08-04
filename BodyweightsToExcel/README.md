Bodyweights2Calc retrieves bodyweights from Google Keep and writes them to a local xlsx file.

*How it works*:
1) Bodyweights2Calc finds the (singular) Google Keep note whose title matches the BODYWEIGHTS_NOTE_TITLE value set in params.py. Bodyweights are expected in the note's text (not title) in a format like this:
"80.1, 80.3, 80.2, 81,"
Each number indicates the user's bodyweight on a given day. The program expects one value for every day. "?, " can be used in place of a forgotten or not logged value.

2) It writes each of those bodyweights to the cell neighboring the date on which that measurement was taken, in the local xlsx file. Precautions will be taken: for example, if there are too few or too many bodyweights provided, the user will be prompted to insert or delete a measurement. 

3) Once complete, the program will tidy up, removing all but the last X measurements from the Google Keep note (where X is an integer specified by the HISTORY_LENGTH parameter in params.py).
