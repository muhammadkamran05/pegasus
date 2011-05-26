#!/usr/bin/env python
"""
Pegasus utility for generating workflow execution gantt chart

Usage: pegasus-gantt [options] submit directory

"""

##
#  Copyright 2010-2011 University Of Southern California
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##

# Revision : $Revision$
import os
import re
import sys
import logging
import optparse
import math
import tempfile
import shutil

# Initialize logging object
logger = logging.getLogger()
# Set default level to INFO
logger.setLevel(logging.INFO)

import common
from Pegasus.tools import utils
import plot_utils
import populate
from netlogger.analysis.workflow.sql_alchemy import *
from datetime import timedelta
from datetime import datetime


#Global variables----
prog_base = os.path.split(sys.argv[0])[1]	# Name of this program
brainbase ='braindump.txt'
base_submit_dir = None;
braindb_submit_dir =None;


#TODO's 
# print warning if kickstart time doesn't fit in the condor window
# Handle  when it is running
# handle the case when it is last retry mode 
# need to handle cluster job case
# need to handle sub dag job
	

def setup_logger(level_str):
	level_str = level_str.lower()
	if level_str == "debug":
		logger.setLevel(logging.DEBUG)
	if level_str == "warning":
		logger.setLevel(logging.WARNING)
	if level_str == "error":
		logger.setLevel(logging.ERROR)
	if level_str == "info":
		logger.setLevel(logging.INFO)
	return

def rlb(file_path):
	"""
	This function converts the path relative to base path
	Returns : path relative to the base 
	"""
	file_path = file_path.replace(braindb_submit_dir,base_submit_dir)
	return file_path
	

			

#-----date conversion----------
def convert_to_seconds(time):
	"""
	Converts the timedelta to seconds format 
	Param: time delta reference
	"""
	return (time.microseconds + (time.seconds + time.days * 24 * 3600) * pow(10,6)) / pow(10,6)

#----------print workflow details--------
def print_workflow_details(workflow_stat_list , output_dir):
	
	# print javascript file
	for workflow_stat in workflow_stat_list:
		data_file = os.path.join(output_dir,  workflow_stat.wf_uuid+"_data.js")
		try:
			fh = open(data_file, "w")
			fh.write( "\n")
			fh.write( "var data = [")
			job_info = workflow_stat.get_formatted_job_data()
			fh.write(job_info)
			fh.write( "];")
		except IOError:
			logger.error("Unable to write to file " + data_file)
			sys.exit(1)
		else:
			fh.close()	
	return
	


def create_action_script(output_dir):
# print action script
	data_file = os.path.join(output_dir,  "action.js")
	try:
		fh = open(data_file, "w")
		action_content = "\n\
function barvisibility(d , index){\n\
if(!d){\n\
 return false;\n\
}\n\
var yPos = index * bar_spacing;\n\
if(yPos < curY || yPos > curEndY ){\n\
return false;\n\
}else{\n\
return true;\n\
}\n\
}\n\n\
function openWF(url){\n\
if(isNewWindow){\n\
window.open(url);\n\
}else{\n\
self.location = url;\n\
}\n\
}\n\n\
function printJobDetails(d){\n\
var job_details = \"Job name :\"+d.name;\n\
if(d.preD !==''){\n\
job_details +=\"\\nPre script duration :\"+d.preD +\" sec.\";\n\
}\n\
if(d.gD !==''){\n\
job_details +=\"\\nResource delay :\"+d.gD +\" sec.\";\n\
}\n\
if(d.eD !==''){\n\
job_details +=\"\\nRuntime as seen by dagman :\"+d.eD +\" sec.\";\n\
}\n\
if(d.kD!==''){\n\
job_details +=\"\\nKickstart duration :\"+d.kD +\" sec.\";\n\
}\n\
if(d.postD!==''){\n\
job_details +=\"\\nPost script duration :\"+d.postD +\" sec.\";\n\
}\n\
job_details +=\"\\nMain task :\"+d.transformation ;\n\
alert(job_details);\n\
}\n\n\
function getJobBorder(d){\n\
if(!d.state){\n\
return 'red';\n\
}\n\
else if(d.sub_wf){\n\
return 'orange';\n\
}\n\
if(d.transformation){\n\
return d.color;\n\
}else{\n\
return 'gray';\n\
}\n\
}\n\n\
function getJobTime(d) {\n\
var jobWidth = 0;\n\
if(d.jobD){\n\
jobWidth = xScale(d.jobS + d.jobD) -xScale(d.jobS);\n\
}\n\
if(jobWidth > 0 && jobWidth < 1 ){\n\
	jobWidth = 1;\n\
}\n\
return jobWidth;\n\
}\n\n\
function getPreTime(d) {\n\
var preWidth = 0; \n\
if(d.preD){\n\
preWidth = xScale(d.preS + d.preD) -xScale(d.preS);\n\
}\n\
if(preWidth > 0 && preWidth < 1 ){\n\
	preWidth = 1;\n\
}\n\
return preWidth;\n\
}\n\n\
function getCondorTime(d) {\n\
var cDWidth = 0;\n\
if(d.cD){\n\
cDWidth = xScale(d.cS + d.cD) - xScale(d.cS)\n\
}\n\
if(cDWidth > 0 && cDWidth < 1 ){\n\
cDWidth = 1;\n\
}\n\
return cDWidth;\n\
}\n\n\
function getResourceDelay(d) {\n\
var gWidth = 0;\n\
if(d.gS){\n\
gWidth = xScale(d.gS + d.gD) - xScale(d.gS);\n\
}\n\
if(gWidth > 0 && gWidth < 1 ){\n\
	gWidth = 1;\n\
}\n\
return gWidth;\n\
}\n\n\
function getRunTime(d) {\n\
var rtWidth = 0;\n\
if(d.eD){\n\
rtWidth = xScale(d.eS + d.eD) -xScale(d.eS);\n\
}\n\
if(rtWidth > 0 && rtWidth < 1 ){\n\
	rtWidth = 1;\n\
}\n\
return rtWidth;\n\
}\n\n\
function getKickStartTime(d) {\n\
var kickWidth = 0;\n\
if(d.kD){\n\
kickWidth = xScale(d.kS + d.kD) -xScale(d.kS);\n\
}\n\
if(kickWidth > 0 && kickWidth < 1 ){\n\
	kickWidth = 1;\n\
}\n\
return kickWidth;\n\
}\n\n\
function getPostTime(d) {\n\
var postWidth = 0;\n\
if(d.postD){\n\
postWidth = xScale(d.postS + d.postD) -xScale(d.postS);\n\
}\n\
if(postWidth > 0 && postWidth < 1 ){\n\
	postWidth = 1;\n\
}\n\
return postWidth;\n\
}\n\n\
function showState(){\n\
if(condorTime || kickstart || condorRuntime || resourceDelay || preScript || postScript){\n\
return true;\n\
}else{\n\
return false;\n\
}\n\
}\n\n\
function setCondorTime(){\n\
if(condorTime){\n\
condorTime = false;\n\
}else{\n\
condorTime = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setKickstart(){\n\
if(kickstart){\n\
kickstart = false;\n\
}else{\n\
kickstart = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setCondorRuntime(){\n\
if(condorRuntime){\n\
condorRuntime = false;\n\
}else{\n\
condorRuntime = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setResourceDelay(){\n\
if(resourceDelay){\n\
resourceDelay = false;\n\
}else{\n\
resourceDelay = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setPreScript(){\n\
if(preScript){\n\
preScript = false;\n\
}else{\n\
preScript = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setPostScript(){\n\
if(postScript){\n\
postScript = false;\n\
}else{\n\
postScript = true;\n\
}\n\
rootPanel.render();\n\
}\n\n\
function setShowLabel(){\n\
if(showName){\n\
	return 'Hide job name';\n\
}else{\n\
	return 'Show job name';\n\
}\n\
}\n\n\
function setShowName(){\n\
if(showName){\n\
	showName = false;\n\
}else{\n\
	showName = true;\n\
}\n\
rootPanel.render();\n\
return;\n\
}\n\n\
function fadeRight(){\n\
if(curX == 0){\n\
	return \"images/right-fade.png\"\n\
}\n\
return \"images/right.png\"\n\
}\n\n\
function fadeDown(){\n\
if(curY == 0){\n\
	return \"images/down-fade.png\"\n\
}\n\
return \"images/down.png\"\n\
}\n\
\n\
function panLeft(){\n\
var panBy = (curEndX -curX)/panXFactor;\n\
curX +=panBy;\n\
curEndX +=panBy;\n\
xScale.domain(curX ,curEndX );\n\
rootPanel.render();\n\
headerPanel.render();\n\
}\n\
\n\
function panRight(){\n\
var panBy = (curEndX -curX)/panXFactor;\n\
if(curX > 0){\n\
curX -=panBy;\n\
curEndX -=panBy;\n\
if(curX <= 0){\n\
curEndX += (curX + panBy)\n\
curX = 0;\n\
}\n\
xScale.domain(curX ,curEndX );\n\
rootPanel.render();\n\
headerPanel.render();\n\
}\n\
}\n\
\n\
function panUp(){\n\
var panBy = (curEndY -curY)/panYFactor;\n\
curY +=panBy;\n\
curEndY += panBy;\n\
yScale.domain(curY ,curEndY);\n\
rootPanel.render();\n\
headerPanel.render();\n\
}\n\
\n\
function panDown(){\n\
var panBy = (curEndY -curY)/panYFactor;\n\
if(curY > 0){\n\
curY -= panBy;\n\
curEndY -= panBy;\n\
if(curY< 0){\n\
curEndY += (curY + panBy);\n\
curY = 0;\n\
}\n\
yScale.domain(curY ,curEndY );\n\
rootPanel.render();\n\
headerPanel.render();\n\
}\n\
}\n\
\n\
function zoomOut(){\n\
var newX = 0;\n\
var newY = 0;\n\
\n\
newX = curEndX  + curEndX*0.1;\n\
newY = curEndY  + curEndY*0.1;\n\
\n\
if(curX < newX && isFinite(newX)){\n\
curEndX = newX;\n\
xScale.domain(curX, curEndX);\n\
}\n\
if(curY < newY && isFinite(newY)){\n\
curEndY = newY;\n\
yScale.domain(curY, curEndY);\n\
}\n\
rootPanel.render();\n\
}\n\
\n\
function zoomIn(){\n\
var newX = 0;\n\
var newY = 0;\n\
newX = curEndX  - curEndX*0.1;\n\
newY = curEndY  - curEndY*0.1;\n\
if(curX < newX && isFinite(newX)){\n\
curEndX = newX;\n\
xScale.domain(curX, curEndX);\n\
}\n\
if(curY < newY && isFinite(newY)){\n\
curEndY = newY;\n\
yScale.domain(curY, curEndY);\n\
}\n\
rootPanel.render();\n\
}\n\
\n\
function resetZooming(){\n\
curX  = 0;\n\
curY = 0;\n\
curEndX  = initMaxX;\n\
curEndY =  initMaxY;\n\
xScale.domain(curX, curEndX);\n\
yScale.domain(curY, curEndY);\n\
rootPanel.render();\n\
}\n"
		fh.write( action_content)
		fh.write( "\n")
	except IOError:
		logger.error("Unable to write to file " + data_file)
		sys.exit(1)
	else:
		fh.close()



def create_header(workflow_stat):
	header_str = "<html>\n<head>\n<title>"+ workflow_stat.wf_uuid +"</title>\n<style type ='text/css'>\n\
#gantt_chart{\n\
border:1px solid red;\n\
}\n\
</style></head>\n<body>\n"
	return header_str
	
def create_include(workflow_stat):
	include_str = "<script type='text/javascript' src='js/protovis-r3.2.js'></script>\n\
<script type='text/javascript' src='action.js'></script>\n\
<script type='text/javascript' src='" + workflow_stat.wf_uuid  +"_data.js'></script>\n"
	return include_str
	
def create_variable(workflow_stat):
	number_of_jobs = workflow_stat.total_jobs
	# Adding  variables
	var_str = "<script type='text/javascript'>\nvar initMaxX = " + str(workflow_stat.workflow_run_time) + ";\n"
	var_str +="var bar_width = 20;\n\
var bar_spacing = 20;\n\
var inner_bar_margin = 4;\n\
var line_width =2;\n\
var inner_bar_width = bar_width-2*inner_bar_margin;\n\
var nameMargin  = 400;\n\
var scaleMargin = 15;\n"
	var_str += "var initMaxY = "+str(number_of_jobs) + "*bar_spacing;\n"
	color_name_str = "var color =['darkblue','yellow','orange' ,'steelblue', 'purple'"
	desc_name_str = "var desc=['pre script','condor job','resource delay', 'job runtime as seen by dagman','post script '"
	for k,v in workflow_stat.transformation_color_map.items():
		if workflow_stat.transformation_statistics_dict.has_key(k):
			color_name_str += ",'"+v +"'"
			desc_name_str +=",'"+k +"'"	
	color_name_str += "];\n"
	desc_name_str +="];\n"
	var_str += color_name_str
	var_str += desc_name_str
	if number_of_jobs < 5:
		var_str +="var h = " +str(number_of_jobs) +"*bar_spacing*2 + scaleMargin + bar_spacing;\n"
	else:
		var_str +="var h = 840;\n"			
	var_str +="var w = 1460;\n\
var toolbar_width = 550;\n\
var containerPanelPadding = 20;\n\
var chartPanelWidth = w+ containerPanelPadding*2;\n\
var chartPanelHeight  = h + containerPanelPadding*2;\n\
var curX  = 0;\n\
var curY = 0;\n\
var curEndX  = initMaxX;\n\
var curEndY =  initMaxY;\n\
var xScale = pv.Scale.linear(curX, curEndX).range(0, w-nameMargin);\n\
var yScale = pv.Scale.linear(curY, curEndY).range(0, h -scaleMargin);\n\
var xLabelPos = containerPanelPadding + nameMargin;\n\
var yLabelPos = 40;\n\
var panXFactor = 10;\n\
var panYFactor  = 10;\n\
var isNewWindow = false;\n\
var condorTime = false;\n\
var kickstart = false;\n\
var condorRuntime = false;\n\
var resourceDelay = false;\n\
var preScript = false;\n\
var postScript = false;\n\
var showName = false;\n\
var headerPanelWidth = w+ containerPanelPadding*2;\n\
var headerPanelHeight  = 100;\n\
var footerPanelWidth = w+ containerPanelPadding*2;\n\
var footerPanelHeight  = "+ str(50 + len(workflow_stat.transformation_statistics_dict)/4*10) + ";\n\
</script>\n"
	return var_str
	

def create_toolbar_panel(workflow_stat):
	panel_str = "<script type=\"text/javascript+protovis\">\n\
var headerPanel = new pv.Panel()\n\
.width(headerPanelWidth)\n\
.height(headerPanelHeight)\n\
.fillStyle('white');\n\n\
var panPanel  = headerPanel.add(pv.Panel)\n\
.left(w + containerPanelPadding -toolbar_width)\n\
.width(toolbar_width)\n\
.height(headerPanelHeight);\n\n\
panPanel.add(pv.Image)\n\
.left(10)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.title('Pan left')\n\
.url('images/left.png').event('click', panLeft);\n\n\
panPanel.add(pv.Image)\n\
.left(50)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url(fadeRight)\n\
.title('Pan right')\n\
.event('click', panRight);\n\n\
panPanel.add(pv.Image)\n\
.left(90)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url('images/up.png')\n\
.title('Pan up')\n\
.event('click', panUp);\n\
 panPanel.add(pv.Image)\n\
.left(140)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url(fadeDown)\n\
.title('Pan down')\n\
.event('click', panDown);\n\n\
panPanel.add(pv.Image)\n\
.left(190)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url('images/zoom-in.png')\n\
.title('Zoom in')\n\
.event('click', zoomIn);\n\n\
panPanel.add(pv.Image)\n\
.left(240)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url('images/zoom-out.png')\n\
.title('Zoom out')\n\
.event('click', zoomOut);\n\n\
panPanel.add(pv.Image)\n\
.left(290)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url('images/zoom-reset.png')\n\
.title('Zoom reset')\n\
.event('click', resetZooming);\n\n\
panPanel.add(pv.Image)\n\
.left(340)\n\
.top(34)\n\
.width(32)\n\
.height(32)\n\
.url(function() {if(isNewWindow){ return 'images/new-window-press.png';}else{ return 'images/new-window.png';}})\n\
.title('Open sub workflow in new window')\n\
.event('click', function(){ if(isNewWindow){ isNewWindow = false;headerPanel.render();}else{ isNewWindow = true;headerPanel.render();}});\n\n\
panPanel.def('active', false);\n\n\
panPanel.add(pv.Bar)\n\
.events('all')\n\
.left(390)\n\
.top(40)\n\
.width(100)\n\
.height(24)\n\
.event('click', setShowName)\n\
.fillStyle(function() this.parent.active() ? 'orange' : '#c5b0d5')\n\
.strokeStyle('black')\n\
.event('mouseover', function() this.parent.active(true))\n\
.event('mouseout', function() this.parent.active(false))\n\
.anchor('left').add(pv.Label)\n\
	.textAlign('left')\n\
	.textMargin(5)\n\
	.textStyle(function() this.parent.active() ? 'white' : 'black')\n\
	.textBaseline('middle')\n\
	.text(setShowLabel);\n\n"
	if workflow_stat.parent_wf_uuid is not None:
		panel_str += "panPanel.add(pv.Image)\n.left(500)\n.top(34)\n.width(32)\n.height(32)\n.url('images/return.png')\n.title('Return to parent workflow')\n.event('click', function(){\nself.location = '" +  workflow_stat.parent_wf_uuid+".html' ;\n});"
	panel_str += "headerPanel.add(pv.Label)\n\
.top(40)\n\
.left( containerPanelPadding + nameMargin)\n\
.font(function() {return 24 +'px sans-serif';})\n\
.textAlign('left')\n\
.textBaseline('bottom')\n\
.text('Workflow execution Gantt chart');\n\n\
headerPanel.add(pv.Label)\n\
.top(80)\n\
.left(containerPanelPadding + nameMargin)\n\
.font(function() {return 16 +'px sans-serif';})\n\
.textAlign('left')\n\
.textBaseline('bottom')\n\
.text('"+workflow_stat.dax_label +"');\n\
headerPanel.render();\n\n\
</script>\n"
	return panel_str

def create_chart_panel(workflow_stat):
	panel_str ="<script type=\"text/javascript+protovis\">\n\
var rootPanel = new pv.Panel()\n\
.width(chartPanelWidth)\n\
.height(chartPanelHeight)\n\
.fillStyle('white');\n\n\
var vis = rootPanel.add(pv.Panel)\n\
.bottom(containerPanelPadding)\n\
.top(containerPanelPadding)\n\
.left(containerPanelPadding)\n\
.width(w)\n\
.height(h)\n\
.fillStyle('white');\n\n\
var rulePanelH = vis.add(pv.Panel)\n\
.overflow('hidden')\n\
.bottom(scaleMargin);\n\n\
rulePanelH.add(pv.Rule)\n\
.left(nameMargin)\n\
.data(data)\n\
.strokeStyle('#F8F8F8')\n\
.width(w)\n\
.bottom( function(){\n\
return yScale(this.index * bar_spacing);\n\
})\n\
.anchor('left').add(pv.Label)\n\
.textBaseline('bottom')\n\
.text(function(d) {\n\
	if(showName){\n\
	return (this.index +1) +' ' + d.name;\n\
	}else{\n\
		return (this.index +1) ;\n\
	}\n\
	});\n\n\
var rulePanelV = vis.add(pv.Panel)\n\
.overflow('hidden')\n\
.left(nameMargin)\n\
.bottom(0);\n\n\
rulePanelV.add(pv.Rule)\n\
.bottom(scaleMargin)\n\
.data(function() xScale.ticks())\n\
.strokeStyle('#F8F8F8')\n\
.left(xScale)\n\
.height(h )\n\
.anchor('bottom').add(pv.Label)\n\
.textAlign('left')\n\
.text(xScale.tickFormat);\n\n\
var chartPanelContainer = vis.add(pv.Panel)\n\
.left(nameMargin)\n\
.bottom(scaleMargin)\n\
.width(w-nameMargin)\n\
.strokeStyle('black')\n\
.overflow('hidden');\n\n\
var barPanel = chartPanelContainer.add(pv.Panel)\n\
.events('all')\n\
.data(data)\n\
.height(function(){return bar_width;})\n\
.bottom(function(d){\n\
return yScale(this.index * bar_spacing);});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return barvisibility(d.jobS , this.parent.index);})\n\
.width(function(d) {\n\
return getJobTime(d);})\n\
.left(function(d){\n\
if(!d.jobS){\n\
return 0;\n\
}\n\
return xScale(d.jobS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
	printJobDetails(d);}\n\
})\n\
.fillStyle(function(d) {return 'white';})\n\
.lineWidth(line_width)\n\
.strokeStyle(function(d) {return getJobBorder(d);});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return !showState() && barvisibility(d.jobS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getJobTime(d);})\n\
.left(function(d){\n\
if(!d.jobS){\n\
return 0;\n\
}\n\
return xScale(d.jobS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
	printJobDetails(d);}\n\
})\n\
.fillStyle(function(d) {return d.color;});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return preScript && showState() && barvisibility(d.preS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getPreTime(d);})\n\
.left(function(d){\n\
if(!d.preS){\n\
return 0;\n\
}\n\
return xScale(d.preS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
	printJobDetails(d);}\n\
})\n\
.fillStyle(function(d) {return color[0];});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return condorTime && showState() && barvisibility(d.cS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getCondorTime(d);})\n\
.left(function(d){\n\
if(!d.cS){\n\
return 0;\n\
}\n\
return xScale(d.cS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
 	printJobDetails(d);}\n\
 	})\n\
.fillStyle(function(d) {return color[1];});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return resourceDelay && showState() && barvisibility(d.gS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getResourceDelay(d);})\n\
.left(function(d){\n\
if(!d.gS){\n\
return 0;\n\
}\n\
return xScale(d.gS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
	openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
	printJobDetails(d);}\n\
	})\n\
.fillStyle(function(d) {return color[2];});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return condorRuntime && showState() && barvisibility(d.eS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getRunTime(d);})\n\
.left(function(d){\n\
if(!d.eS){\n\
return 0;\n\
}\n\
return xScale(d.eS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
 	printJobDetails(d);}\n\
 	})\n\
.fillStyle(function(d) {return color[3];});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return kickstart && showState() && barvisibility(d.kS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getKickStartTime(d);})\n\
.left(function(d){\n\
if(!d.kS){\n\
return 0;\n\
}\n\
return xScale(d.kS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
 	printJobDetails(d);}\n\
 	})\n\
.fillStyle(function(d) {return d.color;});\n\n\
barPanel.add(pv.Bar)\n\
.visible(function(d){return postScript && showState() && barvisibility(d.postS , this.parent.index);})\n\
.height(function(){return inner_bar_width;})\n\
.bottom(inner_bar_margin)\n\
.width(function(d) {\n\
return getPostTime(d);})\n\
.left(function(d){\n\
if(!d.postS){\n\
return 0;\n\
}\n\
return xScale(d.postS);} )\n\
.title(function(d)d.name)\n\
.event('click', function(d){\n\
	if(d.sub_wf){\n\
		openWF(d.sub_wf_name);\n\
	}\n\
	else{\n\
 	printJobDetails(d);}\n\
 	})\n\
.fillStyle(function(d) {return color[4];});\n\n\
rootPanel.add(pv.Label)\n\
.bottom(containerPanelPadding)\n\
.font(function() {return 20 +'px sans-serif';})\n\
.textAlign('left')\n\
.textBaseline('top')\n\
.text('Job count -->')\n\
.textAngle(-Math.PI / 2);\n\n\
rootPanel.add(pv.Label)\n\
.left(containerPanelPadding + nameMargin)\n\
.bottom(0)\n\
.font(function() {return 20 +'px sans-serif';})\n\
.textAlign('left')\n\
.textBaseline('bottom')\n\
.text('Timeline in seconds -->');\n\n\
rootPanel.render();\n\
</script>\n"
	return panel_str
	

def create_legend_panel(workflow_stat):
	panel_str ="<script type=\"text/javascript+protovis\">\n\
var footerPanel = new pv.Panel()\n\
.width(footerPanelWidth)\n\
.height(footerPanelHeight)\n\
.fillStyle('white');\n\
footerPanel.add(pv.Dot)\n\
.data(desc)\n\
.left( function(d){\n\
if(this.index == 0){\n\
xLabelPos = containerPanelPadding + nameMargin;\n\
yLabelPos = 30;\n\
}else{\n\
if(xLabelPos + 180 > w){\n\
	xLabelPos =  containerPanelPadding + nameMargin;\n\
	yLabelPos -=10;\n\
}\n\
else{\n\
xLabelPos += 180;\n\
}\n\
}\n\
return xLabelPos;}\n\
)\n\
.bottom(function(d){\n\
return yLabelPos;})\n\
.fillStyle(function(d) color[this.index])\n\
.strokeStyle(null)\n\
.size(30)\n\
.anchor('right').add(pv.Label)\n\
.textMargin(6)\n\
.textAlign('left')\n\
.text(function(d) d);\n\n\
footerPanel.render();\n\n\
</script>\n"
	return panel_str

def create_gnatt_plot(workflow_stat_list ,output_dir):
	create_action_script(output_dir)
	# print html file
	for workflow_stat in workflow_stat_list:
		data_file = os.path.join(output_dir,  workflow_stat.wf_uuid+".html")
		try:
			fh = open(data_file, "w")
			fh.write( "\n")
			str_list = []
			wf_header = create_header(workflow_stat)
			str_list.append(wf_header)
			wf_content = create_include(workflow_stat)
			str_list.append(wf_content)
			# Adding  variables
			wf_content =create_variable(workflow_stat)
			str_list.append(wf_content)
			# adding the tool bar panel
			wf_content = "<div id ='gantt_chart' style='width: 1500px; margin : 0 auto;' >\n"
			str_list.append(wf_content)
			wf_content =create_toolbar_panel(workflow_stat)
			str_list.append(wf_content)
			# Adding the chart panel
			wf_content =create_chart_panel(workflow_stat)
			str_list.append(wf_content)
			# Adding the legend panel
			wf_content =create_legend_panel(workflow_stat)
			str_list.append(wf_content)
			wf_content ="</div>\n<br />\n\
<div id ='tools' style='width: 1000px; margin : 0 auto;' >\n\
<input type='checkbox' name='state' value='show condor job' onclick=\"setCondorTime();\" /> show condor job [JOB_TERMINATED -SUBMIT]<br />\n\
<input type='checkbox' name='state' value='kickstart' onclick=\"setKickstart();\"/> show kickstart time <br />\n\
<input type='checkbox' name='state' value='execute'   onclick=\"setCondorRuntime();\"/> show runtime as seen by dagman [JOB_TERMINATED - EXECUTE]<br />\n\
<input type='checkbox' name='state' value='resource'  onclick=\"setResourceDelay();\"/> show resource delay  [EXECUTE -GRID_SUBMIT/GLOBUS_SUBMIT] <br/>\n\
<input type='checkbox' name='state' value='pre script'  onclick=\"setPreScript();\"/> show pre script time <br/>\n\
<input type='checkbox' name='state' value='post script'  onclick=\"setPostScript();\"/> show post script time <br/>\n\
<img src = 'images/jobstates.png'/>\n\
</div><br/>\n"
			str_list.append(wf_content)
			# printing the brain dump content
			if workflow_stat.submit_dir is None:
				logger.warning("Unable to display brain dump contents. Invalid submit directory for workflow  " + workflow_stat.wf_uuid)
			else:
				wf_content = plot_utils.print_braindump_file(os.path.join(rlb(workflow_stat.submit_dir)))
				str_list.append(wf_content)
			fh.write("".join(str_list))
			str_list.append(wf_content)
			wf_footer = "\n<div style='clear: left'>\n</div></body>\n</html>"
			fh.write(wf_footer)
		except IOError:
			logger.error("Unable to write to file " + data_file)
			sys.exit(1)
		else:
			fh.close()	
	return
def setup(output_dir):
	src_js_path = os.path.join(common.pegasus_home, "lib/javascript")
	src_img_path = os.path.join(common.pegasus_home, "share/plots/images/protovis/")
	dest_js_path = os.path.join(output_dir, "js")
	dest_img_path = os.path.join(output_dir, "images/")
	if os.path.isdir(dest_js_path):
		logger.warning("Javascript directory exists. Deleting... ")
		try:
			shutil.rmtree(dest_js_path)
		except:
			logger.error("Unable to remove javascript directory."+dest_js_path)
			sys.exit(1)
	if os.path.isdir(dest_img_path):
		logger.warning("Image directory exists. Deleting... ")
		try:
			shutil.rmtree(dest_img_path)
		except:
			logger.error("Unable to remove image directory."+dest_img_path)
			sys.exit(1) 	 	
	shutil.copytree (src_js_path, dest_js_path)
	shutil.copytree (src_img_path, dest_img_path)



def generate_chart(submit_dir,workflow_stat_list, output_dir , log_level):
	# global reference
	global base_submit_dir
	global braindb_submit_dir
	base_submit_dir = submit_dir
	if log_level == None:
		log_level = "info"
	setup_logger(log_level)
	#Getting values from braindump file
	config = utils.slurp_braindb(submit_dir)
	if not config:
		logger.warning("could not process braindump.txt ")
		sys.exit(1)
	wf_uuid = ''
	if (config.has_key('wf_uuid')):
		wf_uuid = config['wf_uuid']
	else:
		logger.error("workflow id cannot be found in the braindump.txt ")
		sys.exit(1)
	
	if (config.has_key('submit_dir')):
		braindb_submit_dir =  os.path.abspath(config['submit_dir'])
	else:
		logger.error("Submit directory cannot be found in the braindump.txt ")
		sys.exit(1)
	
	dag_file_name =''
	if (config.has_key('dag')):
		dag_file_name = config['dag']
	else:
		logger.error("Dag file name cannot be found in the braindump.txt ")
		sys.exit(1)	
	setup(output_dir)
	print_workflow_details(workflow_stat_list ,output_dir)
	create_gnatt_plot(workflow_stat_list , output_dir)


# ---------main----------------------------------------------------------------------------
def main():
	# Configure command line option parser
	prog_usage = prog_base +" [options] SUBMIT DIRECTORY" 
	parser = optparse.OptionParser(usage=prog_usage)
	parser.add_option("-o", "--output", action = "store", dest = "output_dir",
			help = "writes the output to given directory.")
	parser.add_option("-l", "--loglevel", action = "store", dest = "log_level",
			help = "Log level. Valid levels are: debug,info,warning,error, Default is info.")
	# Parse command line options
	(options, args) = parser.parse_args()
	
	print prog_base +" : initializing..."
	if len(args) < 1:
		parser.error("Please specify Submit Directory")
		sys.exit(1)
	
	if len(args) > 1:
		parser.error("Invalid argument")
		sys.exit(1) 
	
	submit_dir = os.path.abspath(args[0])
	# Copy options from the command line parser
	if options.output_dir is not None:
		output_dir = options.output_dir
		if not os.path.isdir(output_dir):
			logger.warning("Output directory doesn't exists. Creating directory... ")
			try:
				os.mkdir(output_dir)
			except:
				logger.error("Unable to create output directory."+output_dir)
				sys.exit(1) 	
	else :
		output_dir = tempfile.mkdtemp()
	wf_info_list = populate.populate_chart(submit_dir)
	generate_chart(submit_dir, wf_info_list, output_dir, options.log_level)
	sys.exit(0)


if __name__ == '__main__':
	main()