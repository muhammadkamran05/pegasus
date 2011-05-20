/**
 *  Copyright 2007-2008 University Of Southern California
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
package edu.isi.pegasus.planner.code.generator;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedList;

import edu.isi.pegasus.common.logging.LogManager;
import edu.isi.pegasus.planner.classes.ADag;
import edu.isi.pegasus.planner.classes.Job;
import edu.isi.pegasus.planner.classes.PegasusBag;
import edu.isi.pegasus.planner.classes.PlannerOptions;
import edu.isi.pegasus.planner.code.CodeGenerator;
import edu.isi.pegasus.planner.code.CodeGeneratorException;
import edu.isi.pegasus.planner.common.PegasusProperties;
import edu.isi.pegasus.planner.dax.Invoke;
import edu.isi.pegasus.planner.dax.Invoke.WHEN;

/**
 * A Notifications Input File Generator that generates the input file required
 * for the notifications module.
 * 
 * @author Rajiv Mayani
 * @version $Revision$
 */
public class Notifications implements CodeGenerator {

    /**
     * The suffix to use while constructing the name of the metrics file
     */
    public static final String NOTIFICATIONS_FILE_SUFFIX = ".notify";

    /**
     * The constant string to write for work flow notifications.
     */
    public static final String WORKFLOW = "WORKFLOW";

    /**
     * The constant string to write for job notifications.
     */
    public static final String JOB = "JOB";

    /**
     * The constant string to write for dag job notifications.
     */
    public static final String DAG_JOB = "DAGJOB";

    /**
     * The constant string to write for dax job notifications.
     */
    public static final String DAX_JOB = "DAXJOB";

    /**
     * The delimiter with which to separate different fields in the
     * notifications file.
     */
    public static final String DELIMITER = " ";

    /**
     * The bag of initialization objects.
     */
    protected PegasusBag mBag;

    /**
     * The directory where all the submit files are to be generated.
     */
    protected String mSubmitFileDir;

    /**
     * The object holding all the properties pertaining to Pegasus.
     */
    protected PegasusProperties mProps;

    /**
     * The object containing the command line options specified to the planner
     * at runtime.
     */
    protected PlannerOptions mPOptions;

    /**
     * The handle to the logging object.
     */
    protected LogManager mLogger;

    private PrintWriter mNotificationsWriter;

    /**
     * Initializes the Code Generator implementation.
     * 
     * @param bag
     *            the bag of initialization objects.
     * 
     * @throws CodeGeneratorException
     *             in case of any error occurring code generation.
     */
    public void initialize(PegasusBag bag) throws CodeGeneratorException {
	mNotificationsWriter = null;
	mBag = bag;
	mProps = bag.getPegasusProperties();
	mPOptions = bag.getPlannerOptions();
	mSubmitFileDir = mPOptions.getSubmitDirectory();
	mLogger = bag.getLogger();
    }

    /**
     * Generates the notifications input file. The method initially generates
     * work-flow level notification records, followed by job-level notification
     * records.
     * 
     * @param dag
     *            the concrete work-flow.
     * 
     * @return the Collection of <code>File</code> objects for the files written
     *         out.
     * 
     * @throws CodeGeneratorException
     *             in case of any error occurring code generation.
     */
    public Collection<File> generateCode(ADag dag)
	    throws CodeGeneratorException {

	File f = new File(mSubmitFileDir, Abstract.getDAGFilename(
	        this.mPOptions, dag.dagInfo.nameOfADag, dag.dagInfo.index,
	        Notifications.NOTIFICATIONS_FILE_SUFFIX));

	try {
	    mNotificationsWriter = new PrintWriter(new BufferedWriter(
		    new FileWriter(f, true)));
	} catch (IOException ioe) {
	    mLogger.log("Unable to intialize writer for notifications file ",
		    ioe, LogManager.ERROR_MESSAGE_LEVEL);
	    throw new CodeGeneratorException(
		    "Unable to intialize writer for notifications file ", ioe);

	}

	// Generate work-flow level notification record.
	generateWorkflowNotifications(dag);
	// Generate job-level notification record.
	generateJobNotifications(dag);

	mNotificationsWriter.close();

	Collection<File> result = new LinkedList<File>();
	result.add(f);
	return result;
    }

    /**
     * 
     * Not implemented
     * 
     * @param dag
     *            the work-flow
     * @param job
     *            the job for which the code is to be generated.
     * 
     * @throws edu.isi.pegasus.planner.code.CodeGeneratorException
     */
    public void generateCode(ADag dag, Job job) throws CodeGeneratorException {
	throw new UnsupportedOperationException("Not supported yet.");
    }

    /**
     * Not implemented
     */
    public boolean startMonitoring() {
	throw new UnsupportedOperationException("Not supported yet.");
    }

    /**
     * Not implemented
     */
    public void reset() throws CodeGeneratorException {
	throw new UnsupportedOperationException("Not supported yet.");
    }

    /**
     * 
     * @param dag
     */
    private void generateWorkflowNotifications(ADag dag) {
	String uuid = dag.getWorkflowUUID();
	edu.isi.pegasus.planner.classes.Notifications notfications = dag
	        .getNotifications();
	for (WHEN wTemp : WHEN.values()) {
	    for (Invoke invoke : notfications.getNotifications(wTemp)) {
		mNotificationsWriter.println(Notifications.WORKFLOW + DELIMITER
		        + uuid + DELIMITER + wTemp.toString() + DELIMITER
		        + invoke.getWhat());
	    }
	}
    }

    /**
     * Iterates over all jobs in the ADag object. Generates notifications for
     * each job.
     * 
     * @param dag
     *            the work-flow
     * @throws CodeGeneratorException
     *             when
     */
    private void generateJobNotifications(ADag dag)
	    throws CodeGeneratorException {
	for (Iterator<Job> it = dag.jobIterator(); it.hasNext();) {
	    Job job = it.next();
	    generateJobNotifications(dag, job);
	}
    }

    /**
     * Generates the notification input record for given work-flow, job.
     * 
     * @param dag
     *            the work-flow
     * @param job
     *            the job
     * @throws CodeGeneratorException
     */
    private void generateJobNotifications(ADag dag, Job job)
	    throws CodeGeneratorException {
	String sType = null;
	String sJobId = job.getID();
	switch (job.getJobType()) {
	case Job.DAG_JOB:
	    sType = Notifications.DAG_JOB;
	    break;
	case Job.DAX_JOB:
	    sType = Notifications.DAX_JOB;
	    break;
	default:
	    sType = Notifications.JOB;
	    break;
	}
	for (WHEN wTemp : WHEN.values()) {
	    for (Invoke invoke : job.getNotifications(wTemp)) {
		mNotificationsWriter.println(sType + DELIMITER + sJobId
		        + DELIMITER + wTemp.toString() + DELIMITER
		        + invoke.getWhat());
	    }
	}
    }
}