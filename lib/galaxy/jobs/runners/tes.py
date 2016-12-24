"""
Job control via TES.
"""
import logging
import os
import json
import urllib
import shlex

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
        self.failed = False
        self.user_log = None
        self.user_log_size = 0


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

    def queue_job( self, job_wrapper ):
        """Create job script and submit it to the DRM"""

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

        task = {
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
        }

        u = urllib.urlopen('http://' + master_addr + "/v1/jobs", json.dumps(task))
        data = json.loads(u.read())
        job_id = data['value']

        cjs = TESJobState(
            job_id=job_id,
            files_dir=job_wrapper.working_directory,
            job_wrapper=job_wrapper
        )
        cjs.cleanup_file_attributes = ['output_file', 'error_file', 'exit_code_file']


        #script = self.get_job_file(
            #job_wrapper,
            #exit_code_path=cjs.exit_code_file,
            #slots_statement=galaxy_slots_statement,
        #)
        #try:
            #self.write_executable_script( executable, script )
        #except:
            #job_wrapper.fail( "failure preparing job script", exception=True )
            #log.exception( "(%s) failure preparing job script" % galaxy_id_tag )
            #return

        #cleanup_job = job_wrapper.cleanup_job
        #try:
            #open(submit_file, "w").write(submit_file_contents)
        #except Exception:
            #if cleanup_job == "always":
                #cjs.cleanup()
                # job_wrapper.fail() calls job_wrapper.cleanup()
            #job_wrapper.fail( "failure preparing submit file", exception=True )
            #log.exception( "(%s) failure preparing submit file" % galaxy_id_tag )
            #return

        # submit task
        #resp = TES.submit(task)

        log.info( "(%s) queued as %s" % ( galaxy_id_tag, job_id ) )

        # TODO is this necessary?
        job_wrapper.set_job_destination( job_destination, job_id )

        self.monitor_job(cjs)

    def check_watched_item( self, job_state ):
        """
        Called by the monitor thread to look at each watched job and deal
        with state changes.
        """
        job_id = job_state.job_id
        galaxy_id_tag = job_state.job_wrapper.get_id_tag()
        master_addr = job_state.job_wrapper.job_destination.params.get("tes_master_addr")

        r = urllib.urlopen("http://" + master_addr + "/v1/jobs/%s" % (job_id))
        data = json.loads(r.read())
        state = data['state']
        job_running = state == "Running"
        job_complete = state == "Complete"
        job_failed = "Error" in state

        #try:
            #s1, s4, s7, s5, s9, log_size = summarize_condor_log(job_state.user_log, job_id)
        #except Exception:
            # so we don't kill the monitor thread
            #log.exception( "(%s/%s) Unable to check job status" % ( galaxy_id_tag, job_id ) )
            #log.warning( "(%s/%s) job will now be errored" % ( galaxy_id_tag, job_id ) )
            #job_state.fail_message = "Cluster could not complete job"
            #self.work_queue.put( ( self.fail_job, job_state ) )
            #continue

        if job_running and not job_state.running:
            log.debug( "(%s/%s) job is now running" % ( galaxy_id_tag, job_id ) )
            job_state.job_wrapper.change_state( model.Job.states.RUNNING )

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
                    try:
                        fh.write(data['logs'][0]['stdout'])
                    except:
                        pass

                with open(job_state.error_file, 'w') as fh:
                    try:
                        fh.write(data['logs'][0]['stderr'])
                    except:
                        pass

                with open(job_state.exit_code_file, 'w') as fh:
                    try:
                        print data
                        fh.write(data['logs'][0]['exitcode'])
                    except:
                        fh.write('0\n')

                log.debug( "(%s/%s) job has completed" % ( galaxy_id_tag, job_id ) )
                self.mark_as_finished(job_state)
            return

        if job_failed:
            log.debug( "(%s/%s) job failed" % ( galaxy_id_tag, job_id ) )
            job_state.failed = True
            self.mark_as_failed(job_state)
            return job_state

        job_state.running = job_running
        return job_state

    def finish_job(self, job_state):
        super(TESJobRunner, self).finish_job(job_state)

    def stop_job( self, job ):
        """Attempts to delete a task from the task queue"""
        external_id = job.job_runner_external_id
        failure_message = condor_stop(external_id)
        if failure_message:
            log.debug("(%s/%s). Failed to stop tes %s" % (external_id, failure_message))

    def recover( self, job, job_wrapper ):
        """Recovers jobs stuck in the queued/running state when Galaxy started"""
        return
        # TODO Check if we need any changes here
        job_id = job.get_job_runner_external_id()
        galaxy_id_tag = job_wrapper.get_id_tag()
        if job_id is None:
            self.put( job_wrapper )
            return
        cjs = TESJobState( job_wrapper=job_wrapper, files_dir=self.app.config.cluster_files_directory )
        cjs.job_id = str( job_id )
        cjs.command_line = job.get_command_line()
        cjs.job_wrapper = job_wrapper
        cjs.job_destination = job_wrapper.job_destination
        cjs.user_log = os.path.join( self.app.config.cluster_files_directory, 'galaxy_%s.tes.log' % galaxy_id_tag )
        cjs.register_cleanup_file_attribute( 'user_log' )
        if job.state == model.Job.states.RUNNING:
            log.debug( "(%s/%s) is still in running state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            cjs.running = True
            self.monitor_queue.put( cjs )
        elif job.state == model.Job.states.QUEUED:
            log.debug( "(%s/%s) is still in DRM queued state, adding to the DRM queue" % ( job.id, job.job_runner_external_id ) )
            cjs.running = False
            self.monitor_queue.put( cjs )
