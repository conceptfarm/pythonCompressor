import subprocess
import re
from datetime import datetime
from math import floor
import sys
import os
import glob
import errno

		
class pyFFMEGCompress:
	timeFormat = "%H:%M:%S.%f"
	exportPath = 'c:/ExportedMOVs'
	ffmpegLocation = 'c:/ffmpeg/bin/ffmpeg.exe'
	
	def __init__(self, dirPath, codec, alpha, frameRate, nameFrom):
		self.dirPath = dirPath
		self.codec = codec
		self.alpha = alpha
		self.frameRate = frameRate
		self.nameFrom = nameFrom
		self.error = True
		self.debugString = '---------------------------------------------------------------------------------\n'

		
	def makeSurePathExists(self, path):
		try:
			os.makedirs(path)
		except OSError as exception:
			#print('dir already here')
			if exception.errno != errno.EEXIST:
				raise
	
	
	#time as HH:MM:SS.mm as timeobject, framerate as float
	def timeToFrames(self, t, frameRate):
		return floor(t.hour*60*60*frameRate + t.minute*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)
	
	#time as string as "HH:MM:SS.mm"
	def stringToTime(self, timeString):
		return (datetime.strptime(timeString, self.timeFormat))
	
	#dirPath is (arg in sys.argv) expects a directory, frameRate is float
	def buildFFMPEGcmd(self):
		
		self.debugString = self.debugString + self.dirPath +'\n'
		result = None
			
		shotName = str(os.path.basename(self.dirPath))
		bf = str(self.dirPath)
		
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
		
		#collect all the file names with a number at the end
		fFileNames = []
		for name in glob.glob(bf+'/*[0-9].' + popularExt):
			fFileName = str(os.path.basename(name))
			fFileNames.append(fFileName)

			
		#this is how we find where numbers change in all the files, this way we know what range of frames there is
		diffMarkers = []
		for x in range(0, (len(fFileNames) - 1)) :
			diffMarkers = diffMarkers + [i for i, (left, right) in enumerate(zip(fFileNames[x],fFileNames[x+1])) if left != right]
		
		#logF.write('diffMarkers finished '+'\n')
				
		#logF.write(str(diffMarkers) +'\n')

		#make the list unique
		mylist = sorted(list(set(diffMarkers)))
		
		#This is the number of the highest changing decimal places ie. for 0000 to 0010 is 2 , for 0000 to 0100 is 3, for 0000 to 1000 is 4
		#logF.write(str( len(mylist)-1) +'\n')
		decimalChange = len(mylist)
		
		#This number is the position in file name string of the lowest number usually 0
		#logF.write(str( mylist[len(mylist)-1]+1) +'\n')
		
		#This is used to extract just the numbers from the file name string from position in file string of the highest number : (to) position in file string of the lowest number
		#logF.write(str( mylist[0]:mylist[len(mylist)-1]+1 ) +'\n')
		
		#This is the actual number as string which needs to be converted to integer to remove padding
		#logF.write(str( (fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1] ) +'\n')
		
		#CHECK HERE IF THE AMOUNT OF FFILENAMES IS EQUAL TO THE LAST MINUS FIRST IS THE SAME
		firstFrame =(int((fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1]))
		lastFrame = (int((fFileNames[len(fFileNames)-1])[mylist[0]:mylist[len(mylist)-1]+1]))
		
		self.debugString = self.debugString + 'From: ' +str(firstFrame)+' To: '+str(lastFrame) +' Total: '+str(lastFrame-firstFrame+1)+'\n'
		self.debugString = self.debugString+'Frames found: '+str(len(fFileNames))+'\n'
		self.debugString = self.debugString+'Frames extension is: '+popularExt+'\n'
		
		#implement here how to get the shot
		#if by file then get the first file in fFileName
		#remove trailing numbers
		if self.nameFrom == 'File':
			shotName = (re.split("[_.]", fFileNames[0], 0))[0]
			#print(shotName)
		
		if (lastFrame-firstFrame+1)!=len(fFileNames):
			self.debugString = self.debugString+'\nERROR: Missing frame files.\n'
			result = None
		else:							
			fMovie = "C:/ExportedMOVs/" + shotName + ".avi"
			fFile = str( (fFileNames[0])[0:mylist[0]] ) + "%0" + str(decimalChange) + "d." + popularExt
			
			pix_fmt = "gbrp"
			if self.alpha:
				pix_fmt="gbrap"
			
			result = "\""+self.ffmpegLocation+"\" "+exrOptions+'-framerate '+str(self.frameRate)+' -y -start_number '+str(firstFrame)+" -i "+"\""+self.dirPath+"/"+fFile+"\""+' -vcodec '+self.codec+' -pred left -pix_fmt '+pix_fmt+' -r '+str(self.frameRate)+' ' + "\"" + fMovie +"\""
			self.debugString = self.debugString + 'FFMPEG Params:\n'
			self.debugString = self.debugString + result + '\n'
		return result
	
	def printProcess(self, proc, *args, **kwargs):
		progress_callback = kwargs['progress_callback']
		errorFFMPEG_callback = kwargs['errorFFMPEG_callback']
		if proc != None:
			for line in proc.stdout:
				
				frameLine = re.search("^frame=.*fps=", line, re.IGNORECASE)
				durationLine = re.search("^  Duration: ", line, re.IGNORECASE)
				completeLine = re.search("video:\d+kB audio:\d+kB subtitle:\d+kB other streams:\d+kB global headers:\d+kB muxing overhead: \d+", line, re.IGNORECASE)
				errorLine = re.search('error', line, re.IGNORECASE)
				
				if (durationLine):
					dTimeString = re.findall("\d{1,2}:\d{2}:\d{2}.\d{2}", line)
					if (dTimeString):
						duration = self.stringToTime(dTimeString[0])
						durationFrames = self.timeToFrames(duration,self.frameRate)
				if (frameLine):
					frameString = re.findall("[0-9]+", line)
					if (frameString):
						try:
							progress_callback.emit( (int(frameString[0])) /durationFrames * 100)
						except:
							self.debugString = self.debugString + 'ERROR: Error in FFMPEG Compression.\n'
							errorFFMPEG_callback.emit(self.dirPath + " %p%")
							break
				if (errorLine):
					self.debugString = self.debugString + 'ERROR: Error in FFMPEG Compression.\n'
					errorFFMPEG_callback.emit(self.dirPath + " %p%")
					break
				if (completeLine):
					self.debugString = self.debugString + '\nSUCCESS: Compressed without errors.\n'
					self.error = False
		else:
			errorFFMPEG_callback.emit(self.dirPath + " %p%")


	def ffmpegCompress(self):
		try:
			self.makeSurePathExists(self.exportPath)
			fString = self.buildFFMPEGcmd()
			#fString = '"c:\\FFmpeg\\bin\\ffmpeg.exe" -framerate 24 -y -start_number 0 -i "Z:\\19-1715_OntarioPlace\\01_Frames\\FINAL\\01_FusionOutput\\s07-02\\s07-02_.0%03d.tga" -vcodec utvideo -pred left -pix_fmt gbrp -r 24 "C:\\ExportedMOVs\\s01-02.avi"'
			
			if fString != None:
				return subprocess.Popen(fString,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
			else:
				return None
		except:
			self.debugString = self.debugString + 'ERROR: Creating export directory.\n'+self.exportPath+'\n'
			return None

#Use
#pyComp = pyFFMEGCompress("H:\\VideoProjectsTemp\\FramesTest\\s01-01","utvideo",False,24)
#ffProc = pyComp.ffmpegCompress()
#pyComp.printProcess(ffProc)





