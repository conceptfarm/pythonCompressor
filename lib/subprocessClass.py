import subprocess
import re
from datetime import datetime
from math import floor
import os
import glob
import errno
from time import perf_counter
from datetime import timedelta

from pathlib import Path
from typing import Union, Optional

from lib.Threading import Callbacks

class FFMpegSettings():

	def __init__(self, frameRate: float = 24, codec: str = "ProRes", alpha: bool = False, startFrame: int = 0, frameExt = "tga") -> None:
		self.codecName: str = codec
		self.frameRateIn: float = frameRate
		self.frameStart: int = startFrame
		self.frameRateOut: float = frameRate
		self.alpha: bool = alpha
		self.frameExt = frameExt
		self.swsFlags = " -sws_flags spline+accurate_rnd+full_chroma_int "
		self.colourFilter = ' -vf "colorspace=bt709:iall=bt601-6-625" '
		self.colourFilterComplex = ' -filter_complex "[0]colorspace=bt709:iall=bt601-6-625[main];[0]alphaextract,format=gray10le[alpha];[main][alpha]alphamerge" '
		self.inputCMD: str = ""
		self.outputCMD: str = ""
		
		self.codecSettings = {"ProRes":	" -codec prores_ks -pix_fmt yuv444p10le -profile:v 4444xq -f mov ", 
						"ProRes+alpha":	" -codec prores_ks -pix_fmt yuva444p10le -alpha_bits 16 -profile:v 4444xq -f mov ", 
						"UTvideo":		" -codec utvideo -pred left -pix_fmt gbrp -f avi ",
						"UTvideo+alpha":" -codec utvideo -pred left -pix_fmt gbrap -f avi ",
						"H.264":		" -c:v libx264 -crf 18 -preset veryslow -vf format=yuv420p ",
						"H.265":		" -c:v libx265 -crf 18 -preset veryslow ",
						"HAP":			" -codec hap -pix_fmt rgba -format hap_q ",
						"HAP+alpha":	" -codec hap -pix_fmt rgba -format hap_alpha "}
		
		self.gammaInOpt = {"gif":"","exr":" -gamma 2.2 ","jpeg":"","jpg":"","tiff":"","tif":"","png":"","tga":""}
		

	
	def getOutputExt(self):
		ext = {"ProRes":".mov", "UTvideo":".avi", "H.264":".mp4", "H.265":".mp4", "HAP":".mov"}
		return ext[self.codecName]
	
	def getGammaOpt(self):
		try:
			return self.gammaInOpt[self.frameExt]
		except:
			return ""
	
	def buildOutCMD(self):
		if self.alpha:
			alpha = "+alpha"
			self.outputCMD = self.swsFlags + self.colourFilterComplex + self.codecSettings[self.codecName+alpha] + "-r " + str(self.frameRateOut)
		else:
			self.outputCMD = self.swsFlags + self.colourFilter + self.codecSettings[self.codecName] + "-r " + str(self.frameRateOut)
		
		return self.outputCMD

	def buildInCMD(self):
		self.inputCMD = self.getGammaOpt() + " -framerate " + str(self.frameRateIn) + " -y -start_number " + str(self.frameStart)
		return self.inputCMD
		
class pyFFMEGCompress:
	timeFormat = "%H:%M:%S.%f"
	# in backwards order of likelyhood, least likely at the front most at the end
	imgExtensions = ['gif','exr','jpeg','jpg','tiff','tif','png','tga']

	def __init__(self, ffmpegLocation:str, exportPath:str, data:dict, codec:str = 'ProRes', alpha:bool = False, frameRate:float = 24.0, nameFrom:str = 'Folder'):
		self.ffmpegLocation:str = ffmpegLocation
		self.exportPath:str = exportPath
		self.row: str = data['row']
		self.framesDirPath: str = data['dirPath']
		self.codec: str = codec
		self.alpha: bool = alpha
		self.frameRate = frameRate
		self.nameFrom: str = nameFrom
		self.hasError: bool = True
		self.ffmpegSettings = FFMpegSettings(self.frameRate, self.codec, self.alpha, 0, "tga")
		
	def makeSurePathExists(self, path:Union[str,Path]) -> Optional[Path]:
		'''
		Creates a dir and returns the path, if error then None
		'''
		try:
			if not isinstance(path, Path):
				path = Path(path)
			path.mkdir(parents=True)
			return path
		except OSError as exception:
			#print('dir already here')
			if exception.errno != errno.EEXIST:
				return None
			elif exception.errno == errno.EEXIST:
				return path
		return None
	
	
	def timeToFrames(self, t, frameRate) -> int:
		'''
		Converts time to frames
		@t: time as HH:MM:SS.mm as timeobject
		@framerate: float
		'''
		return floor(t.hour*60*60*frameRate + t.minute*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)
	
	def stringToTime(self, timeString) -> datetime:
		'''
		Converts time string to time object
		@timeString: str time as HH:MM:SS.mm
		'''
		return datetime.strptime(timeString, self.timeFormat)
	
	#dirPath is (arg in sys.argv) expects a directory, frameRate is float
	def buildFFMPEGcmd(self, callbacks=Callbacks()):
		'''
		Building the FFMpeg command string
		'''
		
		callbacks.setlog(f'Compressing: {self.framesDirPath}')
		callbacks.setlog(f'-------------{"-" * len(self.framesDirPath)}')
			
		shotName = os.path.basename(self.framesDirPath)
		callbacks.setlog(f'INFO: Shot name {shotName}')
		


		#find most popular extension
		popularExt: str = ""
		prevFileCount = 0
		
		for o in self.imgExtensions:
			fileCount = len(glob.glob(self.framesDirPath + '/*[0-9].' + o))
			callbacks.setlog(f'INFO: Image files {o} count {fileCount}')
			if fileCount >= prevFileCount :
				prevFileCount = fileCount
				popularExt = o
		
		# if popularExt == "exr":
		# 	exrOptions = " -gamma 2.2 "
		
		if popularExt == '':
			callbacks.setlog(f'ERROR: Frame files extension is not compatible')
			return None
		
		self.ffmpegSettings.frameExt = popularExt

		callbacks.setlog(f'INFO: Compressing using files with extension {popularExt}')

		#collect all the file names with a number at the end
		fFileNames = []
		for name in glob.glob(self.framesDirPath + '/*[0-9].' + popularExt):
			fFileName = os.path.basename(name)
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
		firstFrame = int((fFileNames[0])[mylist[0]:mylist[len(mylist)-1]+1])
		lastFrame = int((fFileNames[len(fFileNames)-1])[mylist[0]:mylist[len(mylist)-1]+1])
		
		callbacks.setlog(f'INFO: Frame range: {firstFrame} - {lastFrame} Total: {(lastFrame-firstFrame+1)}')
		callbacks.setlog(f'INFO: Total Files: {len(fFileNames)}')

		if len(fFileNames) > (lastFrame-firstFrame+1):
			callbacks.setlog(f'ERROR: Too many frame files for the frame range specified, check file naming')
			return None
		elif len(fFileNames) < (lastFrame-firstFrame+1):
			callbacks.setlog(f'ERROR: Not enough frame files for the range specified, check for missing files')
			return None

		
		# implement here how to get the shot
		# if by file then get the first file in fFileName
		# remove trailing numbers
		if self.nameFrom == 'File':
			shotName = (re.split("[_.]", fFileNames[0], 0))[0]
			callbacks.setlog(f'INFO: Shot name from file: {shotName}')
		
		fFile = str( (fFileNames[0])[0:mylist[0]] ) + "%0" + str(decimalChange) + "d." + popularExt
		callbacks.setlog(f'INFO: FFMpeg input file name variable {fFile}')
	
		self.ffmpegSettings.frameStart = firstFrame
	
		fMovie = os.path.join(self.exportPath, (shotName + self.ffmpegSettings.getOutputExt()))
		callbacks.setlog(f'INFO: Compressed movie file: {fMovie}')
		# result = "\""+self.ffmpegLocation+"\" "+exrOptions+'-framerate '+str(self.frameRate)+' -y -start_number '+str(firstFrame)+" -i "+"\""+self.framesDirPath+"/"+fFile+"\""+' -c:v '+self.codec+' '+format_opt+' '+pix_fmt+' -r '+str(self.frameRate)+' ' + "\"" + fMovie +"\""
		result = f'"{self.ffmpegLocation}" {self.ffmpegSettings.buildInCMD()} -i "{os.path.join(self.framesDirPath, fFile)}" {self.ffmpegSettings.buildOutCMD()} "{fMovie}"'
				
		return result
	
	def ffmpegCompress(self, callbacks=Callbacks()):
		'''
		Initiate the ffmpeg process
		'''
		try:
			if self.makeSurePathExists(self.exportPath):
				fString = self.buildFFMPEGcmd(callbacks)
				#fString = '"c:\\FFmpeg\\bin\\ffmpeg.exe" -framerate 24 -y -start_number 0 -i "Z:\\19-1715_OntarioPlace\\01_Frames\\FINAL\\01_FusionOutput\\s07-02\\s07-02_.0%03d.tga" -vcodec utvideo -pred left -pix_fmt gbrp -r 24 "C:\\ExportedMOVs\\s01-02.avi"'
				
				if fString != None:
					callbacks.setlog(f'INFO: Created FFMpeg cmd string\n{fString}')
					return subprocess.Popen(fString,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
				else:
					callbacks.setlog(f'ERROR: Creating FFMpeg cmd string')
					return None
			else:
				callbacks.setlog(f'ERROR: Creating export directory {self.exportPath}')
				return None
		except:
			callbacks.setlog(f'ERROR: General script error')
			return None
	
	
	def printProcess(self, callbacks=Callbacks()):
		
		start = perf_counter()
		# create ffmpeg process
		proc = self.ffmpegCompress(callbacks)

		# Pre-compile regex
		frameLineRE = re.compile( "^frame=.*fps=" )
		durationLineRE = re.compile( "^  Duration: " )
		dTimeStringRE = re.compile( "\d{1,2}:\d{2}:\d{2}.\d{2}" )
		frameStringRE = re.compile( "[0-9]+" )

		if proc:
			for line in proc.stdout:
				frameLine = frameLineRE.search(line)
				durationLine = durationLineRE.search(line)
				if (durationLine):
					dTimeString = dTimeStringRE.findall(line)
					if (dTimeString):
						duration = self.stringToTime(dTimeString[0])
						durationFrames = self.timeToFrames(duration,self.frameRate)
				if (frameLine):
					frameString = frameStringRE.findall(line)
					if (frameString):
						try:
							callbacks.callback((self.row, int(int(frameString[0])/durationFrames * 100)) )
						except:
							callbacks.setlog('ERROR: Error in FFMPEG Compression\n')
							break
			
			end = perf_counter()
			elapsed = timedelta(seconds=(end-start))
			callbacks.setlog(f'INFO: Compression took {str(elapsed).rsplit(".", 1)[0]} ')
			callbacks.setlog('INFO: Success - compressed without errors.\n')
			self.hasError = False
		else:
			callbacks.setlog('ERROR: Starting FFMpeg process.\n')
		
		return self.hasError




#Use
#pyComp = pyFFMEGCompress("H:\\VideoProjectsTemp\\FramesTest\\s01-01","utvideo",False,24)
#ffProc = pyComp.ffmpegCompress()
#pyComp.printProcess(ffProc)





