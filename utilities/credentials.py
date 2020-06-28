# Should be in gitignore. Should NOT be committed because it might contain sensitive information.
# we separate this file from params.py so that that file does not contain sensitive information

# Optionally change. If left as None, it will need manual typing each run
# this is your Google account username
username = None

# how you save your password is up to you.
# If you'd prefer not to save it, then delete everything except the last line below
# If you'd like to adapt the following, then...
# create a .py file containing nothing but your password, and change the path below.
# If you get the following error, you have 2FA enabled:
# gkeepapi.exception.LoginException: ('NeedsBrowser', 'To access your account, you must sign in on the web. Touch Next to start browser sign-in.')
# Solution: create and use a Google app password instead of your Google account pw.
try:
    with open('PATH_TO_PW_FILE.py') as f:
        password = f.read()
except FileNotFoundError:
    password = None