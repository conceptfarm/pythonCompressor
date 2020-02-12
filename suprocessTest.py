import subprocess
import re
from datetime import datetime
from math import floor

import sys
import os
import glob
import errno



#time as HH:MM:SS.mm as timeobject, framerate as float
def timeToFrames(t,frameRate):
	return floor(t.hour*60*60*60*frameRate + t.minute*60*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)

#dirPath is (arg in sys.argv) expects a directory, frameRate is float
def buildFFMPEGcmd(dirPath,frameRate):
	shotName = str(os.path.basename(dirPath))
	bf = str(dirPath)
	
	# in backwards order of likelyhood, least likely at the front most at the end
	fExt = ['gif','exr','jpeg','jpg','tiff','png','tga']

	#find most popular extension
	popularExt = ""
	exrOptions = ""
	prevFileCount = 0
	for o in fExt:
		fileCount = len(glob.glob(bf +'/*[0-9].' + o))
		if fileCount > prevFileCount :
			prevFileCount = fileCount
			popularExt = o
	
	if popularExt == "exr":
		exrOptions = " -gamma 2.2 "
	#logF.write('popularExt is '+ popularExt +'\n')
	
	#collect all the file names with a number at the end
	fFileNames = []
	for name in glob.glob(bf+'/*[0-9].' + popularExt):
		#print name
		fFileName = str(os.path.basename(name))
		#logF.write('fFileName is '+ fFileName +'\n')
		#print shortName
		fFileNames.append(fFileName)

	
	
	#this is how we find where numbers change in all the files, this way we know what range of frames there is
	diffMarkers = []
	for x in range(0, (len(fFileNames) - 1)) :
		diffMarkers = diffMarkers + [i for i, (left, right) in enumerate(zip(fFileNames[x],fFileNames[x+1])) if left != right]
	
	#logF.write('diffMarkers finished '+'\n')
			
	#logF.write(str(diffMarkers) +'\n')

	#make the list unique
	mylist = sorted(list(set(diffMarkers)))
	#logF.write(str(mylist) +'\n')
	#logF.write('mylist finished '+'\n')
	
	
	#This is the number of the highest changing decimal places ie. for 0000 to 0010 is 2 , for 0000 to 0100 is 3, for 0000 to 1000 is 4
	#logF.write(str( len(mylist)-1) +'\n')
	decimalChange = len(mylist)
	
	#This number is the position in file name string of the lowest number usually 0
	#logF.write(str( mylist[len(mylist)-1]+1) +'\n')
	
	#This is used to extract just the numbers from the file name string from position in file string of the highest number : (to) position in file string of the lowest number
	#logF.write(str( mylist[0]:mylist[len(mylist)-1]+1 ) +'\n')
	
	#This is the actual number as string which needs to be converted to integer to remove padding
	#logF.write(str( (fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1] ) +'\n')
	
	
	firstFrame = str(int((fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1]))
	lastFrame = str(int((fFileNames[len(fFileNames)-1])[mylist[0]:mylist[len(mylist)-1]+1]))
	
	#logF.write('firstFrame is '+ firstFrame +'\n')
	#logF.write('lastFrame is '+ lastFrame +'\n')
				
	fMovie = "C:/ExportedMOVs/" + shotName + ".avi"
	fFile = str( (fFileNames[0])[0:mylist[0]] ) + "%0" + str(decimalChange) + "d." + popularExt
	
	fString = '"//fs-01/DeadlineRepository10/submission/FFmpeg/bin/ffmpeg.exe" '+exrOptions+'-framerate '+str(frameRate)+' -y -start_number '+firstFrame+" -i "+"\""+dirPath+"/"+fFile+"\""+' -vcodec utvideo -pred left -pix_fmt gbrp -r '+str(frameRate)+' ' + "\"" + fMovie +"\""
	return fString



fString = buildFFMPEGcmd("Z:/19-1715_OntarioPlace/01_Frames/FINAL/01_FusionOutput/s07-02", 30)
#fString = '"c:\\FFmpeg\\bin\\ffmpeg.exe" -framerate 24 -y -start_number 0 -i "Z:\\19-1715_OntarioPlace\\01_Frames\\FINAL\\01_FusionOutput\\s07-02\\s07-02_.0%03d.tga" -vcodec utvideo -pred left -pix_fmt gbrp -r 24 "C:\\ExportedMOVs\\s01-02.avi"'

timeFormat = "%H:%M:%S.%f"
durationFrames = 1

process = subprocess.Popen(fString,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
#process = subprocess.Popen(fString)

for line in process.stdout:
	frameLine = re.search("^frame=.*fps=", line)
	durationLine = re.search("^  Duration: ", line)
	if (durationLine):
		dTimeString = re.findall("\d{1,2}:\d{2}:\d{2}.\d{2}", line)
		if (dTimeString):
			duration = (datetime.strptime(dTimeString[0], timeFormat))
			durationFrames = (timeToFrames(duration,30))
	if (frameLine):
		frameString = re.findall("[0-9]+", line)
		if (frameString):
			print(str(int(frameString[0])/durationFrames * 100))