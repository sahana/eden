from stats import ttest_ind, tinv

a = [62,96,26,121,106,59,50,122,114,89,55,36]
b = [109,117,73,80,113,156,24,73,121,125,37,69]

t,prob = ttest_ind(a,b,1)

print tinv(.05,10)
