#!/usr/bin/python
import sys;
import time;

if(len(sys.argv) < 3):
    sys.stderr.write("Needs at least 2 arguments : <input_vector_file> <output_filename>\n");
    sys.exit(-1);

sum=0;
for filename in sys.argv[1:len(sys.argv)-1]:
    fptrS=open(filename, "r");
    for line in fptrS:
        line = line.rstrip();
        val = int(line);
        sum += val;
    fptrS.close();

fptrO=open(sys.argv[len(sys.argv)-1],"w");
fptrO.write("%d\n"%(sum));
fptrO.close();

time.sleep(20);


