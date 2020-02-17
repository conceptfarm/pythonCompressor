import subprocess
import re
from datetime import datetime
from math import floor
import sys
import os
import glob
import errno
#from PyQt5.QtCore import QObject
		
class pyFFMEGCompress:
	timeFormat = "%H:%M:%S.%f"
	exportPath = 'c:/ExportedMOVs'
	ffmpegLocation = 'c:/ffmpeg/bin/ffmpeg.exe'
	
	def __init__(self, dirPath, codec, alpha, frameRate):
		self.dirPath = dirPath
		self.codec = codec
		self.alpha = alpha
		self.frameRate = frameRate
		#self.worker = worker
		
	def make_sure_path_exists(self, path):
		try:
			os.makedirs(path)
		except OSError as exception:
			if exception.errno != errno.EEXIST:
				raise
	
	
	#time as HH:MM:SS.mm as timeobject, framerate as float
	def timeToFrames(self, t, frameRate):
		return floor(t.hour*60*60*60*frameRate + t.minute*60*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)
	
	#time as string as "HH:MM:SS.mm"
	def stringToTime(self, timeString):
		return (datetime.strptime(timeString, self.timeFormat))
	
	#dirPath is (arg in sys.argv) expects a directory, frameRate is float
	def buildFFMPEGcmd(self):
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
		firstFrame = str(int((fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1]))
		lastFrame = str(int((fFileNames[len(fFileNames)-1])[mylist[0]:mylist[len(mylist)-1]+1]))
						
		fMovie = "C:/ExportedMOVs/" + shotName + ".avi"
		fFile = str( (fFileNames[0])[0:mylist[0]] ) + "%0" + str(decimalChange) + "d." + popularExt
		
		pix_fmt = "rgb24"
		if self.alpha:
			pix_fmt="gbrp"
		
		fString = "\""+self.ffmpegLocation+"\" "+exrOptions+'-framerate '+str(self.frameRate)+' -y -start_number '+firstFrame+" -i "+"\""+self.dirPath+"/"+fFile+"\""+' -vcodec '+self.codec+' -pred left -pix_fmt '+pix_fmt+' -r '+str(self.frameRate)+' ' + "\"" + fMovie +"\""
		return fString
	
	def printProcess(self, proc, *args, **kwargs):
		progress_callback = kwargs['progress_callback']
		errorFFMPEG_callback = kwargs['errorFFMPEG_callback']
		result = 0
		for line in proc.stdout:
			frameLine = re.search("^frame=.*fps=", line)
			durationLine = re.search("^  Duration: ", line)
			if (durationLine):
				dTimeString = re.findall("\d{1,2}:\d{2}:\d{2}.\d{2}", line)
				if (dTimeString):
					duration = self.stringToTime(dTimeString[0])
					durationFrames = self.timeToFrames(duration,self.frameRate)
			if (frameLine):
				frameString = re.findall("[0-9]+", line)
				if (frameString):
					try:
						progress_callback.emit(int(frameString[0])/durationFrames * 100)
						#self.worker.signals.progress.emit(int(frameString[0])/durationFrames * 100)
						#pySignalObj.emit(int(frameString[0])/durationFrames * 100)
					except:
						errorFFMPEG_callback.emit(self.dirPath + " %p%")
						#self.worker.signals.progress.emit(100)
						#pySignalObj.emit(100)
						#traceback.print_exc()
						#exctype, value = sys.exc_info()[:2]
						#self.worker.signals.error.emit( (exctype, value, traceback.format_exc()) )
						#self.worker.signals.error.emit( ("error", "error") )
						break


	def ffmpegCompress(self):
		self.make_sure_path_exists(self.exportPath)
		durationFrames = 1
		fString = self.buildFFMPEGcmd()
		#print(fString)
		#fString = '"c:\\FFmpeg\\bin\\ffmpeg.exe" -framerate 24 -y -start_number 0 -i "Z:\\19-1715_OntarioPlace\\01_Frames\\FINAL\\01_FusionOutput\\s07-02\\s07-02_.0%03d.tga" -vcodec utvideo -pred left -pix_fmt gbrp -r 24 "C:\\ExportedMOVs\\s01-02.avi"'

		return subprocess.Popen(fString,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
		#process = subprocess.Popen(fString,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
		#self.printProcess(process)
		#process = subprocess.Popen(fString)
		'''
		for line in process.stdout:
			frameLine = re.search("^frame=.*fps=", line)
			durationLine = re.search("^  Duration: ", line)
			if (durationLine):
				dTimeString = re.findall("\d{1,2}:\d{2}:\d{2}.\d{2}", line)
				if (dTimeString):
					duration = self.stringToTime(dTimeString[0])
					durationFrames = self.timeToFrames(duration,self.frameRate)
			if (frameLine):
				frameString = re.findall("[0-9]+", line)
				if (frameString):
					#self.progressBarWidget.setValue((int(frameString[0])/durationFrames * 100))
					#make this a return? then pass to progressbar setValue method?
					print(str(int(frameString[0])/durationFrames * 100))
		'''			

#Use
#pyComp = pyFFMEGCompress("H:\\VideoProjectsTemp\\FramesTest\\s01-01","utvideo",False,24)
#ffProc = pyComp.ffmpegCompress()
#pyComp.printProcess(ffProc)





