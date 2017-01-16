from qdserver import profile

userID = input('userID: ').strip()
barIDs = input('barIDs (comma separated list): ')
barIDs = [s.strip() for s in barIDs.split(',')]
profile.add_bar_owner(userID, barIDs)
print('Success!')
