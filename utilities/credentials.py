import os

username = os.environ.get("GKEEP_EMAIL")
assert username

# if no password is provided, the user will be prompted for manual entry later
password = os.environ.get("KEEP_PASSPHRASE")

# If you get the following error, you have 2FA enabled:
# gkeepapi.exception.LoginException: ('NeedsBrowser', 'To access your account, you must sign in on the web. Touch Next to start browser sign-in.')
# Solution: create and use a Google app password instead of your Google account pw.