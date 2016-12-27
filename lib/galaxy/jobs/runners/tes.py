"""
Job control via TES.
"""
import logging
import os
import json
import shlex

import requests

from galaxy import model
from galaxy.jobs.runners import (
    AsynchronousJobRunner,
    AsynchronousJobState
)
from galaxy.util import asbool

log = logging.getLogger( __name__ )

__all__ = ( 'TESJobRunner', )


class TESJobState( AsynchronousJobState ):
    def __init__( self, **kwargs ):
        """
        Encapsulates state related to a job.
        """
        super( TESJobState, self ).__init__( **kwargs )
        self.user_log = None
        self.user_log_size = 0
        self.cleanup_file_attributes = ['output_file', 'error_file', 'exit_code_file']


class TESJobRunner( AsynchronousJobRunner ):
    """
    Job runner backed by a finite pool of worker threads. FIFO scheduling
    """
    runner_name = "TESJobRunner"

    def __init__( self, app, nworkers ):
        """Initialize this job runner and start the monitor thread"""
        super( TESJobRunner, self ).__init__( app, nworkers )
        self._init_monitor_thread()
        self._init_worker_threads()

    def _send_task(self, master_addr, task):
        url = 'http://' + master_addr + '/v1/jobs'
        r = requests.post(url, json=task)
        data = r.json()
        job_id = data['value']
        return job_id

    def _get_job(self, master_addr, job_id):
        url = 'http://' + master_addr + '/v1/jobs/' + job_id
        r = requests.get(url)
        return r.json()

    def _cancel_job(self, master_addr, job_id):
        # TODO TES doesn't actually shutdown running jobs.
        url = 'http://' + master_addr + '/v1/jobs/' + job_id
        r = requests.delete(url)

    def queue_job( self, job_wrapper ):
        """Submit the job to TES."""

        # prepare the job
        include_metadata = asbool( job_wrapper.job_destination.params.get( "embed_metadata_in_job", True ) )
        if not self.prepare_job( job_wrapper, include_metadata=include_metadata):
            return

        job_destination = job_wrapper.job_destination
        galaxy_id_tag = job_wrapper.get_id_tag()
        master_addr = job_destination.params.get("tes_master_addr")
        container = job_wrapper.tool.containers[0]

        print '=' * 50
        print job_wrapper.command_line
        print

        job_id = self._send_task(master_addr, {
            "name" : job_wrapper.tool.name,
            "projectId" : "MyProject",
            "description" : job_wrapper.tool.description,
            "resources" : {},
            "docker" : [
                {
                    "imageName" : container.identifier,
                    "cmd" : shlex.split(job_wrapper.command_line),
                    "stdout" : "stdout",
                    "stderr" : "stderr",
                }
            ]
        })

        job_state = TESJobState(
            job_id=job_id,
            files_dir=job_wrapper.working_directory,
            job_wrapper=job_wrapper
        )

        log.info( "(%s) queued as %s" % ( galaxy_id_tag, job_id ) )
        job_wrapper.set_job_destination( job_destination, job_id )
        self.monitor_job(job_state)

    def _concat_job_log(self, data, key):
        s = ''
        for i, log in enumerate(data['logs']):
            s += 'Step #{}\n'.format(i)
            s += log.get(key, '')
        return s

    def _concat_exit_codes(self, data):
        # TODO TES doesn't actually return the exit code yet
        return '0'
        return ','.join([str(l['exitcode']) for l in data['logs']])

    def check_watched_item( self, job_state ):
        """
        Called by the monitor thread to look at each watched job and deal
        with state changes.
        """
        job_id = job_state.job_id
        galaxy_id_tag = job_state.job_wrapper.get_id_tag()
        master_addr = job_state.job_wrapper.job_destination.params.get("tes_master_addr")

        data = self._get_job(master_addr, job_id)
        state = data['state']
        job_running = state == "Running"
        job_complete = state == "Complete"
        job_failed = "Error" in state

        print '=' * 50
        print state, job_state.running, data

        if job_running and job_state.running:
            return job_state

        if job_running and not job_state.running:
            log.debug( "(%s/%s) job is now running" % ( galaxy_id_tag, job_id ) )
            job_state.job_wrapper.change_state( model.Job.states.RUNNING )
            job_state.running = True
            return job_state

        # TODO this is from the condor backend. What's the right thing for TES?
        if not job_running and job_state.running:
            log.debug( "(%s/%s) job has stopped running" % ( galaxy_id_tag, job_id ) )
            # Will switching from RUNNING to QUEUED confuse Galaxy?
            # job_state.job_wrapper.change_state( model.Job.states.QUEUED )

        if job_complete:
            if job_state.job_wrapper.get_state() != model.Job.states.DELETED:
                #external_metadata = not asbool( job_state.job_wrapper.job_destination.params.get( "embed_metadata_in_job", True) )
                #if external_metadata:
                    #self._handle_metadata_externally( job_state.job_wrapper, resolve_requirements=True )
                with open(job_state.output_file, 'w') as fh:
                    fh.write(self._concat_job_log(data, 'stdout'))

                with open(job_state.error_file, 'w') as fh:
                    fh.write(self._concat_job_log(data, 'stderr'))

                with open(job_state.exit_code_file, 'w') as fh:
                    fh.write(self._concat_exit_codes(data))

                log.debug( "(%s/%s) job has completed" % ( galaxy_id_tag, job_id ) )
                self.mark_as_finished(job_state)
            return

        if job_failed:
            log.debug( "(%s/%s) job failed" % ( galaxy_id_tag, job_id ) )
            self.mark_as_failed(job_state)
            return

        return job_state

    def stop_job( self, job ):
        """Attempts to delete a task from the task queue"""

        # Possibly the job was deleted before it was fully started.
        # In this case, the job_id will be None. This seems to be a bug in Galaxy.
        # It's likely that the job was in fact submitted to TES, but the job_id
        # wasn't persisted to the monitor queue?
        job_id = job.job_runner_external_id
        if job_id is None:
            return

        master_addr = job.destination_params.get("tes_master_addr")
        print '=' * 50
        print 'stop job'
        print job_id, master_addr
        print
        self._cancel_job(master_addr, job_id)
        # TODO send cancel message to TES

    def recover( self, job, job_wrapper ):
        """Recovers jobs stuck in the queued/running state when Galaxy started"""
        return
        # TODO Check if we need any changes here
        job_id = job.get_job_runner_external_id()
        galaxy_id_tag = job_wrapper.get_id_tag()
        if job_id is None:
            self.put( job_wrapper )
            return
        job_state = TESJobState( job_wrapper=job_wrapper, files_dir=self.app.config.cluster_files_directory )
        job_state.job_id = str( job_id )
        job_state.command_line = job.get_command_line()
        job_state.job_wrapper = job_wrapper
        job_state.job_destination = job_wrapper.job_destination
        job_state.user_log = os.path.join( self.app.config.cluster_files_directory, 'galaxy_%s.tes.log' % galaxy_id_tag )
        job_state.register_cleanup_file_attribute( 'user_log' )
        if job.state == model.Job.states.RUNNING:
            log.debug( "(%s/%s) is still in running state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            job_state.running = True
            self.monitor_queue.put( job_state )
        elif job.state == model.Job.states.QUEUED:
            log.debug( "(%s/%s) is still in DRM queued state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            job_state.running = False
            self.monitor_queue.put( job_state )
