from GKeepToCalc.utilities.utility_functions import *

def test_is_est_xx_mins_line():
    # returns the result of re.search on a given line
    assert is_est_xx_mins_line('est 45 mins').group() == 'est 45 min'
    assert is_est_xx_mins_line('Est 102 mins').group() == 'Est 102 min'
    assert is_est_xx_mins_line('Est 65 mins').group() == 'Est 65 min'
    assert is_est_xx_mins_line('Est 68 mins').group() == 'Est 68 min'
    assert is_est_xx_mins_line('Est 6 mins') is None
    assert is_est_xx_mins_line('Est 58.2 mins') is None



