#!/usr/bin/env python
"""
 wrapper script for running application
"""

import sys, argparse, os, subprocess, shutil
def check_and_get_file_from_env_var(file_env_var):
    file_path=os.environ.get(file_env_var, None);
    if(not file_path):
        sys.stderr.write('Environment variable '+file_env_var+' not set - exiting\n');
        sys.exit(-1);
    if(not os.path.exists(file_path)):
        sys.stderr.write('Could not access file specified by environment variable '+file_env_var+' = '+file_path+' - exiting\n');
        sys.exit(-1);
    return file_path;

def __main__():

    #BamUtil requires GCC dynamic libraries to run
    gcc49_prefix_path = check_and_get_file_from_env_var('GCC49_PREFIX_PATH');
    ld_library_path = os.environ.get('LD_LIBRARY_PATH','');
    os.environ['LD_LIBRARY_PATH'] = gcc49_prefix_path+'/lib64:'+gcc49_prefix_path+'/lib:'+ld_library_path

    #Parse Command Line
    parser = argparse.ArgumentParser()

    parser.add_argument( '-p', '--pass_through', dest='pass_through_options', action='store', type=str, help='These options are passed through directly to the application without any modification.' )

    options = parser.parse_args()
    print options.pass_through_options
    cmd = options.pass_through_options


    print "Command:"
    print cmd

    try:
        subprocess.check_output(args=cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, e:
        print "!!!!!!!!!!!! BamUtil ERROR: stdout output:\n", e.output


if __name__=="__main__": __main__()



