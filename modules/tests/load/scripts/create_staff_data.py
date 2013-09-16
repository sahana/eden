import csv
import copy
fp = open('staff.csv', 'wb')
with fp as csvfiles:
    writer = csv.writer(csvfiles, delimiter=',')
    baseline = ['34', '1', '', 'FirstName', 'MiddleName', 'LastName', '2-Jan-1987',
                '1', 'FirstName.LastName', '1234567890', '', '', '01-Jan-2012', '31-Dec-2012']
    for i in range(10000):
        templine = copy.deepcopy(baseline)
        templine[3] = baseline[3] + str(i)
        templine[8] = baseline[8] + str(i) + "@example.com"
        writer.writerow(templine)
fp.close()
