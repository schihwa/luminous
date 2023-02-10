
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from client_gui import Ui_MainWindow
import threading
from PyQt5 import QtCore
import socket
from datetime import datetime
from PyQt5 import QtCore
from PyQt5 import QtCore, QtWidgets
import ipaddress
from PyQt5 import sip
import pickle



class Receiver(QtCore.QThread):
    signal = QtCore.pyqtSignal(object)
    
    def __init__(self, socket):
        super(Receiver, self).__init__()
        self.sock = socket
        
    def run(self):
        while True:
                self.signal.emit(pickle.loads( self.sock.recv(5000) ))

class Luminious(QMainWindow):
    def __init__(self):
        super().__init__()

        #sets up the GUI element of the code. 
        self.main_win = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_win)
        self.ui.leave_profiles_btn.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.main_page))

        #sets up buttons for each of the pages 
        self.ui.join_server_btn.clicked.connect(self.username_pg)
        self.ui.message_send_btn.clicked.connect(self.send)
        self.ui.back_join_server_btn.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.join_server_page))
        self.ui.signup_btn.clicked.connect(lambda x: self.ip_checker("sign-up"))
        self.ui.login_btn.clicked.connect(lambda x: self.ip_checker("login"))
        self.ui.back_login_server_btn.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.join_server_page))
        self.ui.chat_members_btn.clicked.connect(self.members)
        self.ui.leave_server.clicked.connect(self.leave_server)
        self.ui.leave_group_creation.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.groups_page))
        self.ui.login_server_btn.clicked.connect(lambda x: threading.Thread(target = self.connect).start())
        self.ui.public_chat_btn.clicked.connect(self.group_handler)
        self.ui.create_group_btn.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.group_creator_page))
        self.ui.create_group.clicked.connect(self.create_group)
        self.ui.back_chat_btn.clicked.connect(lambda x: self.ui.stackedwidget.setCurrentWidget(self.ui.groups_page))
        self.selected = []
        
        #defines client socket and passes to reciever class for further use
        #connecting a signal from the reciever class to the slot
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
        self.receiver = Receiver(self.socket)
        self.receiver.signal.connect(self.message_router)

    #deletes servers from server list after leaving server
    def leave_server(self):
        for object in self.ui.scrollArea.findChildren(QPushButton):
            object = self.ui.scrollArea.findChild(QPushButton)
            sip.delete(object) 
        self.ui.stackedwidget.setCurrentWidget(self.ui.join_server_page)


    #handles server creation
    def create_group(self):
        if len(self.ui.server_text_box.text()) > 3:
            self.socket.send(pickle.dumps(list(("create group", self.ui.server_text_box.text(), self.username, self.selected))))
            self.ui.stackedwidget.setCurrentWidget(self.ui.groups_page)
        else:
            self.ui.server_creation_label.setText("your server name must be over 3 charcters!")

    def show(self): 
        self.main_win.show()
    
    #shows members in server
    def members(self):
        if self.ui.members_scrollArea.isVisible():
            self.ui.members_scrollArea.hide()
        else:
            self.ui.members_scrollArea.show()

    #ip page 
    #checks if the ip provided is correctly formatted for the socket to connect to or use localhost if lan is being utilized if not tell the user its not a valid ip. 
    def ip_checker(self, button):
        self.selection = button
        self.host = self.ui.ip_text_box.text()
        try:
            ipaddress.IPv4Network(self.host)
            if button == "sign-up":
                self.ui.stackedwidget.setCurrentWidget(self.ui.username_page)
            if button == "login":
                self.ui.stackedwidget.setCurrentWidget(self.ui.login_page)

        except:
            if self.host == "localhost":
                if button == "sign-up":
                    self.ui.stackedwidget.setCurrentWidget(self.ui.username_page)
                if button == "login":
                    self.ui.stackedwidget.setCurrentWidget(self.ui.login_page)
            else:
                self.ui.ip_label.setText("this isnt a valid ip!")
                return


    #tells server the current server 
    def group_handler(self):
        self.ui.chat_text_browser.clear()
        if self.sender().objectName() == "public_chat_btn":
            server = "public chat"
        else: server = self.sender().objectName() 

        self.socket.send(pickle.dumps(("current_server", server, self.username)))
        self.ui.stackedwidget.setCurrentWidget(self.ui.main_page)          
 
    #connects to host computer
    def connect(self):
        try:
            self.socket.connect((self.host, 800))
            self.receiver.start()
        except:
            if self.selection == "sign-up":
                #threading.Thread(target = image_sender, args = (self.username, self.picture))
                self.socket.send(pickle.dumps(list(("sign-up", self.username, self.ui.intro_text.toPlainText(), self.password))))
            else:
                self.username = self.ui.username_login_text_box.text()
                self.socket.send(pickle.dumps(list(("login", self.ui.username_login_text_box.text(), self.ui.password_login_text_box.text()))))
    

    #handles login responses
    def login_handler(self, data):
            if data[0] == "login-pass":
                self.ui.stackedwidget.setCurrentWidget(self.ui.groups_page)

            if data[0] == "login-fail":
                self.ui.username_login_label.setText("invalid login!")
    
    def sign_up_handler(self, data):
        if data[0] == "sign-up-fail":
            self.ui.username_label.setText("this username is taken!")
        if data[0] == "sign-up-pass":
            self.ui.stackedwidget.setCurrentWidget(self.ui.groups_page)

#routes server messages
    def message_router(self, data):

        if type(data) is list:
                if data[0] == "message":
                    self.display_message(data)
                    print("its good")

                if data[0].startswith("login"):
                    self.login_handler(data)

                if data[0].startswith("sign-up"):
                    self.sign_up_handler(data)
                
                if data[0] == "add server":
                    servername = QtWidgets.QPushButton(self.ui.add_members_scrollwheel)
                    servername.setText(data[1])
                    self.ui.verticalLayout_2.addWidget(servername)
                    servername.setObjectName(data[1])
                    servername.clicked.connect(self.group_handler)
                    self.ui.verticalLayout_4.addWidget(servername)
        else:  

            for object in self.ui.members_scrollArea.findChildren(QPushButton):
                    object = self.ui.members_scrollArea.findChild(QPushButton)
                    sip.delete(object)

            for object in self.ui.add_members_scrollwheel.findChildren(QPushButton):
                    object = self.ui.add_members_scrollwheel.findChild(QPushButton)
                    sip.delete(object) 

            self.profile_builder(data)
            self.members = data  

    #builds profile for each member in server
    def profile_builder(self, data):
        self.memberslist = data
        self.selected = []
        id =1

        for name in data:
            if name != self.username:
                widget = QtWidgets.QPushButton(self.ui.members_scrollArea)
                widget.setText(name)
                widget.setObjectName(name)
                self.ui.verticalLayout.addWidget(widget)
                widget.clicked.connect(self.profile_page)

                iden = f"name{id}"
                widget2 = QtWidgets.QPushButton(self.ui.add_members_scrollwheel)
                widget2.setText(name)
                widget2.setObjectName(iden)
                self.ui.verticalLayout_2.addWidget(widget2)
                widget2.clicked.connect(self.add_to_server_creation)
                id += 1

    #adds members to members scroll area
    def add_to_server_creation(self):
        if self.sender().text() not in self.selected:
            btn = self.sender().text()
            self.ui.added_members.append(self.sender().text())
            self.selected.append(btn)
        else: 
            self.selected.remove(self.sender().text())
            self.ui.added_members.clear()
            for name in self.selected:
                self.ui.added_members.append(name)


    #creates profile page for member requested
    def profile_page(self):
        user = self.sender().text()
        self.ui.stackedwidget.setCurrentWidget(self.ui.profile_page)
        self.ui.intro_profile_desc.setText(self.members[user])
        self.ui.username_profile.setText(user)

    #each message received by the receiver gets emitted to this slot to be formatted and displayed on the QTextBrowser
    def display_message(self, message):
        self.ui.chat_text_browser.append(f"{message[1]} sent at {datetime.now().strftime('%H:%M:%S')}\n{message[2]}\n")
    
    #checks username and intro
    def username_pg(self):
        self.username = str(self.ui.username_text_box.text())
        self.password = self.ui.password_text_box.text()
        if self.username.isalpha() and len(self.username) > 2:
            if len(self.ui.intro_text.toPlainText()) > 0:
                if len(self.password) > 2:
                    threading.Thread(target = self.connect).start()  
                else:
                    self.ui.username_label.setText("you must have a password longer than 3 characters!")   
            else:
                self.ui.username_label.setText("you must have an intro!") 
                return
        else:
            self.ui.username_label.setText("username must be 3 or more letters!")
            return

    #if the text in QEditLine is atleast one character after the send button is clicked its contents will be sent and the text box cleared. 
    #if it cant be sent the client has disconnected therefore the socket will be closed and the client will be sent back to the username page. 
    def send(self):
            if self.ui.message_text_box.text():
                try:    
                    self.socket.send(pickle.dumps(   list(("message", self.username, self.ui.message_text_box.text()))   ))
                except Exception as error:
                    print(f"couldnt send message: {error}")

                    self.ui.stackedwidget.setCurrentWidget(self.ui.username_page)
                    
                self.ui.message_text_box.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    Luminious().show()
    sys.exit(app.exec_())   