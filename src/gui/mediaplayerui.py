#! /usr/bin/env python
#  This is a unique media player that allows the user to
#  download youtube videos on the fly.
#
#  Requirements:
#    Python 2.7
#    PySide
#    pygame
#    youtube-dl (unix package)
#    ffmpeg (unix package)
#
#  @authors milesw55, ntreado
import pygame
import os, sys
import subprocess
import re
from style import style
from PySide import QtGui, QtCore

##
#  Download widget to be put in seperate thread.
class DownloadWidget(QtCore.QObject):

  ##
  #  Signal of added song.
  songAdded = QtCore.Signal(str)

  ##
  #  Error occurred.
  error = QtCore.Signal(str)

  ##
  #  Main initializer funciton.
  def __init__(self):
    super(DownloadWidget, self).__init__()

  def download(self, url, mp4, name):
    if not re.match("\w+", name):
      self.error.emit("Invalid name for saving song.")
      return
    audioFile = "/downloads/{}".format(name)
    ret = subprocess.call(['youtube-dl', '-o', mp4, url])
    if (ret != 0):
      self.error.emit("Error downloading. URL may be invalid or copyrighted.")
      return
    ret = subprocess.call(['ffmpeg', '-i', mp4, ".{}".format(audioFile)])
    if (ret != 0):
      self.error.emit("Error ripping audio.")
      subprocess.call(['rm', mp4])
      return
    subprocess.call(['rm', mp4])
    self.songAdded.emit(audioFile)


##
#  Standard Font.
class StandardFont(QtGui.QFont):
  ##
  #  Main initializer function.
  def __init__(self):
    super(StandardFont, self).__init__()
    self.setFamily("SansSerif")
    self.setPointSize(10)

##
#  This class will hold the essential UI elements of the
#  song adding features. This includes adding local songs
#  and getting songs from URLs.
class URLDownloadingGroup(QtGui.QGroupBox):

  ##
  #  Signal of added song.
  songAdded = QtCore.Signal(str)

  ##
  #  Signal for download request.
  downloadRequest = QtCore.Signal(str, str, str)

  ##
  #  Main initializer function.
  def __init__(self):
    super(URLDownloadingGroup, self).__init__()
    self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)

    rightGroupLayout = QtGui.QVBoxLayout(self)

    directionLabel = QtGui.QLabel("You can add songs locally by clicking 'Add Local'." +
" Alternatively, you can enter a video URL such as one from YouTube and click 'Add URL' to save the audio from that video to your library." +
" Please note that copyrighted videos will not work. Enjoy.")
    directionLabel.setFont(StandardFont())
    directionLabel.setWordWrap(True)
    rightGroupLayout.addWidget(directionLabel)

    self.findSongGroup = QtGui.QGroupBox()
    self.findSongGroup.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
    self.findSongGroup.setObjectName("urlGroup")
    self.findSongGroup.setStyleSheet(style.GROUP_BOX)
    rightGroupLayout.addWidget(self.findSongGroup)

    groupLayout = QtGui.QVBoxLayout(self.findSongGroup)

    urlLayout = QtGui.QHBoxLayout()
    urlLabel = QtGui.QLabel("URL:")
    urlLabel.setFont(StandardFont())
    self.urlLine = QtGui.QLineEdit()
    self.urlLine.setStyleSheet("QLineEdit { background-color: #FFF; }")
    self.urlLine.setFont(StandardFont())
    urlLayout.addSpacing(27)
    urlLayout.addWidget(urlLabel)
    urlLayout.addWidget(self.urlLine)
    urlLayout.addSpacing(69)

    nameLayout = QtGui.QHBoxLayout()
    nameLabel = QtGui.QLabel("Save As:")
    nameLabel.setFont(StandardFont())
    self.nameLine = QtGui.QLineEdit()
    self.nameLine.setStyleSheet("QLineEdit { background-color: #FFF; }")
    self.nameLine.setFont(StandardFont())
    self.nameEnd = QtGui.QComboBox()
    self.nameEnd.setFont(StandardFont())
    self.nameEnd.addItem(".mp3")
    self.nameEnd.addItem(".wav")
    nameLayout.addWidget(nameLabel)
    nameLayout.addWidget(self.nameLine)
    nameLayout.addWidget(self.nameEnd)

    groupLayout.addLayout(urlLayout)
    groupLayout.addLayout(nameLayout)

    self.songButtonLayout = QtGui.QHBoxLayout()
    
    self.statusLabel = QtGui.QLabel()
    self.statusLabel.setObjectName("status")
    self.statusLabel.setFont(StandardFont())
    self.songButtonLayout.addWidget(self.statusLabel)

    self.addSongButton = QtGui.QPushButton("Add Local")
    self.addSongButton.setObjectName("addSong")
    self.addSongButton.setStyleSheet(style.button("addSong"))
    self.addSongButton.setFont(StandardFont())
    self.addSongButton.clicked.connect(self.addSong)
    self.songButtonLayout.addStretch(0)
    self.songButtonLayout.addWidget(self.addSongButton)

    self.addButton = QtGui.QPushButton("Add URL")
    self.addButton.setObjectName("addButton")
    self.addButton.setStyleSheet(style.button("addButton"))
    self.addButton.setFont(StandardFont())
    self.addButton.clicked.connect(self.onAddClicked)
    self.songButtonLayout.addWidget(self.addButton)

    rightGroupLayout.addLayout(self.songButtonLayout)

  ##
  #  This function will act as a slot to the 'add song'
  #  button being triggered.
  def addSong(self):
    fileName, fileType = QtGui.QFileDialog.getOpenFileName(self, "Add song", os.getcwd(), "Audio Files (*.mp3 *.wav)")
    with open("songlist.txt", 'a') as f:
      f.write(fileName + '\n')
    self.songAdded.emit(fileName)
    
  ##
  #  This will be triggered when the addButton is clicked.
  def onAddClicked(self):
    mp4 = "{}.mp4".format(self.nameLine.text())
    if not os.path.isdir(os.path.join(os.getcwd(), "downloads")):
      os.makedirs(os.path.join(os.getcwd(), "downloads"))
    audioName = "{}{}".format(self.nameLine.text(), self.nameEnd.currentText())
    url = self.urlLine.text()
    self.worker = DownloadWidget()
    self.worker.songAdded.connect(self.onAudioFileAdded)
    self.worker.error.connect(self.onError)
    self.thread = QtCore.QThread()
    self.worker.moveToThread(self.thread)
    self.downloadRequest.connect(self.worker.download)
    self.thread.start()
    self.addButton.setEnabled(False)
    self.statusLabel.setStyleSheet("#status { color: black; }")
    self.statusLabel.setText("Downloading...")
    self.downloadRequest.emit(url, mp4, audioName)

  ##
  #  Updates.
  def onAudioFileAdded(self, audioFile):
    fileName = os.getcwd()+ audioFile
    with open("songlist.txt", 'a') as f:
      f.write(fileName + "\n")
    self.addButton.setEnabled(True)
    self.statusLabel.setText("Download complete.")
    self.songAdded.emit(fileName)

  ##
  #  Display error.
  def onError(self, error):
    self.statusLabel.setStyleSheet("#status { color: red; }")
    self.statusLabel.setText(error)
    self.addButton.setEnabled(True)

##
#  This is the main widget that will parent
#  most of the GUI's features. 
class MusicWidget(QtGui.QWidget):
  ##
  #  Main initializer function.
  def __init__(self):
    super(MusicWidget, self).__init__()
    self.setWindowTitle("Media Player")
    self.setObjectName("musicWidget")
    self.setStyleSheet("#musicWidget { background-color: white; }")
    self.started = False
    self.prevSong = None
    pygame.mixer.init()

    mainLayout = QtGui.QHBoxLayout(self)

    self.splitter = QtGui.QSplitter()
    self.splitter.setObjectName("splitter")
    self.splitter.setStyleSheet(style.SPLITTER)

    leftWidget = QtGui.QWidget()
    leftLayout = QtGui.QVBoxLayout(leftWidget)

    self.rightWidget = QtGui.QWidget()
    self.rightLayout = QtGui.QVBoxLayout(self.rightWidget)
    self.rightGroup = URLDownloadingGroup()
    self.rightGroup.songAdded.connect(self.onSongAdded)
    self.rightLayout.addWidget(self.rightGroup)

    self.splitter.addWidget(leftWidget)
    self.splitter.addWidget(self.rightWidget)

    mainLayout.addWidget(self.splitter)

    groupbox = QtGui.QGroupBox("Your songs:")
    groupbox.setFont(StandardFont())
    gboxLayout = QtGui.QVBoxLayout()

    self.songList = QtGui.QListWidget()
    self.songList.setObjectName("listWidget")
    self.songList.setFont(StandardFont())
    self.songList.setStyleSheet(style.LIST_WIDGET)
    self.songList.itemDoubleClicked.connect(self.onItemDoubleClicked)

    content = ""
    self.names = {}
    with open("songlist.txt", 'a') as f:
      print("songlist.txt does exist\ncontinuing with initialization")
    with open("songlist.txt", 'r') as f:
      content = f.read()
    for song in content.split('\n'):
      if song != "":
        self.names[os.path.basename(song)] = song
        self.songList.addItem(os.path.basename(song))

    gboxLayout.addWidget(self.songList)
    groupbox.setLayout(gboxLayout)
    leftLayout.addWidget(groupbox)

    buttonLayout = QtGui.QHBoxLayout()
    self.playButton = QtGui.QPushButton("Play")
    self.playButton.setObjectName("playButton")
    self.playButton.setStyleSheet(style.button("playButton"))
    self.playButton.setFont(StandardFont())
    self.playButton.clicked.connect(self.playTriggered)
    buttonLayout.addWidget(self.playButton)

    pauseButton = QtGui.QPushButton("Pause")
    pauseButton.setObjectName("pauseButton")
    pauseButton.setStyleSheet(style.button("pauseButton"))
    pauseButton.setFont(StandardFont())
    pauseButton.clicked.connect(self.pauseTriggered)
    buttonLayout.addWidget(pauseButton)

    leftLayout.addLayout(buttonLayout)

  ##
  #  This is triggered when an item in the list is double clicked. A song will play.
  def onItemDoubleClicked(self, item):
    song = self.names[item.text()]
    self.prevSong = song
    pygame.mixer.music.load(song)
    self.started = True
    pygame.mixer.music.play()

  ##
  #  On song added, update the dictionary and list widget.
  def onSongAdded(self, fileName):
    self.names[os.path.basename(fileName)] = fileName
    self.songList.addItem(os.path.basename(fileName))

  ##
  #  This function will act as a slot to the 'play button'
  #  being triggered.
  def playTriggered(self):
    song = self.names[self.songList.currentItem().text()]
    if (self.prevSong is None) or (self.prevSong != song):
      self.prevSong = song
      pygame.mixer.music.load(song)
    if self.started == False:
      self.started = True
      pygame.mixer.music.play()
    elif pygame.mixer.music.get_busy():
      pygame.mixer.music.unpause()
    else:
      pygame.mixer.music.play()

  ##
  #  This function will act as a slot to the 'pause button'
  #  being triggered.
  def pauseTriggered(self):
    pygame.mixer.music.pause()

