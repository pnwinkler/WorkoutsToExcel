import unittest
from functools import partial
from Bodyweights2Calc.main import *
import utilities.params as params


class MockWorkBookClass():
	def __init__(self, matrix: List[List]):
		self.wb = openpyxl.Workbook()
		self.ws = self.wb.active
		self.load_data(matrix)

	def load_data(self, matrix):
		for row in matrix:
			self.ws.append(row)


# 	def cell(self, int_col, int_row):
# 		value =
# 		return MockCell(value=value)


# class MockCell():
# 	def __init__(self, value):
# 		self.value = None

# TODO: test note(s) like the following. This one gets written as "Shadowboxing: . EST 22 mins". Not good.
# TITLE="29 January", TEXT=
'''
Cardio: shadowboxing

EST 22 mins
'''


class MockNoteClass():
	def __init__(self, title, text, trashed=False):
		self.title = title
		self.text = text
		self.trashed = trashed


class MyTestCase(unittest.TestCase):
	# a convenience function, to simplify asserting for raises
	def _assertRaise(self, error, function, *args, **kwargs):
		with self.assertRaises(error):
			return function(*args, **kwargs)


class TestReturnBodyweightsList(MyTestCase):
	# the function being tested can reasonably expect a correctly identified bodyweights note.
	def setUp(self) -> None:
		self.mock_note_1 = MockNoteClass(title="", text="")
		self.mock_note_2 = MockNoteClass(title="3243", text="")
		self.mock_note_3 = MockNoteClass(title="", text="23423")
		self.mock_note_4 = MockNoteClass(title="", text="abcd .")
		self.mock_note_5 = MockNoteClass(title=p.BODYWEIGHTS_NOTE_TITLE, text="abcd .")
		self.mock_note_6 = MockNoteClass(title="74", text="")
		self.mock_note_7 = MockNoteClass(title="74,", text=" ")
		self.mock_note_8 = MockNoteClass(title="74, ", text="")
		self.mock_note_9 = MockNoteClass(title="74, ", text="74, ")
		self.mock_note_10 = MockNoteClass(title="74, ", text="?, ")
		self.mock_note_11 = MockNoteClass(title="74, ", text="?, 72")
		self.mock_note_12 = MockNoteClass(title="74, ", text="?, ?")

		# test grammar
		self.mock_note_13 = MockNoteClass(title="", text="(95.3), ")
		self.mock_note_14 = MockNoteClass(title="", text="(), ")
		self.mock_note_15 = MockNoteClass(title="", text="(, ")
		self.mock_note_16 = MockNoteClass(title="", text="), ")
		self.mock_note_17 = MockNoteClass(title="", text="((), ")
		self.mock_note_18 = MockNoteClass(title="74, 72", text="()), ")

		# test context window
		self.mock_note_19 = MockNoteClass(title="", text="(72.4)")
		self.mock_note_20 = MockNoteClass(title="", text="(72.4),")
		self.mock_note_21 = MockNoteClass(title="", text="(72.4), ")
		self.mock_note_22 = MockNoteClass(title="", text="(72.4, 82.6)")
		self.mock_note_23 = MockNoteClass(title="", text="(72.4, 82.6), 72")
		self.mock_note_24 = MockNoteClass(title="", text="(72.4, 82.6), 72, ")
		self.mock_note_25 = MockNoteClass(title="", text="(72.4, 82.6, 1.142698),")

	def test_extract_bodyweights_lst_from_raw_string(self):
		# assert that a list of string bodyweights is extracted from a raw string
		no_split = partial(extract_bodyweights_from_validated_string, split_on_parenthesis=False)
		self.assertEqual(no_split(""), [])
		self.assertEqual(no_split("82"), ["82"])
		self.assertEqual(no_split("82.2"), ["82.2"])
		self.assertEqual(no_split("82.2,"), ["82.2"])
		self.assertEqual(no_split("(82.2)"), ["82.2"])
		self.assertEqual(no_split("(82.2),"), ["82.2"])
		self.assertEqual(no_split("(82.2), 103.4"), ["82.2", "103.4"])
		self.assertEqual(no_split("(82.2, 103.4)"), ["82.2", "103.4"])
		self.assertEqual(no_split("(82.2, 103.4),"), ["82.2", "103.4"])
		self.assertEqual(no_split(self.mock_note_10.text), ["?"])
		self.assertEqual(no_split(self.mock_note_11.text), ["?", "72"])
		self.assertEqual(no_split(self.mock_note_12.text), ["?", "?"])

		with_split = partial(extract_bodyweights_from_validated_string, split_on_parenthesis=True)
		self.assertEqual(with_split(""), ([], []))
		self.assertEqual(with_split("(82.2, 103.4)"), (["82.2", "103.4"], []))
		self.assertEqual(with_split("(82.2, 103.4),"), (["82.2", "103.4"], []))
		self.assertEqual(with_split("(82.2, 103.4), 103.5"), (["82.2", "103.4"], ["103.5"]))

	def test_validate_bodyweight_note_text(self):
		# this runs validation for split_history_from_uncommitted_bodyweights(...)
		# rudimentary checks on its own. It will be further tested below
		assert _validate_bodyweight_note_text("") is None
		assert _validate_bodyweight_note_text("82") is None

		# we don't want this to fail on question marks
		assert _validate_bodyweight_note_text("?") is None
		assert _validate_bodyweight_note_text("82, ?") is None
		assert _validate_bodyweight_note_text("?, 123.45") is None
		assert _validate_bodyweight_note_text("(81),") is None
		assert _validate_bodyweight_note_text("(81), 95.2, ") is None

		assert _validate_bodyweight_note_text(self.mock_note_1.text) is None
		assert _validate_bodyweight_note_text(self.mock_note_2.text) is None
		assert _validate_bodyweight_note_text(self.mock_note_3.text) is None
		assert _validate_bodyweight_note_text(self.mock_note_6.text) is None
		assert _validate_bodyweight_note_text(self.mock_note_7.text) is None

		self._assertRaise(ValueError, _validate_bodyweight_note_text, "()")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "(")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "(81, 95.2, ")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, ")")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "((81), ")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "((81)), ")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "(81)), ")

		# we don't raise for this
		# self._assertRaise(ValueError, validate_bodyweight_note_text, "81.")
		# self._assertRaise(ValueError, validate_bodyweight_note_text, "81?")
		# self._assertRaise(ValueError, validate_bodyweight_note_text, "(81)") # no trailing comma

		# non-digit character, that also isn't "." or "?"
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "81.O")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "81, p")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "a")
		self._assertRaise(ValueError, _validate_bodyweight_note_text, "81.2, 83.b, 91")

		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_4.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_5.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_14.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_15.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_16.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_17.text)
		self._assertRaise(ValueError, _validate_bodyweight_note_text, self.mock_note_18.text)


# def test_split_context_window_bodyweights_lst_returns_bodyweights_if_bodyweights_in_note(self):
# 	# given a bodyweight note, return the list of bodyweights found in that note's text as list.
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_9), ([], ["74"]))
#
# 	# notes without bodyweights in the text should return an empty list
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_1), ([], []))
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_2), ([], []))
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_3), ([], ["23423"]))
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_6), ([], []))
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_7), ([], []))
# 	self.assertEqual(split_history_from_uncommitted_bodyweights(self.mock_note_8), ([], []))


class TestFormatBodyweightHistory(MyTestCase):
	def test_format_bodyweight_history(self):
		# check that the trailing comma and space are present
		history = ["75", "86.2", "63.5"]
		self.assertEqual(format_bodyweight_history(history), "(75, 86.2, 63.5), ")
		self.assertEqual(format_bodyweight_history(["anything goes here"]), "(anything goes here), ")


class TestFindBodyweightsNote(MyTestCase):
	def setUp(self) -> None:
		# fail if there's no BODYWEIGHTS_NOTE_TITLE in title
		self.mock_note_1 = MockNoteClass(title="", text="")
		self.mock_note_2 = MockNoteClass(title="3243", text="")
		self.mock_note_3 = MockNoteClass(title="", text="23423")
		self.mock_note_4 = MockNoteClass(title="", text="abcd .")
		self.mock_note_5 = MockNoteClass(title="", text=params.BODYWEIGHTS_NOTE_TITLE)

		# pass if BODYWEIGHTS_NOTE_TITLE is in title
		self.mock_note_6 = MockNoteClass(title=params.BODYWEIGHTS_NOTE_TITLE, text="")
		self.mock_note_7 = MockNoteClass(title=params.BODYWEIGHTS_NOTE_TITLE, text=params.BODYWEIGHTS_NOTE_TITLE)
		self.mock_note_8 = MockNoteClass(title=params.BODYWEIGHTS_NOTE_TITLE, text="Something totally unrelated")

		# test that otherwise matching bodyweights are not matched, if they're flagged as trashed
		self.mock_note_9 = MockNoteClass(title=params.BODYWEIGHTS_NOTE_TITLE,
										 text=params.BODYWEIGHTS_NOTE_TITLE,
										 trashed=True)

	def _return_note_collection_1(self):
		return [self.mock_note_1, self.mock_note_2, self.mock_note_3, self.mock_note_4, self.mock_note_5]

	def _return_note_collection_2(self):
		return [self.mock_note_6, self.mock_note_7, self.mock_note_8]

	def _return_note_collection_3(self):
		return [self.mock_note_1, self.mock_note_2, self.mock_note_6]

	def test_finds_single_bodyweights_note(self):
		# find the correct note, when there's only one right answer
		bodyweights = self._return_note_collection_3()
		self.assertEqual(find_bodyweights_note(bodyweights), self.mock_note_6)

	def test_raises_on_multiple_finds(self):
		bodyweights_2 = self._return_note_collection_2()
		self._assertRaise(ValueError, find_bodyweights_note, bodyweights_2)
		self._assertRaise(ValueError, find_bodyweights_note, bodyweights_2[:-1])

	def test_raises_on_no_find(self):
		bodyweights_1 = self._return_note_collection_1()
		self._assertRaise(ValueError, find_bodyweights_note, bodyweights_1[:-1])

	def test_ignores_trashed(self):
		self._assertRaise(ValueError, find_bodyweights_note, [self.mock_note_9])


class TestPairBodyweightsWithRows(MyTestCase):
	def setUp(self) -> None:
		# used to construct the objects below. The first one is without gaps
		self.mock_matrix_1 = [[None] * 10 for lst in range(5)]  # 5 lists containing 10 times ''
		self.mock_matrix_2 = [[None] * 10 for lst in range(5)]  # 5 lists containing 10 times ''
		self.mock_matrix_3 = [[None] * 10 for lst in range(5)]  # 5 lists containing 10 times ''
		self.mock_matrix_4 = [[None] * 10 for lst in range(5)]  # 5 lists containing 10 times ''

		# insert bodyweights into mock matrices
		dates = ['a', 'b', 'c', 'd', 'e']
		for ind, date in enumerate(dates):
			# date only needs to not be none, in order for the tested function to work. -1 is to account for columns
			# starting at index 1, but lists starting at 0.
			self.mock_matrix_1[ind][params.DATE_COLUMN - 1] = date
			self.mock_matrix_2[ind][params.DATE_COLUMN - 1] = date
			self.mock_matrix_3[ind][params.DATE_COLUMN - 1] = date
			self.mock_matrix_4[ind][params.DATE_COLUMN - 1] = date

		# knock out date cell values
		self.mock_matrix_2[2][params.DATE_COLUMN - 1] = None
		self.mock_matrix_3[1][params.DATE_COLUMN - 1] = None
		self.mock_matrix_3[2][params.DATE_COLUMN - 1] = None
		self.mock_matrix_4[0][params.DATE_COLUMN - 1] = None

		self.mock_sheet_1 = MockWorkBookClass(matrix=self.mock_matrix_1).ws
		self.mock_sheet_2 = MockWorkBookClass(matrix=self.mock_matrix_2).ws
		self.mock_sheet_3 = MockWorkBookClass(matrix=self.mock_matrix_3).ws
		self.mock_sheet_4 = MockWorkBookClass(matrix=self.mock_matrix_4).ws

	def _get_k_v_combo(self, x: RowBodyweightPairings):
		return [(k, v) for k, v in x.items()]

	# todo: test duplication, empty list, negative rows, etc
	def test_pair_bodyweights_with_rows(self):
		# check that a list of bodyweights is paired correctly with a series of rows. This will be a contiguous list of rows
		# unless there's an empty date cell neighboring the examined cell in the Excel file. In that case, continue
		# searching subsequent columns until the empty cell threshold is hit. Then raise ValueError
		bodyweights_lst_1 = ["81", "72", "102.34"]
		bodyweights_lst_2 = ["1"]
		bodyweights_lst_3 = ["?"]
		bodyweights_lst_4 = ["a not real bodyweight"]
		# test under normal circumstances
		pair = partial(pair_new_bodyweights_with_rows, sheet=self.mock_sheet_1, start_row=1)
		results_1 = pair(bodyweights_lst=bodyweights_lst_1)
		results_2 = pair(bodyweights_lst=bodyweights_lst_2)
		results_3 = pair(bodyweights_lst=bodyweights_lst_3)

		# raise on invalid input
		self.assertRaises(AssertionError, pair, bodyweights_lst=bodyweights_lst_4)
		self.assertRaises(AssertionError, pair, bodyweights_lst=["73, test, ?"])
		self.assertRaises(AssertionError, pair, bodyweights_lst=["X"])

		assert isinstance(results_3, RowBodyweightPairings)
		assert all(isinstance(k, int) for k in results_3.keys()), "Non integer keys are unexpected"

		expected_1 = {r: v for r, v in zip(range(1, 4), bodyweights_lst_1)}
		self.assertEqual(results_1, expected_1)
		expected_2 = {1: bodyweights_lst_2[0]}
		self.assertEqual(results_2, expected_2)
		expected_3 = {1: bodyweights_lst_3[0]}
		self.assertEqual(results_3, expected_3)

		# test with incremented start row
		pair2 = partial(pair_new_bodyweights_with_rows, sheet=self.mock_sheet_1, start_row=2)
		results_5 = pair2(bodyweights_lst=bodyweights_lst_1)
		results_6 = pair2(bodyweights_lst=bodyweights_lst_2)

		expected_5 = {r: v for r, v in zip(range(2, 6), bodyweights_lst_1)}
		self.assertEqual(results_5, expected_5)
		expected_6 = {2: bodyweights_lst_2[0]}
		self.assertEqual(results_6, expected_6)

		# test with non-contiguous sheet. Note that you'll get an IndexError if you provide too many bodyweights
		pair_3 = partial(pair_new_bodyweights_with_rows, sheet=self.mock_sheet_2)
		results_7 = pair_3(bodyweights_lst=bodyweights_lst_1[:-1], start_row=2)
		results_8 = pair_3(bodyweights_lst=bodyweights_lst_2, start_row=1)

		# we expect expected_5 to skip the empty date cell at row 3
		expected_7 = {2: '81', 4: '72'}
		expected_8 = {1: bodyweights_lst_2[0]}
		self.assertEqual(results_7, expected_7)
		self.assertEqual(results_8, expected_8)

		# assert IndexError raised if max_empty_rows exceeded
		self._assertRaise(RuntimeError, pair_new_bodyweights_with_rows, sheet=self.mock_sheet_4,
						  bodyweights_lst=bodyweights_lst_2, start_row=1, max_empty_rows=1)


class TestReturnBodyweightHistory(MyTestCase):
	# input and expected result
	def test_return_most_recent_bodyweights(self):
		pairing_1 = ["82.2"]
		pairing_2 = ["82", "75"]
		pairing_3 = ["82", "75", "76.8"]
		pairing_4 = ["82", "75", "?", "76.8"]
		fn = return_most_recent_bodyweights

		self.assertEqual(fn(bodyweights=pairing_1, desired_count=1), [pairing_1[-1]])
		self.assertEqual(fn(bodyweights=pairing_1, desired_count=2), [pairing_1[-1]])

		self.assertEqual(fn(bodyweights=pairing_2, desired_count=1), [pairing_2[-1]])
		self.assertEqual(fn(bodyweights=pairing_2, desired_count=2), pairing_2[-2:])
		self.assertEqual(fn(bodyweights=pairing_2, desired_count=3), pairing_2[-2:])

		self.assertEqual(fn(bodyweights=pairing_3, desired_count=1), [pairing_3[-1]])
		self.assertEqual(fn(bodyweights=pairing_3, desired_count=2), pairing_3[-2:])
		self.assertEqual(fn(bodyweights=pairing_3, desired_count=3), pairing_3[-3:])
		self.assertEqual(fn(bodyweights=pairing_3, desired_count=4), pairing_3[-3:])

		self.assertEqual(fn(bodyweights=pairing_4, desired_count=1), pairing_4[-1:])
		self.assertEqual(fn(bodyweights=pairing_4, desired_count=2), pairing_4[-2:])
		self.assertEqual(fn(bodyweights=pairing_4, desired_count=3), pairing_4[-3:])
		self.assertEqual(fn(bodyweights=pairing_4, desired_count=4), pairing_4[-4:])

		# raise on non-integer history length
		self.assertRaises(AssertionError, fn, bodyweights=[], desired_count='2')
		self.assertRaises(AssertionError, fn, bodyweights=[], desired_count=2.2)


class TestExtractBodyweightsFromValidatedString(MyTestCase):
	def test_extract_bodyweights_from_validated_string(self):
		test_str_1a = "82.2"
		test_str_1b = "(82.2)"
		test_str_2a = "82.2, 75"
		test_str_2b = "(82.2), 75"
		test_str_3a = "82.2, 75, 76.8"
		test_str_3b = "(82.2, 75), 76.8"
		test_str_4a = "82.2, 75, ?, 76.8"
		test_str_4b = "(82.2, 75, ?), 76.8"

		fn = extract_bodyweights_from_validated_string
		fn_no_split = partial(fn, split_on_parenthesis=False)
		fn_with_split = partial(fn, split_on_parenthesis=True)

		# test edge cases
		self.assertEqual(fn_no_split(""), [])
		self.assertEqual(fn_no_split(","), [])
		self.assertEqual(fn_no_split("!"), ["!"])
		self.assertEqual(fn_with_split(""), ([], []))
		self.assertEqual(fn_with_split("!"), (["!"], []))
		#
		# test normal cases
		self.assertEqual(fn_no_split(test_str_1a), ["82.2"])
		self.assertEqual(fn_no_split(test_str_1b), ["82.2"])
		self.assertEqual(fn_with_split(test_str_1a), (["82.2"], []))
		self.assertEqual(fn_with_split(test_str_1b), (["82.2"], []))

		self.assertEqual(fn_no_split(test_str_2a), ["82.2", "75"], [])
		self.assertEqual(fn_no_split(test_str_2b), ["82.2", "75"])
		self.assertEqual(fn_with_split(test_str_2a), (["82.2","75"], []))
		self.assertEqual(fn_with_split(test_str_2b), (["82.2"],(["75"])))

		self.assertEqual(fn_no_split(test_str_3a), ["82.2", "75", "76.8"])
		self.assertEqual(fn_no_split(test_str_3b), ["82.2", "75", "76.8"])
		self.assertEqual(fn_with_split(test_str_3a), (["82.2", "75", "76.8"], []))
		self.assertEqual(fn_with_split(test_str_3b), (["82.2", "75"], ["76.8"]))

		self.assertEqual(fn_no_split(test_str_4a), ["82.2", "75", "?", "76.8"])
		self.assertEqual(fn_no_split(test_str_4b), ["82.2", "75", "?", "76.8"])
		self.assertEqual(fn_with_split(test_str_4a), (["82.2", "75", "?", "76.8"], []))
		self.assertEqual(fn_with_split(test_str_4b), (["82.2", "75", "?"], ["76.8"]))


# self.assertEqual(fn(bodyweights=pairing_4, desired_count=2), pairing_4[-2:])
# self.assertEqual(fn(bodyweights=pairing_4, desired_count=3), pairing_4[-3:])
# self.assertEqual(fn(bodyweights=pairing_4, desired_count=4), pairing_4[-4:])


if __name__ == '__main__':
	unittest.main()

# TODO: update the wiki, to notify the change on title, now being used to identify bodyweights notes
