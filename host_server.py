import threading
import socket
import pickle


connections = set() #creates initial connection to seperate connectors from members 
connections_lock = threading.Lock() 
server_members = {} #keeps ip and name of each person in server currently. 
members_details = {} #keeps description and name of each person currently in server. 
member_logins = {}#keeps members login details (username:password)

current_server_members = {"public chat": {} } #send messages to people in this server currently
server_members = {  "public chat": {}   } #people in the server have the option to join

#starts the functionality of the server
#while loop is a blocking call so a worker thread must be made
#server.accept gets overwritten each connections therefore connections list is made for the server_controller to send messages to
def server_init():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", 800))
    server.listen()

    while True:
        connection, address = server.accept()
        with connections_lock:
            connections.add(connection)
        threading.Thread(target=server_controller, args=(connection,)).start()

#handles recoeved messages and distributes them accross all clients
def server_controller(connection):
    try:
        while True:
            msg = connection.recv(2048)
            if msg:
                test = pickle.loads(msg)
                print(test)


                ## if a profile message is recieved.
                if test[0] == "sign-up":
                    if test[1] not in member_logins:

                        #add user to each server and tell user they may passed
                        connection.send(pickle.dumps(["sign-up-pass"]))
                        server_members[test[1]] = connection
                        members_details[test[1]] = test[2]
                        member_logins[test[1]] = test[3]
                        connection.send(pickle.dumps(members_details))

                        with connections_lock:
                                for client in connections:
                                    try:
                                        client.sendall(pickle.dumps(members_details))
                                    except:
                                        pass
                    else:
                        connection.send(pickle.dumps(["sign-up-fail"]))
                if test[0] == "login":
                    if str(member_logins[test[1]]) == str(test[2]):
                        try:
                            connection.send(pickle.dumps(["login-pass"]))
                            connection.send(pickle.dumps(members_details))
                        except:
                            pass
                    else: 
                        try:
                            connection.send(pickle.dumps(["login-fail"]))
                        except:
                            pass


                #sets the current server the user is demanding
                if test[0] == "current_server":
                    try:
                        for server in current_server_members:
                            for name in current_server_members[server]:
                                if name == test[2]:
                                    del current_server_members[server][name]
                    except:
                        pass
                    current_server_members[test[1]][test[2]] = connection

                #sends a message to everyone in this persons server
                if test[0] == "message":
                    for server in current_server_members:
                        for name in current_server_members[server]:
                            if name == test[1]:
                                for con in current_server_members[server].values():
                                    try:
                                        con.send(msg)
                                    except:
                                        pass

                #creates a group chat with these people then demands them to add it to their server list
                if test[0] == "create group":
                    current_server_members[test[1]] = {}
                    server_members[test[1]] = {}
                    try:
                        print(test[3])
                        for person in test[3]:
                            ip = server_members[person]
                            server_members[test[1]][person] = ip
                    except:
                        pass
                    server_members[test[1]][test[2]] = connection     
                    for con in server_members[test[1]].values():
                        try: 
                            con.send(pickle.dumps(["add server", test[1]]))
                        except:
                            pass
            else:
                pass       
    finally:
        with connections_lock:
            connections.remove(connection)
        connection.close()

def members_list(connection):
    if connection:
        pass

if __name__ == "__main__":
    threading.Thread(target = server_init).start()