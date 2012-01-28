#!/usr/bin/env python

from Pegasus.DAX3 import *
import sys
import os
import ConfigParser

if len(sys.argv) != 3:
	print "Usage: %s PEGASUS_HOME" % (sys.argv[0])
	sys.exit(1)

# Create a abstract dag
diamond = ADAG("diamond")

config = ConfigParser.ConfigParser()
config.read(sys.argv [2] + '/test.config')

# Add input file to the DAX-level replica catalog
a = File("f.a")
a.addPFN(PFN(config.get('all', 'file_url') + os.getcwd() + "/f.a", config.get('all', 'file_site')))
diamond.addFile(a)
	
# Add executables to the DAX-level replica catalog
# In this case the binary is pegasus-keg, which is shipped with Pegasus, so we use
# the remote PEGASUS_HOME to build the path.
e_preprocess = Executable(namespace="diamond", name="preprocess", version="4.0", os="linux", arch="x86", installed=False)
e_preprocess.addPFN(PFN(config.get('all', 'executable_url') + sys.argv[1] + "/bin/pegasus-keg", config.get('all', 'executable_site')))
diamond.addExecutable(e_preprocess)
	
e_findrange = Executable(namespace="diamond", name="findrange", version="4.0", os="linux", arch="x86", installed=False)
e_findrange.addPFN(PFN(config.get('all', 'executable_url') + sys.argv[1] + "/bin/pegasus-keg", config.get('all', 'executable_site')))
diamond.addExecutable(e_findrange)
	
e_analyze = Executable(namespace="diamond", name="analyze", version="4.0", os="linux", arch="x86", installed=False)
e_analyze.addPFN(PFN(config.get('all', 'executable_url') + sys.argv[1] + "/bin/pegasus-keg", config.get('all', 'executable_site')))
diamond.addExecutable(e_analyze)

# Add a preprocess job
preprocess = Job(namespace="diamond", name="preprocess", version="4.0")
b1 = File("f.b1")
b2 = File("f.b2")
preprocess.addArguments("-a preprocess","-T5","-i",a,"-o",b1,b2)
preprocess.uses(a, link=Link.INPUT)
preprocess.uses(b1, link=Link.OUTPUT)
preprocess.uses(b2, link=Link.OUTPUT)
diamond.addJob(preprocess)

# Add left Findrange job
frl = Job(namespace="diamond", name="findrange", version="4.0")
c1 = File("f.c1")
frl.addArguments("-a findrange","-T5","-i",b1,"-o",c1)
frl.uses(b1, link=Link.INPUT)
frl.uses(c1, link=Link.OUTPUT)
diamond.addJob(frl)

# Add right Findrange job
frr = Job(namespace="diamond", name="findrange", version="4.0")
c2 = File("f.c2")
frr.addArguments("-a findrange","-T5","-i",b2,"-o",c2)
frr.uses(b2, link=Link.INPUT)
frr.uses(c2, link=Link.OUTPUT)
diamond.addJob(frr)

# Add Analyze job
analyze = Job(namespace="diamond", name="analyze", version="4.0")
d = File("f.d")
analyze.addArguments("-a analyze","-T5","-i",c1,c2,"-o",d)
analyze.uses(c1, link=Link.INPUT)
analyze.uses(c2, link=Link.INPUT)
analyze.uses(d, link=Link.OUTPUT, register=True)
diamond.addJob(analyze)

# Add control-flow dependencies
diamond.addDependency(Dependency(parent=preprocess, child=frl))
diamond.addDependency(Dependency(parent=preprocess, child=frr))
diamond.addDependency(Dependency(parent=frl, child=analyze))
diamond.addDependency(Dependency(parent=frr, child=analyze))

# Write the DAX to stdout
diamond.writeXML(sys.stdout)
