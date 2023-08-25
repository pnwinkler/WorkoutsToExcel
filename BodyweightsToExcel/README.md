This module retrieves bodyweights and writes them to the target file.

**How it works** _(subject to change)_
1) The bodyweights note is identified. Bodyweights matching the following format are expected in the note's text (not title):
"80.1, 80.3, 80.2, 81,"
Each number indicates the user's bodyweight on a given day. The program expects one value for every day. "?, " can be  in place of a missing value.

2) Each bodyweight is written to the cell neighboring the date on which that measurement was taken, in the target file. 

3) Once complete, all but the last X measurements from the source note will be removed from the note (where X is an integer specified by the HISTORY_LENGTH parameter in params.py).
