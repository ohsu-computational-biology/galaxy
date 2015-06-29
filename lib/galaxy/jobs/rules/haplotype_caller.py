from galaxy.jobs import JobDestination
from galaxy.app import log 
import os
import json

def haplotype_caller(app, job):
    #log.debug('HC param_dict :  { ' + str([ str(param.name)+':::'+str(param.value) for param in job.parameters ]) + ' }');
    destination = app.job_config.get_destination(None); #Get default destination
    drmaa_params = destination.get('params');
    if('nativeSpecification' not in drmaa_params):
        drmaa_params['nativeSpecification'] = '';
    grid_job = False;
    if(drmaa_params['nativeSpecification'].find('remote_jobuniverse') != -1):   #grid job
        grid_job = True;
    for param in job.parameters:
        if(param.name == 'analysis_param_type'):
            json_dict = json.loads(param.value);
            if('useScatterGather' in json_dict and json_dict['useScatterGather'] == 'True'):
                if(grid_job):
                    drmaa_params['nativeSpecification'] += '\n+remote_RequestCpus=DetectedCpus';
                else:
                    drmaa_params['nativeSpecification'] += '\nrequest_cpus=DetectedCpus';
    return JobDestination(runner="drmaa", params=drmaa_params);

