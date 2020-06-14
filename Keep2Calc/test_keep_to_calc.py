from keep2calc.keep_to_calc import *
# perhaps tests is reserved? PyCharm doesn't want to import it

path_to_tests_folder = os.path.join(os.getcwd(), "keep2calc_tests")
single_workout1_path = os.path.join(path_to_tests_folder, "single_workout1")
single_workout2_path = os.path.join(path_to_tests_folder, "single_workout2")
single_workout3_path = os.path.join(path_to_tests_folder, "single_workout3")
multiple_workouts1_path = os.path.join(path_to_tests_folder, "multiple_workouts1")
multiple_workouts2_path = os.path.join(path_to_tests_folder, "multiple_workouts2")
multiple_workouts3_path = os.path.join(path_to_tests_folder, "multiple_workouts3")
noisy_data_single_workout1_path = os.path.join(path_to_tests_folder, "noisy_data_single_workout1")


# def test_accepts_rings_and_treadmill():
#     pass


def test_is_est_xx_mins_line():
    assert is_est_xx_mins_line('est 45 mins').group() == 'est 45 min'
    assert is_est_xx_mins_line('Est 102 mins').group() == 'Est 102 min'
    assert is_est_xx_mins_line('Est 65 mins').group() == 'Est 65 min'
    assert is_est_xx_mins_line('Est 68 mins').group() == 'Est 68 min'


def test_is_dateline():
    assert is_dateline('22 November, day 3') == True
    assert is_dateline('22 November, day 2') == True
    assert is_dateline('22 Nov, day 2') == True
    assert is_dateline('November 22, day 2') == True
    assert is_dateline('November 22, day 2') == True

    assert is_dateline('1 Apr') == True
    assert is_dateline('01 Apr') == True
    assert is_dateline('12 Sep') == True
    assert is_dateline('15 May') == True
    assert is_dateline('12 September') == True
    assert is_dateline('1 september') == True
    assert is_dateline('2 Jan') == True
    assert is_dateline('2 jan') == True
    assert is_dateline('02 Jan') == True
    assert is_dateline('2 January') == True
    assert is_dateline('02 January') == True
    assert is_dateline('02 january') == True
    assert is_dateline('03 nov') == True
    assert is_dateline('15 mar') == True
    assert is_dateline('1 mar') == True

    # we reject invalid February dates
    assert is_dateline('29 February 2019') == False
    assert is_dateline('29 February 2020') == True

    # we don't test for MON DD format. We don't accept it

    # we don't want to match lines with a month but no date
    assert is_dateline('September') == False
    assert is_dateline('August') == False

    assert is_dateline('Jan') == False
    assert is_dateline('jan') == False
    assert is_dateline('hi') == False
    assert is_dateline('17') == False
    assert is_dateline('est 65') == False
    assert is_dateline('may be') == False
    assert is_dateline('maybe') == False


def test_is_commentline():
    assert is_commentline('/doot') == True
    assert is_commentline('(aserfwefwef aowseihj sdfsdf') == True
    assert is_commentline('/') == True
    assert is_commentline('(') == True
    assert is_commentline('(75kg:8,8,8 / 8,8,7)') == True
    assert is_commentline('/4x8 is a grinder') == True
    assert is_commentline('/Minor overreach') == True

    assert is_commentline('hi') == False
    assert is_commentline('12312') == False
    assert is_commentline('Squat 90kg: 8,8,8') == False
    assert is_commentline('Squat 110kg:5,5,5,5') == False
    assert is_commentline('Assisted pull up -15kg:12,15,6,10;') == False


def test_return_clean_data():
    # copies all non-extraneous workout data from source_path into a matrix
    # then returns that matrix
    # we feed it a source path and confirm that it saves all workouts from that source
    # note that we do NOT check the contents of each workout here (so far)

    # we check length because otherwise we get weird problems with the list contents
    # being identical, but the commas separating items being invalidly positioned
    r1 = return_clean_data(multiple_workouts3_path)
    assert len(r1) == 2



# def test_strip_num_x_nums():
#     # regex to match: 4x7 , 3x5 , 5x6 min , 7x4+, 2x10-12 etc
#     # I don't even use these features any more
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#
#     # regex to match: kilogram range comma and trailing space (e.g. '75-85kg, ')
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#
#     # regex to match: exercise-set count, leading and trailing spaces. e.g. ' 3 sets '
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = True
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#     # assert strip_num_x_nums('') = False
#
#     assert True

'''
def test_copy_and_parsing():
    # test that the program copies and parses a workout correctly
    # test single workouts (files containing nothing but 1 workout)
    assert parse_it(copy_days_data(single_workout1_path)) == keep2calc_tests.tst_solutions.single_workout1_solution
    assert parse_it(copy_days_data(single_workout2_path)) == keep2calc_tests.tst_solutions.single_workout2_solution
    assert parse_it(copy_days_data(single_workout3_path)) == keep2calc_tests.tst_solutions.single_workout3_solution

    # test copying and parsing for files containing multiple workouts
    # note that in the case of multiple workouts, it should only return the first workout!
    assert parse_it(copy_days_data(multiple_workouts1_path)) == keep2calc_tests.tst_solutions.multiple_workout1_solution
    assert parse_it(copy_days_data(multiple_workouts2_path)) == keep2calc_tests.tst_solutions.multiple_workout2_solution

    # test copying and parsing for files containing noise: data unrelated to workouts
    # in this test case, there's a fabricated event preceding the workout in the input file
    # it has no est xx mins line or workout exercises
    assert parse_it(
        copy_days_data(noisy_data_single_workout1_path)) == keep2calc_tests.tst_solutions.noisy_data_single_workout1_solution
'''
