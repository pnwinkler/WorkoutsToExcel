import unittest
from GKeepToCalc.Bodyweights2Calc.main import *
import GKeepToCalc.utilities.params as params


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
		self.assertEqual(extract_bodyweights_lst_from_raw_string(""), [])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("82"), ["82"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("82.2"), ["82.2"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("82.2,"), ["82.2"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("(82.2)"), ["82.2"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("(82.2),"), ["82.2"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("(82.2), 103.4"), ["82.2", "103.4"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("(82.2, 103.4)"), ["82.2", "103.4"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string("(82.2, 103.4),"), ["82.2", "103.4"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string(self.mock_note_10.text), ["?"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string(self.mock_note_11.text), ["?", "72"])
		self.assertEqual(extract_bodyweights_lst_from_raw_string(self.mock_note_12.text), ["?", "?"])

	def test_validate_bodyweight_note_text(self):
		# this runs validation for split_context_window_bodyweights_lst(...)
		# rudimentary checks on its own. It will be further tested below
		assert validate_bodyweight_note_text("") is None
		assert validate_bodyweight_note_text("82") is None

		# we don't want this to fail on question marks
		assert validate_bodyweight_note_text("?") is None

	def test_split_context_window_bodyweights_lst_returns_empty_list_if_no_bodyweights_in_note(self):
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_1), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_2), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_6), ([], []))

	def test_split_context_window_bodyweights_lst_raises_if_and_only_if_invalid_input(self):
		# if there is not exactly one opening and closing parenthesis, a ValueError should be raised. Also, if the
		# parentheses contain nothing
		# fail cases
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_4)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_5)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_14)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_15)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_16)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_17)
		self._assertRaise(ValueError, split_context_window_bodyweights_lst, self.mock_note_18)

		# pass cases
		split_context_window_bodyweights_lst(self.mock_note_1)
		split_context_window_bodyweights_lst(self.mock_note_2)
		split_context_window_bodyweights_lst(self.mock_note_3)
		split_context_window_bodyweights_lst(self.mock_note_6)
		split_context_window_bodyweights_lst(self.mock_note_7)

	def test_split_context_window_bodyweights_lst_returns_bodyweights_if_bodyweights_in_note(self):
		# given a bodyweight note, return the list of bodyweights found in that note's text as list.
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_9), ([], ["74"]))

		# notes without bodyweights in the text should return an empty list
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_1), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_2), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_3), ([], ["23423"]))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_6), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_7), ([], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_8), ([], []))

	def test_return_context_window(self):
		# assert that bodyweight history is returned
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_20), (["72.4"], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_21), (["72.4"], []))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_23), (["72.4", "82.6"], ["72"]))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_24), (["72.4", "82.6"], ["72"]))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_25), (["72.4", "82.6", "1.142698"], []))

		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_10), ([], ["?"]))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_11), ([], ["?", "72"]))
		self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_12), ([], ["?", "?"]))


# we expect an error if there's no comma after the context window
# self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_19), [72.4])
# self.assertEqual(split_context_window_bodyweights_lst(self.mock_note_22), [72.4, 82.6])


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

	def test_pair_bodyweights_with_rows(self):
		# check that a list of bodyweights is paired correctly with a series of rows. This will be a contiguous list of rows
		# unless there's an empty date cell neighboring the examined cell in the Excel file. In that case, continue
		# searching subsequent columns until the empty cell threshold is hit. Then raise ValueError
		bodyweights_lst_1 = ["81", "72", "a bodyweight", "102.34"]
		bodyweights_lst_2 = ["x"]
		bodyweights_lst_3 = ["?"]
		# test under normal circumstances
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_1, bodyweights_lst=bodyweights_lst_1, start_row=1),
			[(1, '81'), (2, '72'), (3, 'a bodyweight'), (4, '102.34')])
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_1, bodyweights_lst=bodyweights_lst_2, start_row=1),
			[(1, bodyweights_lst_2[0])])
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_1, bodyweights_lst=bodyweights_lst_3, start_row=1),
			[(1, bodyweights_lst_3[0])])

		# test with incremented start row
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_1, bodyweights_lst=bodyweights_lst_1, start_row=2),
			[(2, '81'), (3, '72'), (4, 'a bodyweight'), (5, '102.34')])
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_1, bodyweights_lst=bodyweights_lst_2, start_row=2),
			[(2, bodyweights_lst_2[0])])

		# test with non-contiguous sheet. Note that you'll get an IndexError if you provide too many bodyweights
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_2, bodyweights_lst=bodyweights_lst_1[:-1], start_row=2),
			[(2, '81'), (4, '72'), (5, 'a bodyweight')])
		self.assertEqual(
			pair_bodyweights_with_rows(sheet=self.mock_sheet_2, bodyweights_lst=bodyweights_lst_2, start_row=1),
			[(1, bodyweights_lst_2[0])])

		# assert IndexError raised if max_empty_rows exceeded
		self._assertRaise(IndexError, pair_bodyweights_with_rows, sheet=self.mock_sheet_4,
		                  bodyweights_lst=bodyweights_lst_2, start_row=1, max_empty_rows=1)


class TestBodyweightHistory(MyTestCase):
	def setUp(self) -> None:
		self.bodyweights_lst_1 = ["82.2"]
		# self.bodyweights_lst_2 = ["82", "75"]
		# self.bodyweights_lst_3 = ["82", "75", "76.8"]
		# self.bodyweights_lst_4 = ["82", "75", "?", "76.8"]

	def test_return_bodyweight_history(self):
		# self.assertEqual(
		# 	return_bodyweight_history(context_window_weights=[], new_bodyweights=[], history_length=2),
		# 	''
		# )
		self.assertEqual(
			return_bodyweight_history(context_window_weights=self.bodyweights_lst_1, new_bodyweights=[], history_length=2),
			'(82.2), '
		)
		self.assertEqual(
			return_bodyweight_history(context_window_weights=self.bodyweights_lst_1, new_bodyweights=["82.4"], history_length=2),
			'(82.2, 82.4), '
		)
		self.assertEqual(
			return_bodyweight_history(context_window_weights=self.bodyweights_lst_1, new_bodyweights=["?"], history_length=2),
			'(82.2, ?), '
		)

		# test with bodyweight count greater than history length. Is the correct count returned?
		self.assertEqual(
			return_bodyweight_history(context_window_weights=["82.2"], new_bodyweights=["83.2", "83.4"], history_length=2),
			'(83.2, 83.4), '
		)

		self.assertEqual(
			return_bodyweight_history(context_window_weights=["71.0","71.1"], new_bodyweights=["83.4"], history_length=2),
			'(71.1, 83.4), '
		)

		# raise on non-integer history length
		self.assertRaises(AssertionError,
		                  return_bodyweight_history,
		                  context_window_weights=[],
		                  new_bodyweights=[],
		                  history_length='2')
		self.assertRaises(AssertionError,
		                  return_bodyweight_history,
		                  context_window_weights=[],
		                  new_bodyweights=[],
		                  history_length=2.2)



if __name__ == '__main__':
	unittest.main()

# TODO: update the wiki, to notify the change on title, now being used to identify bodyweights notes