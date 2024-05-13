import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import json
import xml.etree.ElementTree as ET
import csv
from functools import partial

class KryptoM3UReader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.channels = []
        self.countries = set()
        self.m3u_files = []
        self.init_ui()

    def open_file_dialog(self):
        file_paths = filedialog.askopenfilenames(title="Select M3U Files", filetypes=(("M3U files", "*.m3u"), ("All files", "*.*")))
        if file_paths:
            self.m3u_files.extend(file_paths)
            self.process_files()

    def process_files(self):
        for m3u_path in self.m3u_files:
            try:
                with open(m3u_path, 'r', encoding='utf-8') as file:
                    content = file.readlines()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")
                return
    
            capturing_url = False  # Flag to indicate the next line is the channel URL
            for line in content:
                line = line.strip()
                if capturing_url:  # If the flag is set, the current line is the URL
                    channel["url"] = line
                    capturing_url = False  # Reset the flag
                    self.channels.append(channel)  # Now append the channel as it includes the URL
                    continue
    
                if line.startswith("#EXTINF:-1"):
                    channel = {}
                    for prop in re.findall(r'(tvg-name|tvg-logo|tvg-id|group-title)="([^"]*)"', line):
                        channel[prop[0]] = prop[1].strip()
    
                    name_match = re.search(r',([^,]+)$', line)
                    if name_match:
                        channel["name"] = name_match.group(1).strip()
                        country_match = re.search(r'\b[A-Z]{2}\b', channel["name"])
                        if country_match:
                            channel["country"] = country_match.group().strip()
                            self.countries.add(channel["country"])
                        else:
                            channel["country"] = "Unknown"
                        # Don't append the channel here since the URL is on the next line
                        capturing_url = True  # Set the flag to capture the URL on the next line
    
        self.display_channels()


    def display_channels(self):
        self.text_box.delete('1.0', tk.END)
        for channel in self.channels:
            self.text_box.insert(tk.END, f"Name: {channel.get('name', '')}\nURL: {channel.get('url', '')}\nCountry: {channel.get('country', 'Unknown')}\nGroup-title: {channel.get('group-title', 'Unknown')}\n\n")

    def filter_channels(self):
        filter_type = self.filter_type_combobox.get()
        filtered_channels = [channel for channel in self.channels if channel.get(filter_type.lower(), '').lower() == self.search_entry.get().lower()]

        self.text_box.delete('1.0', tk.END)
        for channel in filtered_channels:
            self.text_box.insert(tk.END, f"Name: {channel.get('name', '')}\nURL: {channel.get('url', '')}\nCountry: {channel.get('country', 'Unknown')}\nGroup-title: {channel.get('group-title', 'Unknown')}\n\n")

    def sort_channels(self, sort_key):
        if sort_key not in ['name', 'country']:
            return

        self.channels.sort(key=lambda x: x.get(sort_key, '').lower())
        self.display_channels()

    def save_to_file(self, file_format):
        save_path = filedialog.asksaveasfilename(defaultextension=f".{file_format}", filetypes=((f"{file_format.upper()} files", f"*.{file_format}"), ("All files", "*.*")))
        if not save_path:
            return

        channels_by_group = {}
        for channel in self.channels:
            group = channel.get('group-title', 'Generic')
            if group not in channels_by_group:
                channels_by_group[group] = []
            channels_by_group[group].append(channel)

        if file_format == "json":
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(channels_by_group, file, indent=4)
        elif file_format == "xml":
            root = ET.Element("channelsByGroup")
            for group, channels in channels_by_group.items():
                group_elem = ET.SubElement(root, "group", name=group)
                for channel in channels:
                    channel_elem = ET.SubElement(group_elem, "channel")
                    for key, value in channel.items():
                        sub_elem = ET.SubElement(channel_elem, key)
                        sub_elem.text = value
            tree = ET.ElementTree(root)
            tree.write(save_path)
        elif file_format == "csv":
            with open(save_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["name", "url", "country", "group-title", "tvg-name", "tvg-logo", "tvg-id"])
                writer.writeheader()
                for channels in channels_by_group.values():
                    for channel in channels:
                        writer.writerow(channel)
        elif file_format == "py":
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write("channels_by_group = {\n")
                for group, channels in channels_by_group.items():
                    file.write(f"    '{group}': [\n")
                    for channel in channels:
                        file.write(f"        {channel},\n")
                    file.write("    ],\n")
                file.write("}\n")

        messagebox.showinfo("Saved", f"Channels saved to {file_format.upper()} file successfully.")

    def init_ui(self):
        self.title("Krypto IPTV M3UReader + File Saver")
        self.geometry("800x600")

        # Setup the frame for the Open File button
        open_file_frame = ttk.Frame(self)
        open_file_frame.pack(pady=10, fill=tk.X)
        self.load_button = ttk.Button(open_file_frame, text="Open M3U File", command=self.open_file_dialog)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # Setup the frame for search and filter options
        search_filter_frame = ttk.Frame(self)
        search_filter_frame.pack(pady=10, fill=tk.X)
        self.search_entry = ttk.Entry(search_filter_frame)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.filter_type_combobox = ttk.Combobox(search_filter_frame, values=["name", "country", "group-title"], state="readonly")
        self.filter_type_combobox.set("name")
        self.filter_type_combobox.pack(side=tk.LEFT, padx=5)
        self.filter_button = ttk.Button(search_filter_frame, text="Filter", command=self.filter_channels)
        self.filter_button.pack(side=tk.LEFT, padx=5)

        # Setup the frame for sorting and saving options
        sort_save_frame = ttk.Frame(self)
        sort_save_frame.pack(pady=5, fill=tk.X)
        self.save_json_button = ttk.Button(sort_save_frame, text="Save to JSON", command=lambda: self.save_to_file("json"))
        self.save_json_button.pack(side=tk.LEFT, padx=5)
        self.save_xml_button = ttk.Button(sort_save_frame, text="Save to XML", command=lambda: self.save_to_file("xml"))
        self.save_xml_button.pack(side=tk.LEFT, padx=5)
        self.save_csv_button = ttk.Button(sort_save_frame, text="Save to CSV", command=lambda: self.save_to_file("csv"))
        self.save_csv_button.pack(side=tk.LEFT, padx=5)
        self.save_python_button = ttk.Button(sort_save_frame, text="Save to Python", command=lambda: self.save_to_file("py"))
        self.save_python_button.pack(side=tk.LEFT, padx=5)

        # ScrolledText widget for displaying channels information
        self.text_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

if __name__ == "__main__":
    app = KryptoM3UReader()
    app.mainloop()
