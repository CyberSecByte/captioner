# @author: CypherpunkSamurai
# @license: MIT
# A program to assist in tagging of images

import sys
import logging
import shelve # for settings
from PyQt5 import QtWidgets, uic

# Required
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

# Image
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QRectF


# Lists
from src import utils
import os
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QColor

# Short Cuts
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

# theme
from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import qApp


# Use MainWindow UI
from src.ui.MainWindow import Ui_MainWindow
from src.ui.Theme import ThemeChooseDlg, apply_theme

    
__version__ = 0.2
__author__ = "Cypherpunk Samurai"
__author_email__ = "cypherpunksamurai@protonmail.com"

logging.basicConfig(
    level=logging.INFO
)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        Main Window Class
    """
    current_folder = None
    current_image = None
    
    # image handling
    current_image_pixmap = None
    current_scene = None
    
    # colors
    colors = {
        "green": QColor("#8dd4b2"),
        "red": QColor("#f09ead"),
        "yellow": QColor("#f2bc5d"),
    }
    
    # cache
    cached_caption = {}
    
    
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.bind_connect()
    
    def open_folder(self):
        """
            Open a project folder
        """
        if self.current_folder:
            self.close_folder()
        
        # Open Folder
        current_folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        # If not selected
        logging.info(f"opening folder: {current_folder}")
        if current_folder == None or current_folder == "":
            logging.info("No folder was selected...")
            return
        else:
            self.current_folder = str(current_folder)
        
        # List Files
        for file in utils.list_images(self.current_folder):
            item = QListWidgetItem(file)
            
            # check if caption file is present
            filename = os.path.join(self.current_folder, file)
            caption_path = utils.change_file_ext(filename, "txt")
            
            # if caption file present set green
            if os.path.exists(caption_path) and not utils.is_empty(caption_path):
                item.setBackground(self.colors["green"])
            elif utils.is_empty(caption_path):
                item.setBackground(self.colors["red"])
            
            # add item
            self.listFile.addItem(item)
            
        # enable widget
        self.txtCaption.setEnabled(True)
        self.listFile.setEnabled(True)


    def close_folder(self):
        """
            Handles File Menu "Close"
        """
        # Close the folder
        self.current_folder = None
        self.listFile.clear()
        self.img.setScene(QGraphicsScene())
        self.txtCaption.clear()
        
        # btn
        self.btnSaveCaption.setEnabled(False)
        self.txtCaption.setEnabled(False)
        self.listFile.setEnabled(False)
        
        # Status
        self.setStatusTip("Ready")
    
    
    def message(self, text):
        """
            Message
        """
        QMessageBox.information(self, "Info", text)
    
    
    def list_item_select(self, current_item, old_item):
        """
            Runs when the list item is clicked
        """
        # list was cleared
        if current_item is None:
            return
        
        # get file
        text = current_item.text()
        file_path = os.path.join(self.current_folder, text)
        
        # path
        if not os.path.exists(file_path):
            logging.info("file not found")
            return
        
        # save current
        if not self.txtCaption.document().isEmpty() and self.txtCaption.document().toPlainText() and self.txtCaption.document().isModified():
            # cache
            self.cached_caption[old_item.text()] = self.txtCaption.document().toPlainText()
            self.txtCaption.clear()
            logging.info("caption was cached...")
            
            # old item color
            old_item.setBackground(self.colors["yellow"])
            
        self.current_image = file_path
        # load the image
        self.load_image()
        # render the new image
        self.render_scene()
        
        # btn
        self.btnSaveCaption.setEnabled(True)
        
        # load caption if exists
        self.load_caption()

    
    def load_image(self, url=None):
        """
            loads a image to a self.img_scene pixmap for rendering and renders
        """
        if url == None and not self.current_image == None: url=self.current_image
        else: return
        logging.info("currently selected: " + url)
        
        self.img.setAlignment(Qt.AlignCenter)
        
        # set
        self.current_image_pixmap = QPixmap(url)
        self.img_scene = QGraphicsScene()
        self.img_scene.addPixmap(self.current_image_pixmap)
        
    
    def render_scene(self):
        """
            Render self.img_scene without reloading the image
        """
        
        # Scene
        self.img.setScene(self.img_scene)
        
        # Scale
        self.img.fitInView(QRectF(0, 0, self.current_image_pixmap.width(), self.current_image_pixmap.height()), Qt.KeepAspectRatio)


    def resizeEvent(self, event):
        """
            Overrides the resize event
        """
        
        # render image everytime window resizes
        if self.current_image: self.render_scene()
        
        # resize
        QtWidgets.QMainWindow.resizeEvent(self, event)


    def load_caption(self, filename=None):
        """
            Load caption from cache or txt if exits else return empty
        """
        # clear
        self.txtCaption.clear()
        
        image_filename = self.listFile.currentItem().text()
        # filename
        if filename == None:
            filename = os.path.join(self.current_folder, image_filename)
        
        # caption file
        caption_path = utils.change_file_ext(filename, "txt")
        
        # caption
        caption = None
        
        # log("%i cached caption" % len(self.cached_caption))
        if os.path.exists(caption_path):
            caption = self.read_caption(caption_path)
        elif image_filename in self.cached_caption:
            caption = self.cached_caption.get(image_filename)
        
        
        self.txtCaption.document().setPlainText(caption)
        
        # simulate loading file
        # change detection false positive avert
        self.txtCaption.document().setModified(False)
        

    def btn_save_caption_clicked(self):
        """
            Handles SaveCaption button click
        """
        
        # cap
        caption = self.txtCaption.document().toPlainText()
        
        # save caption in cache
        self.cached_caption[self.listFile.currentItem().text()] = caption
        
        # filename
        filename = os.path.join(self.current_folder, self.listFile.currentItem().text())

        # caption file
        caption_path = utils.change_file_ext(filename, "txt")
        self.save_caption(caption_path, caption)
        
        # set the current item to green
        if not len(caption) == 0: self.listFile.currentItem().setBackground(self.colors["green"])
        else: self.listFile.currentItem().setBackground(self.colors["red"])
        
        # simulate file save
        self.txtCaption.document().setModified(False)
    
    
    def save_caption(self, filename, caption):
        """
            Save the caption in a txt file
        """
        with open(filename, "w+") as file:
            file.write(caption)
        
        logging.info(f"[+] {filename}")
        logging.info("Saved caption...")

    def read_caption(self, filename):
        """
            Read the caption from a txt file
        """
        caption = None
        with open(filename, "r", encoding="utf-8", errors="ignore") as file:
            caption = file.read()
        
        return caption

    def choose_theme_dialog(self):
        """
            Show a choose theme dialog
        """
        dlg = ThemeChooseDlg()
        if dlg.exec_():
            
            # get returned value
            values = dlg.getResult()
            
            # apply theme
            apply_theme(values)
            
            # property
            QtWidgets.QApplication.instance().setProperty("current_style", values)
            
            # save current settings
            try:
                with shelve.open("config") as settings:
                    settings["current_style"] = values
            except Exception as e:
                logging.info("cannot write current_style to shelve. ", e)
            return

        else:
            logging.info("no theme chosen")
            return
        
    def about(self):
        self.message(f"Captioner {__version__}\n\nA Captioning tool created for image captioning. \n\n💻Authour: {__author__}\n📫Email: {__author_email__}")
    
    
    def caption_shortcut_1(self):
        """
            set's caption to list view
        """
        logging.info("set focus to list view")
        self.listFile.setFocus()
        self.listFile.setCurrentRow(self.listFile.currentRow())
    
    @pyqtSlot()
    def caption_shortcut_2(self):
        """
            set's caption to caption text box
        """
        self.txtCaption.setFocus()
    
    def bind_connect(self):
        """
            Connection Binder
        """
        # Exit
        self.mnuExit.triggered.connect(sys.exit)
        # Folder Select
        self.mnuOpenFolder.triggered.connect(self.open_folder)
        # Folder Close
        self.mnuCloseFolder.triggered.connect(self.close_folder)
        # Theme
        self.mnuTheme.triggered.connect(self.choose_theme_dialog)
        # About
        self.mnuAbout.triggered.connect(self.about)
        
        # ListWidget
        self.listFile.currentItemChanged.connect(self.list_item_select)
        
        # Caption Button
        self.btnSaveCaption.clicked.connect(self.btn_save_caption_clicked)
        
        # Short Cuts
        self.cs1 = QShortcut(QKeySequence("Ctrl+Alt+Left"), self)
        self.cs1.activated.connect(self.caption_shortcut_1)
        self.cs2 = QShortcut(QKeySequence("Ctrl+Alt+Right"), self)
        self.cs2.activated.connect(self.caption_shortcut_2)
        


if __name__ == "__main__":
    
    # Run
    app = QtWidgets.QApplication(sys.argv)
    app.setProperty("current_style", None)
    
    # read settings
    if os.path.exists("config.dat"):
        try:
            with shelve.open("config") as settings:
                if "current_style" in settings: app.setProperty("current_style", settings["current_style"])
        except Exception as e:
            logging.exception(e)
        finally: pass

    
    # current style
    if app.property("current_style"):
        apply_theme(app.property("current_style"))
    
    # Windows
    window = MainWindow()
    window.show()
    app.exec()
