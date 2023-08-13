from GKeepToCalc.utilities.utility_functions import *

# todo: add more tests here

def test_is_est_xx_mins_line():
    # returns the result of re.search on a given line
    assert is_est_xx_mins_line('est 45 mins')
    assert is_est_xx_mins_line('Est 102 mins')
    assert is_est_xx_mins_line('Est 65 mins')
    assert is_est_xx_mins_line('Est 68 mins')
    assert is_est_xx_mins_line('Est 6 mins')
    assert is_est_xx_mins_line('Est 58.2 mins') is False
