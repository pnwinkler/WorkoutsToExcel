# retrieves all entries from https://keep.google.com/u/0/, as logged in user
# concatenates it, then saves it to desktop as name specified in SOURCE_PATH

from GKeepToCalc.utilities.params import SOURCE_PATH
import GKeepToCalc.utilities.utility_functions as uf


def write_gkeep_data_to_desktop():
    # SOURCE_PATH is
    # 1) the file keep_to_calc will read in from
    # 2) a place for the user to verify that only the correct notes were retrieved from Keep
    keep = uf.login_and_return_keep_obj()
    gnotes = uf.retrieve_notes(keep)

    with open(SOURCE_PATH, 'w') as f:
        for gnote in gnotes:
            f.write(gnote.title + '\n' + gnote.text + '\n\n\n')
