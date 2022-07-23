from GKeepToCalc.Keep2Calc.keep_to_calc import *
from GKeepToCalc.Keep2Calc.keep2calc_tests.tst_solutions import *

path_to_tests_folder = os.path.join(os.getcwd(), "keep2calc_tests")
single_workout1_path = os.path.join(path_to_tests_folder, "single_workout1")
single_workout2_path = os.path.join(path_to_tests_folder, "single_workout2")
single_workout3_path = os.path.join(path_to_tests_folder, "single_workout3")
single_cardio1_path = os.path.join(path_to_tests_folder, "single_cardio1")
single_shadowboxing1_path = os.path.join(path_to_tests_folder, "single_shadowboxing1")
multiple_workouts1_path = os.path.join(path_to_tests_folder, "multiple_workouts1")
multiple_workouts2_path = os.path.join(path_to_tests_folder, "multiple_workouts2")
multiple_workouts3_path = os.path.join(path_to_tests_folder, "multiple_workouts3")
noisy_data_single_workout1_path = os.path.join(path_to_tests_folder, "noisy_data_single_workout1")


def test_is_commentline():
    assert line_is_comment('/doot')
    assert line_is_comment('(aserfwefwef aowseihj sdfsdf')
    assert line_is_comment('/')
    assert line_is_comment('(')
    assert line_is_comment('(75kg:8,8,8 / 8,8,7)')
    assert line_is_comment('/4x8 is a grinder')
    assert line_is_comment('/Minor overreach')

    assert line_is_comment('hi') is False
    assert line_is_comment('12312') is False
    assert line_is_comment('Squat 90kg: 8,8,8') is False
    assert line_is_comment('Squat 110kg:5,5,5,5') is False
    assert line_is_comment('Assisted pull up -15kg:12,15,6,10;') is False


# def test_is_dateline():
#     assert is_dateline('22 November, day 3')
#     assert is_dateline('22 November, day 2')
#     assert is_dateline('22 Nov, day 2')
#     assert is_dateline('November 22, day 2')
#
#     assert is_dateline('1 Apr')
#     assert is_dateline('01 Apr')
#     assert is_dateline('12 Sep')
#     assert is_dateline('15 May')
#     assert is_dateline('12 September')
#     assert is_dateline('1 september')
#     assert is_dateline('2 Jan')
#     assert is_dateline('2 jan')
#     assert is_dateline('02 Jan')
#     assert is_dateline('2 January')
#     assert is_dateline('02 January')
#     assert is_dateline('02 january')
#     assert is_dateline('03 nov')
#     assert is_dateline('15 mar')
#     assert is_dateline('1 mar')
#
#     # we reject invalid February dates (2019 has no 29th of February)
#     assert is_dateline('29 February 2019') is False
#     assert is_dateline('29 February 2020')
#
#     # we don't test for MON DD format. We don't accept it
#
#     # we don't want to match lines with a month but no date
#     assert is_dateline('September') is False
#     assert is_dateline('August') is False
#
#     assert is_dateline('Jan') is False
#     assert is_dateline('jan') is False
#     assert is_dateline('hi') is False
#     assert is_dateline('17') is False
#     assert is_dateline('est 65') is False
#     assert is_dateline('may be') is False
#     assert is_dateline('maybe') is False
#

# todo: update tests below for new process

# def test_return_clean_data_matrix():
#     # reads a file, ignores non-workout data, then returns a
#     # matrix, where each list represents one workout verbatim (as a list of strings)
#     # it does NOT remove comments or newlines or add punctuation.
#     # it only copies each line between a dateline and an est xx mins line (inclusive)
#     # into becomes a string inside a list
#
#     assert len(return_list_of_workouts_from_file(single_workout1_path)) == 1
#     assert return_list_of_workouts_from_file(single_workout1_path)[0][0] == '22 November, day 3\n'
#     # capture comment lines
#     assert return_list_of_workouts_from_file(single_workout1_path)[0][2] == '(75kg: 8,8,8,7,7)\n'
#     assert return_list_of_workouts_from_file(single_workout1_path)[0][13] == '/RPE 9.5\n'
#     # do not copy any line after the est xx mins line
#     assert return_list_of_workouts_from_file(single_workout1_path)[0][-1] == 'Est 65 mins\n'
#
#     assert len(return_list_of_workouts_from_file(single_workout2_path)) == 1
#     assert return_list_of_workouts_from_file(single_workout2_path)[0][0] == '21 November, day 2\n'
#     assert return_list_of_workouts_from_file(single_workout2_path)[0][-1] == 'Est ?? mins\n'
#
#     assert len(return_list_of_workouts_from_file(single_workout3_path)) == 1
#     assert return_list_of_workouts_from_file(single_workout3_path)[0][0] == '24 November, day 4\n'
#     # if there's no line after the est xx mins line, there should be no newline in the est xx mins line
#     assert return_list_of_workouts_from_file(single_workout3_path)[0][-1] == 'Est 91 mins'
#
#     assert len(return_list_of_workouts_from_file(single_cardio1_path)) == 1
#     assert return_list_of_workouts_from_file(single_cardio1_path)[0][0] == '3 October\n'
#     assert return_list_of_workouts_from_file(single_cardio1_path)[0][1] == "Cardio (target heart rate 120-130): 45 mins\n"
#     assert return_list_of_workouts_from_file(single_cardio1_path)[0][-2] == "\n"
#     assert return_list_of_workouts_from_file(single_cardio1_path)[0][-3] == "+ band dislocates\n"
#     assert return_list_of_workouts_from_file(single_cardio1_path)[0][-1] == 'Est 54 mins\n'
#
#     assert len(return_list_of_workouts_from_file(single_shadowboxing1_path)) == 1
#     assert return_list_of_workouts_from_file(single_shadowboxing1_path)[0][0] == '6 October\n'
#     assert return_list_of_workouts_from_file(single_shadowboxing1_path)[0][1] == 'Shadowboxing:\n'
#     assert return_list_of_workouts_from_file(single_shadowboxing1_path)[0][3] == 'front delts\n'
#     assert return_list_of_workouts_from_file(single_shadowboxing1_path)[0][13] == '3x25 jabs\n'
#     assert return_list_of_workouts_from_file(single_shadowboxing1_path)[0][-1] == 'Est 27 mins\n'
#
#     assert len(return_list_of_workouts_from_file(multiple_workouts1_path)) == 3
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[0][0] == '22 November, day 3\n'
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[0][-1] == 'Est 65 mins\n'
#     # doesn't care about date order of workouts. Still copies verbatim.
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[1][0] == '21 November, day 2\n'
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[1][-1] == 'Est ?? mins\n'
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[2][0] == '24 November, day 4\n'
#     assert return_list_of_workouts_from_file(multiple_workouts1_path)[2][-1] == 'Est 91 mins\n'
#
#     assert len(return_list_of_workouts_from_file(multiple_workouts2_path)) == 3
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[0][0] == '7 October\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[0][-1] == 'Est 74 mins\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[1][0] == '5 October\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[1][1] == 'Flat leg press 107kg: 10,10,10\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[1][-1] == 'Est 69 mins\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[2][0] == '1 October\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[2][-1] == 'Est 62 mins\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[2][-3] == '\n'
#     assert return_list_of_workouts_from_file(multiple_workouts2_path)[2][-4] == 'Dead hang\n'
#
#     # we deliberately don't catch the exercises listed up top without an est xx mins line
#     assert len(return_list_of_workouts_from_file(multiple_workouts3_path)) == 2
#     assert return_list_of_workouts_from_file(multiple_workouts3_path)[0][0] == '26 October\n'
#     assert return_list_of_workouts_from_file(multiple_workouts3_path)[0][-1] == 'Est 57 mins\n'
#
#
# def test_return_parsed_data():
#     # expects to read exclusively workout data. (Typically the output of return_list_of_workouts_from_file())
#     # returns a list of lists. Each workout is 1 inner list. Each inner list contains 2 tuples:
#     # each tuple[0] is the date, and each tuple[1] is a string containing a formatted workout
#     assert len(return_parsed_data(single_workout1_path)) == 1
#     assert isinstance(return_parsed_data(single_workout1_path), list)
#     assert isinstance(return_parsed_data(single_workout1_path)[0], tuple)
#     assert isinstance(return_parsed_data(single_workout1_path)[0][0], str)
#     assert isinstance(return_parsed_data(single_workout1_path)[0][1], str)
#     assert return_parsed_data(single_workout1_path)[0][0] == '22 November'
#     # fully parsed and ready to write.
#     assert return_parsed_data(single_workout1_path)[0][1] == single_workout1_solution
#
#     assert len(return_parsed_data(multiple_workouts3_path)) == 2
#     assert return_parsed_data(multiple_workouts2_path)[0][0] == '7 October'
#     assert return_parsed_data(multiple_workouts2_path)[1][0] == '5 October'
#     assert return_parsed_data(multiple_workouts2_path)[0][1] == multiple_workout3_solution_matrix[0]
#     assert return_parsed_data(multiple_workouts2_path)[1][1] == multiple_workout3_solution_matrix[1]
#
#     assert len(return_parsed_data(single_cardio1_path)) == 1
#     assert return_parsed_data(single_cardio1_path)[0][0] == '3 October'
#     assert return_parsed_data(single_cardio1_path)[0][1] == single_cardio1_solution
#
#     assert len(return_parsed_data(single_shadowboxing1_path)) == 1
#     assert return_parsed_data(single_shadowboxing1_path)[0][0] == '6 October'
#     assert return_parsed_data(single_shadowboxing1_path)[0][1] == single_shadowboxing1_solution
