from Keep2Calc.keep_to_calc import *
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
def test_is_dateline():
    assert is_dateline('22 November, day 3') 
    assert is_dateline('22 November, day 2') 
    assert is_dateline('22 Nov, day 2') 
    assert is_dateline('November 22, day 2') 
    assert is_dateline('November 22, day 2') 

    assert is_dateline('1 Apr') 
    assert is_dateline('01 Apr') 
    assert is_dateline('12 Sep') 
    assert is_dateline('15 May') 
    assert is_dateline('12 September') 
    assert is_dateline('1 september') 
    assert is_dateline('2 Jan') 
    assert is_dateline('2 jan') 
    assert is_dateline('02 Jan') 
    assert is_dateline('2 January') 
    assert is_dateline('02 January') 
    assert is_dateline('02 january') 
    assert is_dateline('03 nov') 
    assert is_dateline('15 mar') 
    assert is_dateline('1 mar') 

    # we reject invalid February dates (2020 has no 29th of February)
    assert is_dateline('29 February 2019') is False
    assert is_dateline('29 February 2020') 

    # we don't test for MON DD format. We don't accept it

    # we don't want to match lines with a month but no date
    assert is_dateline('September') is False
    assert is_dateline('August') is False

    assert is_dateline('Jan') is False
    assert is_dateline('jan') is False
    assert is_dateline('hi') is False
    assert is_dateline('17') is False
    assert is_dateline('est 65') is False
    assert is_dateline('may be') is False
    assert is_dateline('maybe') is False


def test_is_commentline():
    assert is_commentline('/doot') 
    assert is_commentline('(aserfwefwef aowseihj sdfsdf') 
    assert is_commentline('/') 
    assert is_commentline('(') 
    assert is_commentline('(75kg:8,8,8 / 8,8,7)') 
    assert is_commentline('/4x8 is a grinder') 
    assert is_commentline('/Minor overreach') 

    assert is_commentline('hi') is False
    assert is_commentline('12312') is False
    assert is_commentline('Squat 90kg: 8,8,8') is False
    assert is_commentline('Squat 110kg:5,5,5,5') is False
    assert is_commentline('Assisted pull up -15kg:12,15,6,10;') is False


# def test_return_clean_data():
#     # copies all non-extraneous workout data from source_path into a matrix
#     # then returns that matrix
#     # we feed it a source path and confirm that it saves all workouts from that source
#     # note that we do NOT check the contents of each workout here (so far)
#
#     # we check length because otherwise we get weird problems with the list contents
#     # being identical, but the commas separating items being invalidly positioned
#     r1 = return_clean_data(multiple_workouts3_path)
#     assert len(r1) == 2



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
