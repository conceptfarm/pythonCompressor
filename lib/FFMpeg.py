import subprocess
import re
import os
import glob
import errno

from time import perf_counter
from datetime import timedelta, datetime
from math import floor
from pathlib import Path
from typing import Union, Optional
from dataclasses import dataclass

from lib.Threading import Callbacks


@dataclass
class cmdRegex():
	frameLineRE = re.compile( "^frame=.*fps=" )
	durationLineRE = re.compile( "^  Duration: " )
	dTimeStringRE = re.compile( "\d{1,2}:\d{2}:\d{2}.\d{2}" )
	frameStringRE = re.compile( "[0-9]+" )

class FFMpegSettings():
	SWS_FLAGS = " -sws_flags spline+accurate_rnd+full_chroma_int "
	COLOUR_FILTER = ' -vf "colorspace=bt709:iall=bt601-6-625" '
	COLOUR_FILTER_COMPLEX = ' -filter_complex "[0]colorspace=bt709:iall=bt601-6-625[main];[0]alphaextract,format=gray10le[alpha];[main][alpha]alphamerge" '
	CODEC_SETTINGS = {"ProRes":	" -codec prores_ks -pix_fmt yuv444p10le -profile:v 4444xq -f mov ", 
					"ProRes+alpha":	" -codec prores_ks -pix_fmt yuva444p10le -alpha_bits 16 -profile:v 4444xq -f mov ", 
					"UTvideo":		" -codec utvideo -pred left -pix_fmt gbrp -f avi ",
					"UTvideo+alpha":" -codec utvideo -pred left -pix_fmt gbrap -f avi ",
					"H.264":		" -c:v libx264 -crf 18 -preset veryslow -vf format=yuv420p ",
					"H.265":		" -c:v libx265 -crf 18 -preset veryslow ",
					"HAP":			" -codec hap -pix_fmt rgba -format hap_q ",
					"HAP+alpha":	" -codec hap -pix_fmt rgba -format hap_alpha "}
	
	# in backwards order of likelyhood, least likely at the front most at the end
	IMG_EXT = ['gif','exr','jpeg','jpg','tiff','tif','png','tga']

	# Input extension gamma options
	GAMMA_IN_OPT = {"gif":"","exr":" -gamma 2.2 ","jpeg":"","jpg":"","tiff":"","tif":"","png":"","tga":""}

	# Codec container pairs
	EXT_CODEC = {"ProRes":".mov", "UTvideo":".avi", "H.264":".mp4", "H.265":".mp4", "HAP":".mov"}

	def __init__(self, ffmpegLocation: str, exportPath: str, framesDirPath:str, frameRate: float = 24, codec: str = "ProRes", alpha: bool = False, nameFrom: str = 'Folder' , callbacks=Callbacks()) -> None:
		self.ffmpegLocation: str = ffmpegLocation
		self.exportPath: str = exportPath
		self.framesDirPath: str = framesDirPath	
		self.frameRateIn: float = frameRate
		self.frameRateOut: float = frameRate
		self.codecName: str = codec
		self.alpha: bool = alpha
		self.nameFrom: str = nameFrom
		
		# Defaults
		self.frameStart: int = 0	
		self.frameExt: str = 'tga'	
		self.inputCMD: str = ""
		self.outputCMD: str = ""

		self.callbacks= callbacks
		
	def _getOutputExt(self) -> Optional[str]:
		"""Gets extension based on the codec name

		Returns:
			Optional[str]: file extension WITH leading period
		"""		
		try:
			return self.EXT_CODEC[self.codecName]
		except:
			return None
	
	def _getGammaOpt(self):
		try:
			return self.GAMMA_IN_OPT[self.frameExt]
		except:
			return ""
	
	def _getPopularExt(self) -> Optional[str]:
		"""Looks through the file directory and find the most\n
		frequently occuring file extension

		Returns:
			str: extension WITHOUT leading period
		"""
		popularExt: str = ""
		prevFileCount: int = 0
		
		for ext in self.IMG_EXT:
			fileCount = len(glob.glob(self.framesDirPath + '/*[0-9].' + ext))
			self.callbacks.setlog(f'INFO: Image files {ext} count {fileCount}')
			if fileCount >= prevFileCount :
				prevFileCount = fileCount
				popularExt = ext
				
		if popularExt == '':
			self.callbacks.setlog(f'ERROR: Frame files extension is not compatible')
			return None
		
		return popularExt
	
	def _getImgSequence(self) -> tuple:
		"""Parses images in the frames folder and creates an image sequence string\n
		Creates shot name from file string

		Returns:
			tuple: tuple of image sequence string and shot from name string
		"""		
		# collect all the file names with a number at the end
		frameFileNames = []
		for name in glob.glob(self.framesDirPath + '/*[0-9].' + self.frameExt):
			fFileName = os.path.basename(name)
			frameFileNames.append(fFileName)
		
		# this is how we find where numbers change in all the files, 
		# this way we know what range of frames there is
		diffMarkers = []
		for x in range(0, (len(frameFileNames) - 1)) :
			diffMarkers = diffMarkers + [i for i, (left, right) in enumerate(zip(frameFileNames[x],frameFileNames[x+1])) if left != right]
		
		#make the list unique
		decimalChangeList = sorted(list(set(diffMarkers)))
		
		# This is the number of the highest changing decimal places 
		# ie. for 0000 to 0010 is 2 
		# for 0000 to 0100 is 3
		# for 0000 to 1000 is 4
		decimalChange = len(decimalChangeList)
		
		# Character position in file name of the lowest number usually 0
		# decimalChangeList[-1] + 1
			
		# Slice off only the decimal change parts of the file name
		# Convert to int
		firstFrameNumber: int = int((frameFileNames[0])[decimalChangeList[0]:decimalChangeList[-1]+1])
		lastFrameNumber: int = int((frameFileNames[len(frameFileNames)-1])[decimalChangeList[0]:decimalChangeList[-1]+1])
		self.frameStart = firstFrameNumber

		self.callbacks.setlog(f'INFO: Frame range: {firstFrameNumber} - {lastFrameNumber} Total: {(lastFrameNumber-firstFrameNumber+1)}')
		self.callbacks.setlog(f'INFO: Total Files: {len(frameFileNames)}')

		# Check that all the frame files are there
		if len(frameFileNames) > (lastFrameNumber-firstFrameNumber+1):
			self.callbacks.setlog(f'ERROR: Too many frame files for the frame range specified, check file naming')
			return (None,None)
		elif len(frameFileNames) < (lastFrameNumber-firstFrameNumber+1):
			self.callbacks.setlog(f'ERROR: Not enough frame files for the range specified, check for missing files')
			return (None,None)

		# implement here how to get the shot
		# if by file then get the first file in fFileName
		# remove trailing numbers
		shotName = ( re.split("[_.]", frameFileNames[0][:decimalChangeList[0]]) )[0]
				
		# Convert filename of the first frame to ffmpeg image sequence format Image_0000.jpg -> Image_0%03d.jpg
		imgSeqFileName = frameFileNames[0][:decimalChangeList[0]] + "%0" + str(decimalChange) + "d." + self.frameExt
		self.callbacks.setlog(f'INFO: FFMpeg input file name variable {imgSeqFileName}')
		imgSeqFilePath = os.path.join(self.framesDirPath, imgSeqFileName)
		self.callbacks.setlog(f'INFO: FFMpeg input file path variable {imgSeqFilePath}')

		return (imgSeqFilePath, shotName )
	
	def _buildOutCMD(self) -> str:
		"""Builds ffmpeg output command

		Returns:
			str: ffmepg output command
		"""		
		if self.alpha:
			alpha = "+alpha"
			self.outputCMD = self.SWS_FLAGS + self.COLOUR_FILTER_COMPLEX + self.CODEC_SETTINGS[self.codecName+alpha] + "-r " + str(self.frameRateOut)
		else:
			self.outputCMD = self.SWS_FLAGS + self.COLOUR_FILTER + self.CODEC_SETTINGS[self.codecName] + "-r " + str(self.frameRateOut)
		
		return self.outputCMD

	def _buildInCMD(self) -> str:
		"""Builds ffmpeg input command

		Returns:
			str: ffmepg input command
		"""		
		return self._getGammaOpt() + " -framerate " + str(self.frameRateIn) + " -y -start_number " + str(self.frameStart)
		
	def buildFFMPEGcmd(self) -> Optional[str]:
		'''
		Building the FFMpeg command string
		'''
		
		self.callbacks.setlog(f'Compressing: {self.framesDirPath}')
		self.callbacks.setlog(f'-------------{"-" * len(self.framesDirPath)}')
			
		
				
		self.frameExt = self._getPopularExt()
		if not self.frameExt:
			self.callbacks.setlog(f'ERROR: Cannot find image extension from file list')
			return None
		
		outPutExt = self._getOutputExt()
		if not outPutExt:
			self.callbacks.setlog(f'ERROR: Codec specified does not have a matching output extension')
			return None

		self.callbacks.setlog(f'INFO: Compressing using files with extension {self.frameExt}')

		# Collect frame files and create image sequence string
		# Create shot from name string
		imgSeqFilePath, ShotNameFromFile = self._getImgSequence()
		if not imgSeqFilePath or not ShotNameFromFile:
			return None

		shotName = os.path.basename(self.framesDirPath)
		if self.nameFrom == 'File':
			shotName = ShotNameFromFile
			self.callbacks.setlog(f'INFO: Shot name from file: {shotName}')
		else:
			self.callbacks.setlog(f'INFO: Shot name {shotName}')
	
		# Output movie path and name
		fMovie = os.path.join(self.exportPath, (shotName + outPutExt))
		self.callbacks.setlog(f'INFO: Compressed movie file: {fMovie}')
		
		# Build input and output commands
		self.inputCMD = self._buildInCMD()
		self.outputCMD = self._buildOutCMD()
			
		# Build the full ffmpeg command
		# result = "\""+self.ffmpegLocation+"\" "+exrOptions+'-framerate '+str(self.frameRate)+' -y -start_number '+str(firstFrame)+" -i "+"\""+self.framesDirPath+"/"+fFile+"\""+' -c:v '+self.codec+' '+format_opt+' '+pix_fmt+' -r '+str(self.frameRate)+' ' + "\"" + fMovie +"\""
		result = f'"{self.ffmpegLocation}" {self.inputCMD} -i "{imgSeqFilePath}" {self.outputCMD} "{fMovie}"'
				
		return result
		
class pyFFMEGCompress:
	TIME_FORMAT = "%H:%M:%S.%f"

	def __init__(self, ffmpegLocation:str, exportPath:str, data:dict, codec: str = 'ProRes', alpha:bool = False, frameRate:float = 24.0, nameFrom: str = 'Folder', callbacks=Callbacks()):
		self.ffmpegLocation:str = ffmpegLocation
		self.exportPath:str = exportPath
		self.row: str = data['row']
		self.framesDirPath: str = data['dirPath']
		self.codec: str = codec
		self.alpha: bool = alpha
		self.frameRate = frameRate
		self.nameFrom: str = nameFrom
		self.callbacks = callbacks
		# ffmpegLocation: str, exportPath: str, framesDirPath:str, frameRate: float = 24, codec: str = "ProRes", alpha: bool = False, nameFrom: str = 'Folder' , callbacks=Callbacks()
		self.ffmpegSettings = FFMpegSettings(self.ffmpegLocation, self.exportPath, self.framesDirPath, self.frameRate, self.codec, self.alpha, self.nameFrom, self.callbacks)
		
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
	
	
	def timeToFrames(self, t: datetime, frameRate: float) -> int:
		'''
		Converts time to frames
		@t: time as HH:MM:SS.mm as timeobject
		@framerate: float
		'''
		return floor(t.hour*60*60*frameRate + t.minute*60*frameRate + t.second*frameRate + t.microsecond/1000000 * frameRate)
	
	def stringToTime(self, timeString: str) -> datetime:
		'''
		Converts time string to time object
		@timeString: str time as HH:MM:SS.mm
		'''
		return datetime.strptime(timeString, self.TIME_FORMAT)
	
	
	def ffmpegCompress(self):
		'''
		Initiate the ffmpeg process
		'''
		try:
			if self.makeSurePathExists(self.exportPath):
				fString = self.ffmpegSettings.buildFFMPEGcmd()
								
				if fString != None:
					self.callbacks.setlog(f'INFO: Created FFMpeg command\n{fString}')
					return subprocess.Popen(fString, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
				else:
					self.callbacks.setlog(f'ERROR: Creating FFMpeg command')
					return None
			else:
				self.callbacks.setlog(f'ERROR: Creating export directory {self.exportPath}')
				return None
		except:
			self.callbacks.setlog(f'ERROR: General script error')
			return None
	
	
	def startProcess(self):
		
		start = perf_counter()
		
		# create ffmpeg process
		proc = self.ffmpegCompress()

		# Pre-compile regex
		frameLineRE = re.compile( "^frame=.*fps=" )
		durationLineRE = re.compile( "^  Duration: " )
		dTimeStringRE = re.compile( "\d{1,2}:\d{2}:\d{2}.\d{2}" )
		frameStringRE = re.compile( "[0-9]+" )
		hasError = True
		
		if proc:		
			for line in proc.stdout:
				frameLine = frameLineRE.search(line)
				durationLine = durationLineRE.search(line)
				if (durationLine):
					dTimeString = dTimeStringRE.findall(line)
					if (dTimeString):
						duration = self.stringToTime(dTimeString[0])
						durationFrames = self.timeToFrames(duration, self.frameRate)
				if (frameLine):
					frameString = frameStringRE.findall(line)
					if (frameString):
						try:
							self.callbacks.callback((self.row, int(int(frameString[0])/durationFrames * 100)) )
						except:
							self.callbacks.setlog('ERROR: Error in FFMPEG Compression\n')
							break
			
			end = perf_counter()
			elapsed = timedelta(seconds=(end-start))
			self.callbacks.setlog(f'INFO: Compression took {str(elapsed).rsplit(".", 1)[0]} ')
			self.callbacks.setlog('INFO: Success - compressed without errors.\n')
			hasError = False
		else:
			self.callbacks.setlog('ERROR: Starting FFMpeg process.\n')
		
		return hasError





