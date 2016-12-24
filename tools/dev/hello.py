import os

print os.getcwd()
print 'Hello, worlddddd!' * 10000
fh = open('output', 'w')
fh.write("Hey")
fh.close()
