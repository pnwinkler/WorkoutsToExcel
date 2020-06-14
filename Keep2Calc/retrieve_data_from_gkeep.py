# retrieves all entries from https://keep.google.com/u/0/, as logged in user
# concatenates it, then saves it to desktop as name specified in source_path

import gkeepapi
import getpass
from utilities.params import source_path


def write_gkeep_data_to_desktop():
    # source_path is the file keep_to_calc will read in from
    keep = gkeepapi.Keep()

    try:
        from utilities.credentials import username
    except FileNotFoundError:
        # to avoid typing your username each time, create a file called credentials.py with the following line:
        # username = 'YOUR_USERNAME@gmail.com'
        username = input('Google Keep username: ')
    if username is None:
        # it's not set in credentials.py
        username = input('Google Keep username: ')

    # takes in password. Obscures it as it's entered
    password = getpass.getpass('Google Keep password: ')
    print('Logging in...')
    keep.login(username, password)

    # retrieves a list of Note objects
    print('Retrieving notes')
    gnotes = keep.all()
    if not gnotes:
        raise ValueError('No notes found. Incorrect username or password?')

    with open(source_path, 'w') as f:
        for gnote in gnotes:
            f.write(gnote.title + '\n' + gnote.text + '\n\n\n')