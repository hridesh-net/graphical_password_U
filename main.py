import ast
import numpy as np
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2

MSE_THRESHOLD = 500

def segment_image(image_path, num_segments):
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    segment_width = int(width / num_segments)

    segments = []
    for i in range(num_segments):
        segment_start = i * segment_width
        segment_end = segment_start + segment_width
        segment = image[0:height, segment_start:segment_end]
        segments.append(segment)

    return segments

def create_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(username text PRIMARY KEY, password_segments text)''')
    conn.commit()
    conn.close()

def create_user(username, password_image_path, num_segments):
    segments_data = segment_image(password_image_path, num_segments)
    segments_data_str = str(segments_data)
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (username, segments_data_str))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user is None:
        return None
    
    password_segments_str = user[1]
    password_segments = ast.literal_eval(password_segments_str)
    
    return password_segments

def authenticate_user(username, password_image_path, num_segments):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('SELECT password_segments FROM users WHERE username = ?', (username,))
        stored_segments_data = c.fetchone()[0]

    # Load password image and segment it
    password_image = Image.open(password_image_path)
    width, height = password_image.size
    segment_width = int(width / num_segments)
    segments = [password_image.crop((i * segment_width, 0, (i+1) * segment_width, height)) for i in range(num_segments)]

    # Convert segments to numpy arrays and compare with stored segments
    stored_segments = [np.frombuffer(stored_segment_data.encode(), dtype=np.uint8).reshape((height, segment_width, 3)) for stored_segment_data in stored_segments_data]
    input_segments = [np.array(segment) for segment in segments]
    mse = [np.square(np.subtract(stored_segment, input_segment)).mean() for stored_segment, input_segment in zip(stored_segments, input_segments)]
    return sum(mse) < MSE_THRESHOLD

class GraphicalPasswordGUI:
    def __init__(self, master):
        self.master = master
        master.title('Graphical Password Login')
        master.geometry('400x300')

        self.username_label = tk.Label(master, text='Username:')
        self.username_label.pack()

        self.username_entry = tk.Entry(master)
        self.username_entry.pack()

        self.password_label = tk.Label(master, text='Password:')
        self.password_label.pack()

        self.password_image_path = ''
        self.password_button = tk.Button(master, text='Select Password Image', command=self.select_password_image)
        self.password_button.pack()

        self.authenticate_button = tk.Button(master, text='Authenticate', command=self.authenticate)
        self.authenticate_button.pack()

    def select_password_image(self):
        self.password_image_path = filedialog.askopenfilename(initialdir='.', title='Select Password Image', filetypes=[('Image Files', '.png;.jpg;*.jpeg')])
        if self.password_image_path:
            self.password_button.config(text=self.password_image_path)
    
    def authenticate(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showerror('Error', 'Please enter a username')
            return
        if not self.password_image_path:
            messagebox.showerror('Error', 'Please select a password image')
            return
        num_segments = 4
        authenticated = authenticate_user(username, self.password_image_path, num_segments)
        if authenticated:
            messagebox.showinfo('Success', 'Authentication successful')
        else:
            messagebox.showerror('Error', 'Authentication failed')

class GraphicalPasswordRegistrationGUI:
    def __init__(self, master):
        self.master = master
        master.title('Graphical Password Registration')
        master.geometry('400x300')
        self.username_label = tk.Label(master, text='Username:')
        self.username_label.pack()

        self.username_entry = tk.Entry(master)
        self.username_entry.pack()

        self.password_label = tk.Label(master, text='Password:')
        self.password_label.pack()

        self.password_image_path = ''
        self.password_button = tk.Button(master, text='Select Password Image', command=self.select_password_image)
        self.password_button.pack()

        self.register_button = tk.Button(master, text='Register', command=self.register)
        self.register_button.pack()

    def select_password_image(self):
        self.password_image_path = filedialog.askopenfilename(initialdir='.', title='Select Password Image', filetypes=[('Image Files', '*.png;*.jpg;*.jpeg')])
        if self.password_image_path:
            self.password_button.config(text=self.password_image_path)
    
    def register(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showerror('Error', 'Please enter a username')
            return
    
        if not self.password_image_path:
            messagebox.showerror('Error', 'Please select a password image')
            return
    
        num_segments = 4
        create_user(username, self.password_image_path, num_segments)
        messagebox.showinfo('Success', 'Registration successful')

create_table()
root = tk.Tk()

login_gui = GraphicalPasswordGUI(root)
registration_gui = GraphicalPasswordRegistrationGUI(root)
root.mainloop()