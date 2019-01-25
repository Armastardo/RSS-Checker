import re
import ctypes
import platform
import feedparser
import sys
import datetime
import webbrowser
import logging

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QBasicTimer
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QPushButton, QMainWindow, \
    QLabel, QGridLayout, QLineEdit, QMessageBox, QInputDialog, QComboBox, QDialog, QTableWidget, \
    QTableWidgetItem, QHBoxLayout, QVBoxLayout, QHeaderView, QAbstractItemView, QStatusBar


if platform.system() == 'Windows':
    myappid = u'BBR.RSS Checker.Main.1.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# I don't know what the hell Main.getWords() is doing so I'll print some annoying stuff
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Main(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QWidget(self)
        self.setCentralWidget(layout)

        grid = QGridLayout()
        grid.setSpacing(10)

        rssLabel = QLabel("RSS Feed:", self)
        self.rssInput = QLineEdit(self)
        self.rssInput.textEdited.connect(self.enableButtons)
        self.btnCheckRss = QPushButton("Load", self)
        self.btnCheckRss.setToolTip("Loads the RSS")
        self.btnCheckRss.setEnabled(False)
        self.btnCheckRss.clicked.connect(self.showRss)

        inputLabel= QLabel("Looking for:", self)
        self.entryInput = QLineEdit(self)
        self.entryInput.textChanged.connect(self.enableButtons)

        timerLabel = QLabel("Check:", self)
        self.combo = QComboBox(self)
        self.combo.addItems(["Once", "Every minute", "Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Every hour"])
        self.combo.setEnabled(False)

        self.statusBar = QStatusBar()

        self.buttonStart = QPushButton("Check the RSS feed", self)
        self.buttonStart.setEnabled(False)
        self.buttonStart.clicked.connect(self.startChecking)

        grid.addWidget(rssLabel, 1, 0)
        grid.addWidget(self.rssInput, 1, 1)
        grid.addWidget(self.btnCheckRss, 1, 2)
        grid.addWidget(inputLabel, 2, 0)
        grid.addWidget(self.entryInput, 2, 1)
        # grid.addWidget(self.btnHelpInput,2,2)
        grid.addWidget(timerLabel, 3, 0)
        grid.addWidget(self.combo, 3, 1, 1, 2)
        grid.addWidget(self.buttonStart, 4, 0, 1, 3)

        self.rssdialog = FeedEntries()
        self.rssdialog.reloadButton.clicked.connect(self.showRss)

        self.timer = QBasicTimer()

        self.loadedFlag = False

        layout.setLayout(grid)

        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        self.setWindowTitle('RSS Checker')
        self.setWindowIcon(QtGui.QIcon('icon.png'))

    def enableButtons(self):
        if len(self.rssInput.text()) > 0:
            self.loadedFlag = False
            self.rssdialog.purgeAll()
            self.btnCheckRss.setEnabled(True)
            if len(self.entryInput.text()) > 0:
                self.buttonStart.setEnabled(True)
                self.combo.setEnabled(True)
            else:
                self.buttonStart.setEnabled(False)
                self.combo.setEnabled(False)
        else:
            self.btnCheckRss.setEnabled(False)

    def rssEntriesWarning(self, feed):
        if len(feed.entries) == 0:
            self.statusBar.showMessage("Warning!")
            QMessageBox.warning(self, "Warning!", "The current RSS has no entries.\nPlease make sure you are using a valid RSS feed")
            self.statusBar.showMessage("Ready")
            return True
        else:
            return False

    def startChecking(self):
        if not self.timer.isActive():
            if not self.checkRSS():
                timer = self.combo.currentIndex()
                times = [0, 60000, 300000, 900000, 1800000, 3600000]
                if timer != 0:
                    self.btnCheckRss.setEnabled(False)
                    self.combo.setEnabled(False)
                    self.entryInput.setEnabled(False)
                    self.rssInput.setEnabled(False)
                    self.timer.start(times[timer], self)
                    now = self.getTime()
                    message = "Last checked: "+ now
                    self.statusBar.showMessage(message)
                    self.buttonStart.setText('Stop')
        elif self.timer.isActive():
            self.btnCheckRss.setEnabled(True)
            self.combo.setEnabled(True)
            self.entryInput.setEnabled(True)
            self.rssInput.setEnabled(True)
            self.timer.stop()
            self.buttonStart.setText('Check the RSS feed')
            self.statusBar.clearMessage()

    def checkRSS(self):
        flag = False

        entries = self.getRss()
        if entries == list():
            return False
        check = self.entryInput.text()
        name, number = self.getWords(check)
        found = list()

        message = "Looking into the RSS feed for "+check+" ..."
        self.statusBar.showMessage(message)

        for post in entries:
            if name in post['title'].lower() and number in post['title'].lower():
                found.append(post)
                self.statusBar.clearMessage()
                flag = True
        if not flag:
            self.statusBar.showMessage("Not found :(")
        else:
            self.showRss(found)
        return flag

    def getTime(self):
        now = datetime.datetime.now()
        timestamp = datetime.time(now.hour, now.minute).isoformat()[:-3]
        logger.debug(timestamp)
        return timestamp

    def timerEvent(self, e):
        if self.checkRSS():
            self.timer.stop()
            self.btnCheckRss.setEnabled(True)
            self.combo.setEnabled(True)
            self.entryInput.setEnabled(True)
            self.rssInput.setEnabled(True)
            self.buttonStart.setText('Check the RSS feed')
            self.statusBar.showMessage()
        else:
            message = "Last checked: "+self.getTime().zfill(2)
            self.statusBar.showMessage(message)

    def getRss(self):
        rss = self.rssInput.text()
        if rss != str():
            self.statusBar.showMessage("Reading the RSS Feed...")
            feed = feedparser.parse(rss)
            if not self.rssEntriesWarning(feed):
                entries = list()
                now = self.getTime()
                for post in feed.entries:
                    entry = {"title": post.title, "link": post.link, "added": now}
                    entries.append(entry)
            else:
                return list()
        return entries

    def showRss(self, entries=None):
        logger.info(entries)
        if not entries:
            results = self.getRss()
        else:
            results = entries
        if results == list():
            return
        if not self.loadedFlag:
            self.loadedFlag = True
            for i in results:
                self.rssdialog.addItems(i, self.rssdialog.feedlist.rowCount())
        else:
            for i in reversed(results):
                self.rssdialog.addItems(i, 0)
        self.rssdialog.show()

    def getWords(self, string):
        string = string.split(".")[0]
        m = re.findall(r"\[([A-Za-z0-9_]+)\]", string)
        logger.debug((string, m))

        for line in m:
            remove = "["+line+"]"
            string = string.replace(remove,"")
        string = string.lstrip().rstrip()
        logger.debug(string)

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
            logger.debug(newString)
        else:
            number = ''
            name = string
        logger.debug((number, name))
        return name, number


class FeedEntries(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(800,500)
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        self.feedlist = QTableWidget()
        self.feedlist.setColumnCount(3)
        header = self.feedlist.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.feedlist.setHorizontalHeaderLabels(("Added", "Title", "URL"))
        self.feedlist.setSelectionMode(QAbstractItemView.SingleSelection)
        self.feedlist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setLayout(hlayout)
        self.removeButton = QPushButton("Remove")
        self.reloadButton = QPushButton("Reload")
        vlayout.addWidget(self.removeButton)
        vlayout.addWidget(self.reloadButton)
        vlayout.addStretch()
        hlayout.addWidget(self.feedlist)
        hlayout.addLayout(vlayout)
        self.removeButton.clicked.connect(self.removeSelected)
        self.feedlist.itemDoubleClicked.connect(self.openWeb)

    def addItems(self, entry, place):
        find = self.feedlist.findItems(entry['link'], Qt.MatchExactly)
        if find != list():
            logger.debug(find)
            return
        rows = self.feedlist.rowCount()
        self.feedlist.setRowCount(rows+1)
        if place != rows:
            self.relocateItems(place, False)
        items = (QTableWidgetItem(entry['added']),
                QTableWidgetItem(entry['title']),
                QTableWidgetItem(entry['link']))
        for i in range(0, 3):
            items[i].setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.feedlist.setItem(place, i, items[i])

    def removeItem(self, row):
        for i in range(0, 3):
            item = self.feedlist.takeItem(row, i)
            del item
        self.relocateItems(row)
        rows = self.feedlist.rowCount()
        if rows != 0:
            self.feedlist.setRowCount(rows-1)

    def purgeAll(self):
        self.feedlist.setRowCount(0)
        self.removeItem(0)

    def removeSelected(self):
        self.removeItem(self.feedlist.currentRow())

    def relocateItems(self, place, removing=True):
        rows = self.feedlist.rowCount()
        if removing:
            temp = place
        else:
            temp = rows
        while True:
            logger.debug((temp, place))
            if removing:
                if temp == rows:
                    break
            else:
                if temp < 0:
                    break
            for i in range(0, 3):
                if removing:
                    item = self.feedlist.takeItem(temp+1, i)
                    self.feedlist.setItem(temp, i, item)
                else:
                    item = self.feedlist.takeItem(temp, i)
                    self.feedlist.setItem(temp+1, i, item)
            if removing:
                temp += 1
            else:
                temp -= 1

    def openWeb(self):
        row = self.feedlist.currentRow()
        item = self.feedlist.item(row, 2)
        link = item.text()
        webbrowser.open(link)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    program = Main()
    program.show()
    sys.exit(app.exec_())
