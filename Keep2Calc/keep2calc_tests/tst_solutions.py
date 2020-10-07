# holds solutions to the test questions / parameters
# called by the test_keep_to_calc.py file

# note that these solutions only contain solutions for tuple[1] of return_parsed_data's output.

single_cardio1_solution = "Cardio (target heart rate 120-130): 45 mins; Front delts; Straight arm pulldowns; Side delts; Weighted lunges; Band dislocates. Est 54 mins"
single_shadowboxing1_solution = "Shadowboxing: Front delts; Straight arm pulldowns; Side delts; Band dislocates; 3x25 jabs; 3x25 hooks; 3x25 uppercuts; 2x25 foot jab; 2x25 hook kicks. Est 27 mins"

single_workout1_solution = ''.join(['Bench press 75kg: 8,8,7,6,8; ',
                                    'Db incline 24ea: 8,9,9; ',
                                    'Ohp 40kg: 8,8,7; ',
                                    'Assisted pull up -9kg: 7,5, -18kg: 7,5; ',
                                    'Chest supported row 59kg: 9, 45kg: 12,12; ',
                                    'Machine lateral raise 45kg: 15,18; ',
                                    'Close grip bench press 60kg: 12,8,8,7; ',
                                    'Bayesian curl 23kg: 10, 18kg: 12,12; ',
                                    'RC rotations; ',
                                    'Dead hang 1. ',
                                    'Est 65 mins'])

single_workout2_solution = ''.join(['Squat 90kg: 8,8,8; ',
                                    'Deadlift 90kg: 7,7; ',
                                    'Barbell momentum shrug and hold (3s top, 5s bottom) 130kg: 5,5; ',
                                    'Pendlay row 70kg: 8,8,8; ',
                                    'Calf press machine 79kg: 16,17; ',
                                    'Leg raise: 10,10, 5kg: 10; ',
                                    'Machine crunch 30kg: 10,20; ',
                                    'Bayesian curl 40lb: 10, 32lb: 7, 22lb: 12; ',
                                    'Back supported Tricep pushdown 23kg: 15,18; ',
                                    'Machine lateral raise 45kg: 17,17; ',
                                    'Dead hang 1. ',
                                    'Est ?? mins'])

single_workout3_solution = ''.join(['Squat 100kg: 7,7,7,7,7; ',
                                    'Rack pull 110kg (with hold 2:5): 5,5,5; ',
                                    'Pendlay rows 70kg: 8,8,8,8; ',
                                    'Face pulls 130lb: 15,15,15; ',
                                    'Calf press machine 79kg: 15,20; ',
                                    '(Kinda low) Hanging circular leg raise (no reset): 9,6; ',
                                    'Hanging circular leg raise with reset: 8,6; ',
                                    'Machine crunch 36kg with reset: 12, without reset 36kg: 8; ',
                                    'Bayesian curl 10.2kg: 11,12; ',
                                    'Machine lateral raise 41kg: 20,20; ',
                                    'Dead hang. ',
                                    'Est 91 mins'])

# because our program only extracts one workout at time, we only want the first workout returned
multiple_workout1_solution = single_workout1_solution

# solution to a "noisy" dataset, where there's junk in the file unrelated to workouts
# we expect the program to ignore junk, and return only workout data
noisy_data_single_workout1_solution = single_workout1_solution

multiple_workout2_solution = [''.join(['Flat leg press 107kg: 10,10,10; ',
                                       'Romanian deadlift 100kg: 6, 110kg: 5,6; ',
                                       'Wide grip power shrug 125kg: 12; ',
                                       'Hanging toes to bar: 6,6,6; ',
                                       'Calf press machine 97.5kg: 12,12; ',
                                       'Bicycle cable crunch 37kg: 15; ',
                                       'Cable crunch 42kg: 15; ',
                                       'Dumbbell lateral raise 9ea: 15,10; ',
                                       'Machine rear delt fly 52kg: 12,12; ',
                                       'Light face pulls; ',
                                       'Og curl 14ea: 12; ',
                                       'Hammer curl 14ea: 12; ',
                                       'EZ bar momentum modified skullcrusher 10ea: 14,13; ',
                                       'Neck forwards curl, 15kg on forehead: 15,15; ',
                                       'Dead hang. ',
                                       'Est 69 mins']),
                              ''.join(['Flat leg press 107kg: 10,10,10; ',
                                       'Deadlift 120kg: 6, 130kg: 6, 135kg: 6; ',
                                       'Cable machine wide grip shrugs; ',
                                       'Hanging toes to bar: 6,6,6; ',
                                       'Calf press machine 97.5kg: 12,12; ',
                                       'Bicycle cable crunch 37kg: 15; '
                                       'Cable crunch 42kg: 12; '
                                       'Machine lateral raise 64kg: 15,15; ',
                                       'Light face pull: 18; ',
                                       'Machine curl 32kg: 12,10; ',
                                       'Tricep pushdown 36kg: 15, 41kg: 15; ',
                                       'Neck forwards curl, 15kg on forehead: 15,16; ',
                                       'Dead hang. ',
                                       'Est 68 mins'])
                              ]

multiple_workout3_solution_matrix = [
    "Bench 100kg: 3, 80kg: 8,8,10; Ohp 45kg: 8,10; Db incline press 24ea: 10,10; Chest supported row (vertical handles, full scapula movement) 45kg: 15,15 43kg: 14; Diverging Lat pulldown 47kg: 12,12; Face pull 100lb: 20; RC external rotations; Cable 2 handed curl 21kg: 15,14; Cable overhead tricep extension 36kg: 15; Tricep pushdown 36kg: 20; Neck forwards curl, 15kg on forehead: 15,15; Chest stretch; Dead hang 1. Est 74 mins",
    "Flat leg press 107kg: 10,10,10; Romanian deadlift 100kg: 6, 110kg: 5,6; Wide grip power shrug 125kg: 12; Hanging toes to bar: 6,6,6; Calf press machine 97.5kg: 12,12; Bicycle cable crunch 37kg: 15; Cable crunch 42kg: 15; Dumbbell lateral raise 9ea: 15,10; Machine rear delt fly 52kg: 12,12; Light face pulls; Og curl 14ea: 12; Hammer curl 14ea: 12; EZ bar momentum modified skullcrusher 10ea: 14,13; Neck forwards curl, 15kg on forehead: 15,15; Dead hang. Est 69 mins"
]
