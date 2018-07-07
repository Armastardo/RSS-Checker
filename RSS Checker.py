import re
import ctypes
import platform
import feedparser
import sys
import datetime
import webbrowser

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QBasicTimer
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QPushButton, QMainWindow, \
    QLabel, QGridLayout, QLineEdit, QMessageBox, QInputDialog, QComboBox

if platform.system() == 'Windows':
    myappid = u'BBR.RSS Checker.Main.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class Main(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        #RSS to test: https://readms.net/rss
        layout = QWidget(self)
        self.setCentralWidget(layout)

        grid = QGridLayout()
        grid.setSpacing(10)

        rssLabel = QLabel("RSS Feed:", self)
        self.rssInput = QLineEdit(self)
        self.rssInput.textEdited.connect(self.enableButtons)
        self.btnCheckRss = QPushButton("Show", self)
        self.btnCheckRss.setToolTip("Show the RSS Feed")
        self.btnCheckRss.setEnabled(False)
        self.btnCheckRss.clicked.connect(self.printRss)
        
        inputLabel= QLabel("Looking for:", self)
        self.entryInput = QLineEdit(self)
        self.entryInput.textChanged.connect(self.enableButtons)
        self.btnHelpInput = QPushButton("Help", self)
        self.btnHelpInput.setToolTip("Help me with the input!")
        self.btnHelpInput.setEnabled(False)
        self.btnHelpInput.clicked.connect(self.helpInput)

        timerLabel = QLabel("Check:", self)
        self.combo = QComboBox(self)
        self.combo.addItems(["Once", "Every minute", "Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Every hour"])
        self.combo.setEnabled(False)

        self.statusLabel = QLabel("", self)
        self.lastLabel = QLabel("", self)

        self.buttonStart = QPushButton("Check the RSS feed", self)
        self.buttonStart.setEnabled(False)
        self.buttonStart.clicked.connect(self.startChecking)

        grid.addWidget(rssLabel, 1, 0)
        grid.addWidget(self.rssInput, 1, 1)
        grid.addWidget(self.btnCheckRss, 1, 2)
        grid.addWidget(inputLabel, 2, 0)
        grid.addWidget(self.entryInput, 2, 1)
        grid.addWidget(self.btnHelpInput,2,2)
        grid.addWidget(timerLabel, 3, 0)
        grid.addWidget(self.combo, 3, 1, 1, 2)
        grid.addWidget(self.buttonStart, 4, 0, 1, 3)

        grid.addWidget(self.statusLabel, 5, 0, 1,2)
        grid.addWidget(self.lastLabel, 5, 2)

        self.timer = QBasicTimer()

        layout.setLayout(grid)
        
        self.statusBar().showMessage("Ready")
        self.setWindowTitle('RSS Checker')
        self.setWindowIcon(QtGui.QIcon('icon.png'))

    def enableButtons(self):
        if len(self.rssInput.text()) > 0:
            self.btnHelpInput.setEnabled(True)
            self.btnCheckRss.setEnabled(True)
        else:
            self.btnCheckRss.setEnabled(False)
            self.btnHelpInput.setEnabled(False)

        if len(self.rssInput.text()) > 0 and len(self.entryInput.text()) > 0:
            self.buttonStart.setEnabled(True)
            self.combo.setEnabled(True)
        else:
            self.buttonStart.setEnabled(False)
            self.combo.setEnabled(False)

    def rssEntriesWarning(self, feed):
        if len(feed.entries) == 0:
            self.statusBar().showMessage("Warning!")
            QMessageBox.warning(self, "Warning!", "The current RSS has no entries.\nPlease make sure you are using a valid RSS feed")
            self.statusBar().showMessage("Ready")
            return True
        else:
            return False

    def startChecking(self):
        if not self.timer.isActive():
            rss = self.rssInput.text()
            feed = feedparser.parse(rss)
            if not self.rssEntriesWarning(feed):
                if not self.checkRSS():
                    timer = self.combo.currentIndex()
                    times = [0, 60000, 300000, 900000, 1800000, 3600000]
                    if timer != 0:
                        self.btnCheckRss.setEnabled(False)
                        self.btnHelpInput.setEnabled(False)
                        self.combo.setEnabled(False)
                        self.entryInput.setEnabled(False)
                        self.rssInput.setEnabled(False)
                        self.timer.start(times[timer], self)
                        now = datetime.datetime.now()
                        strHour = str(now.hour)
                        strMin = str(now.minute)
                        if len(strHour) == 1:
                            strHour = "0"+strHour
                        if len(strMin) == 1:
                            strMin = "0"+ strMin
                        message = "Last checked: "+ strHour +":"+ strMin
                        self.statusLabel.setText(message)
                        self.buttonStart.setText('Stop')
        elif self.timer.isActive():
            self.btnCheckRss.setEnabled(True)
            self.btnHelpInput.setEnabled(True)
            self.combo.setEnabled(True)
            self.entryInput.setEnabled(True)
            self.rssInput.setEnabled(True)
            self.timer.stop()
            self.buttonStart.setText('Check the RSS feed')
            self.statusLabel.setText("")

    def checkRSS(self):
        flag = False

        rss = self.rssInput.text()
        check = self.entryInput.text()
        name, number = self.getWords(check)
        
        message = "Looking into the RSS feed for "+check+" ..."
        self.statusBar().showMessage(message)

        feed = feedparser.parse(rss)
        for post in feed.entries:
            if name in post.title.lower() and number in post.title.lower():
                message = "It's here! - " + check
                self.statusBar().showMessage(message) 
                message = "Found a post that matches.\n"
                message += post.title
                message += "\nDo you want to visit the page?"
                reply = QMessageBox.warning(self, "It's here", message, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    webbrowser.open(post.link)
                self.statusLabel.setText("")
                flag = True
                break
        if not flag:
            self.statusBar().showMessage("Not found :(")
        return flag

    def timerEvent(self, e):
        if self.checkRSS():
            self.timer.stop()
            self.btnCheckRss.setEnabled(True)
            self.btnHelpInput.setEnabled(True)
            self.combo.setEnabled(True)
            self.entryInput.setEnabled(True)
            self.rssInput.setEnabled(True)
            self.buttonStart.setText('Check the RSS feed')
            self.statusLabel.setText("")
        else:
            now = datetime.datetime.now()
            message = "Last checked: "+str(now.hour)+":"+str(now.minute).zfill(2)
            self.statusLabel.setText(message)

    def printRss(self):
        rss = self.rssInput.text()
        if not rss == "":
            self.statusBar().showMessage("Reading the RSS Feed...")
            feed = feedparser.parse(rss)
            if not self.rssEntriesWarning(feed):
                message = "Found "+ str(len(feed.entries)) +" entries\n"
                message += "="*25 +"\n"
                for post in feed.entries:
                    message += post.title + "\n"
                QMessageBox.about(self, "Entries on the RSS feed", message)
        self.statusBar().showMessage("Ready")

    def helpInput(self):
        flags = Qt.WindowFlags(QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        rss = self.rssInput.text()
        if not rss == "":
            self.statusBar().showMessage("Reading the RSS Feed...")
            feed = feedparser.parse(rss)
            if not self.rssEntriesWarning(feed):
                entries = []
                for post in feed.entries:
                    entries.append(post.title)
                self.statusBar().showMessage("Select an option")
                item, okPressed = QInputDialog.getItem(self, "Input assist","Current entries:",
                        entries, 0, True, flags)
                if okPressed and item:
                    self.entryInput.setText(item)
        self.statusBar().showMessage("Ready")

    def getWords(self, string):
        string = string.split(".")[0]
        m = re.findall(r"\[([A-Za-z0-9_]+)\]", string)
        for line in m:
            remove = "["+line+"]"
            string = string.replace(remove,"")
        string = string.lstrip().rstrip()

        if(any(char.isdigit() for char in string)):
            newString = string[::-1]
            counter = 0
            for number in newString:
                if number.isdigit():
                    counter += 1
                else:
                    break
            number = (string[-counter:]).lower()
            name = string[:-(counter+1)].lower()

        else:
            number = ''
            name = string
        return name, number

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    program = Main()
    program.show()
    sys.exit(app.exec_())