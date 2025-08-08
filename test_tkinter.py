#!/usr/bin/env python3
"""
Simple test to verify tkinter is working
"""

import tkinter as tk
from tkinter import ttk

def test_gui():
    print("Creating tkinter window...")
    root = tk.Tk()
    root.title("AAR System - Test Window")
    root.geometry("400x300")
    
    # Add a simple label
    label = tk.Label(root, text="AAR System Test Window", font=("Arial", 16))
    label.pack(pady=50)
    
    # Add a button
    button = tk.Button(root, text="Click Me!", command=lambda: print("Button clicked!"))
    button.pack(pady=20)
    
    print("Starting tkinter mainloop...")
    root.mainloop()
    print("GUI closed.")

if __name__ == "__main__":
    test_gui()
