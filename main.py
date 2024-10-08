import argparse
import sys
import tkinter as tk
from tkinter import scrolledtext as st
import tarfile
import time
import datetime

# Class that describes the window of user interface
class GUI: 
    def __init__(self, args, main_window): # Constructor
        # Getting arguments for subsequent using
        # self.args = args
        self.username = args[0]
        self.hostname = args[1]
        self.path_to_archive = args[2]

        # Binding processer
        self.processer = Processer(self.path_to_archive)
   
        # Window settings
        self.main_window = main_window 
        self.main_window.title("GUI Shell Emulator")
        self.main_window.wm_attributes("-topmost", 1)
        self.main_window.resizable(False, True)
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_columnconfigure(0, weight=1)

        # Display that shows actions in cmd
        self.display = st.ScrolledText(self.main_window, height=20, width=60)
        self.display.configure(background="#000000", foreground="#7FFF00")
        self.display.grid(row=0, column=0, columnspan=2, pady=5)
        self.prompt_insert()
        self.display.config(state='disabled')

        # Standard entry
        self.input_area = tk.Entry(self.main_window, width=50)
        self.input_area.configure(background="#000000", foreground="#7FFF00")
        self.input_area.grid(row=1, column=0, pady=2)
        
        # Button that launches the entered command processing
        self.enter_btn = tk.Button(self.main_window, text="Enter", command=self.push_text)
        self.enter_btn.configure(background="#47B1DE", font=("Arial", 14, "bold"), foreground="#FFFFFF")
        self.enter_btn.grid(row=1, column=1, padx=2, pady=2, sticky='n')

    def close(self): # Closing the GUI
        self.main_window.quit()

    def prompt_insert(self): # Entering the prompt
        self.display.insert(tk.END, f"{self.username}@{self.hostname}:{self.processer.cur_dir}$ ") #TODO: add username, hostname, cur dir

    def push_text(self): # Capturing the text from entry
        # Command text wrapping
        command = self.input_area.get()
        self.input_area.delete(0, tk.END)
        self.display.config(state='normal')
        self.display.insert(tk.END, command + '\n')

        # Processing command and printing result
        result = self.processer.process(command) 
        if self.processer.must_exit:
            self.close()
        self.display.insert(tk.END, result)
        self.prompt_insert()
        self.display.config(state='disabled')

# Class that operating with the user input
class Processer:
    def __init__(self, path_to_archive):
        self.must_exit = False
        self.path_to_archive = path_to_archive
        self.cur_dir = "~" # full path to current directory
        self.dir_system = {} # key - full dirpath, value - children
        self.files = []
        self.parse_archive()

    def parse_archive(self):
        if not tarfile.is_tarfile(self.path_to_archive):
            print("There is no .tar archive! Please create it before run the program.")
            self.must_exit = True
            return
        
        with tarfile.open(self.path_to_archive, 'r') as tar:
            self.dir_system["~"] = list()

            for member in tar.getmembers():
                if member.isdir():
                    self.dir_system["~/" + member.path] = list()
                elif member.isfile():
                    self.files.append("~/" + member.path)

            for member in tar.getmembers():
                spath = ("~/" + member.path).split("/")
                if self.dir_system.get("/".join(spath[:-1])) != None:
                   self.dir_system["/".join(spath[:-1])].append(spath[-1])

    def process(self, command): # Analysing command
        result, command_s = "", command.split()
        if not command_s:
            return result
        elif command_s[0] == "ls":
            result = self._ls(command_s[1:])
        elif command_s[0] == "exit":
            self._exit()
        elif command_s[0] == "cd":
            result = self._cd(command_s[1:])
        elif command_s[0] == "cp":
            result = self._cp(command_s[1:])
        elif command_s[0] == "uptime":
            result = self._uptime(command_s[1:])
        elif command_s[0] == "tree":
            result = self._tree(command_s[1:])
        else:
            result = f'Command "{command_s[0]}" is not found\n'
        return result

    def approve_dirpath(self, path): # returns full path if directory correct
        if path[-1] == "/": # ignore last '/'
            path = "/".join(filter(None, path.split("/")))
        if path.startswith(".."): # embedding parent directory
            path = path.replace("..", "/".join(self.cur_dir.split("/")[:-1]), 1)
        elif path.startswith("."): # embedding current directory
            path = path.replace(".", self.cur_dir, 1)
        if not path.startswith("~"): # if path still not full
            path = self.cur_dir + "/" + path # make it full
        return path if (self.dir_system.get(path) != None) else ""

    def approve_filepath(self, path): # returns full path if file correct
        if path.startswith(".."): # embedding parent directory
            path = path.replace("..", "/".join(self.cur_dir.split("/")[:-1]), 1)
        elif path.startswith("."): # embedding current directory
            path = path.replace(".", self.cur_dir, 1)
        if not path.startswith("~"): # if path still not full
            path = self.cur_dir + "/" + path # make it full
        return path if path in self.files else ""

    def get_name(self, path):
        return path.split("/")[-1]
    
    def get_parent(self, path):
        return "/".join(path.split("/")[:-1])

    def _ls(self, args):
        if not args: # current directory
            return " ".join(self.dir_system[self.cur_dir]) + "\n"
        path = self.approve_dirpath(args[0])
        if path:
            return " ".join(self.dir_system[path]) + "\n"
        else:
            return f"There is no directory with name '{args[0]}'\n"
            
    def _cd(self, args):
        if not args:
            return ""
        path = self.approve_dirpath(args[0])
        if path:
            self.cur_dir = path
            return ""
        else:
            return f"There is no directory with name '{args[0]}'\n"

    def _exit(self):
        self.must_exit = True

    def _cp(self, args):
        if len(args) != 2:
            return "Command 'cp' must have two arguments.\n"
        else:
            ar0_d = self.approve_dirpath(args[0])
            ar0_f = self.approve_filepath(args[0])
            ar1_d = self.approve_dirpath(args[1])
            ar1_f = self.approve_filepath(args[1]) 
            if ar0_f: # copy file
                if ar1_d: # copy to directory with creating the same file
                    if self.get_name(args[0]) not in self.dir_system.get(ar1_d):
                        self.dir_system.get(ar1_d).append(args[0].split("/")[-1])
                        self.files.append(ar1_d + "/" + str(args[0].split("/")[-1]))
                elif ar1_f: # copy to existing file
                    None
                elif self.approve_dirpath(self.get_parent(args[1])): # copy to directory with creating the new file
                    self.dir_system.get(self.approve_dirpath(self.get_parent(args[1]))).append(self.get_name(args[1]))
                    self.files.append(self.approve_dirpath(self.get_parent(args[1])) + "/" + str(self.get_name(args[1])))
                else:
                    return f"There is no such file or directory with name '{args[1]}'\n"

            elif ar0_d: # copy directory
                if ar1_f: # copy dir to file
                    return f"'{self.get_name(args[1])}' is not a directory.\n"
                elif ar1_d: # copy dir to dir
                    if ar0_d in ar1_d:
                        return f"Cannot copy directory that contains or equal to target directory!\n"
                    self.recursive_copying(ar0_d, ar1_d)
                else:
                    return f"There is no such file or directory with name '{args[1]}'\n"
            else:
                return f"There is no such file or directory with name '{args[0]}'\n"
        return ""
            
    def recursive_copying(self, dir, target_dir):
        self.dir_system.get(target_dir).append(self.get_name(dir))
        new_dir = target_dir + "/" + self.get_name(dir)
        self.dir_system[new_dir] = list()
        for suc in self.dir_system.get(dir):
            full_suc = dir + "/" + suc
            if full_suc in self.files:
                self.files.append(new_dir + "/" + suc)
                self.dir_system.get(new_dir).append(suc)
            else:
                self.recursive_copying(full_suc, new_dir)

    def _uptime(self, args):
        work_time = str(round(time.time() - start_time)) # worktime in seconds
        cur_time = datetime.datetime.now().strftime("%H:%M:%S") # current time
        return cur_time + " up " + work_time + " sec\n"

    def _tree(self, args):
        if not args:
            return self.build_tree(self.cur_dir, "") + "\n"
        path = self.approve_dirpath(args[0])
        if path != "":
            return self.build_tree(path, "") + "\n"
        else:
            return f"There is no directory with name '{args[0]}'\n"
        
    def build_tree(self, root, indent): # recursive building of hierarchy
        if not self.dir_system.get(root) or self.dir_system.get(root) == None:
            return indent + self.get_name(root)
        else:
            s = indent + self.get_name(root)
            for suc in self.dir_system.get(root):
                s += "\n" + self.build_tree(root + "/" + suc, indent + "|--")
            return s

def get_args(): # Getting arguments transmitted to script
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="Имя пользователя")
    parser.add_argument("hostname", help="Имя компьютера")
    parser.add_argument("path_to_archive", help="Путь до архива")
    parser.add_argument("path_to_script", help="Путь до стартового скрипта")
    args = parser.parse_args()
    return [args.username, args.hostname, args.path_to_archive, args.path_to_script]


start_time = time.time()
if __name__ == "__main__":
    args = get_args()
    main_window = tk.Tk()
    Gui = GUI(args, main_window)
    main_window.mainloop()

