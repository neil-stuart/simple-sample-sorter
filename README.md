# Simple Sample Sorter 🎵🗂️

Enhancing the efficiency of sorting music samples with a swift and user-friendly terminal-based file explorer. 

## Objective 🎯

Develop a terminal-based file explorer using Python's `curses` to expedite the sorting of music samples into a structured file hierarchy. This tool aims to significantly streamline the process, making it quicker and more intuitive for users to manage their music samples.

### Planned Features 🛠️
- **Tab-Switching** 🔄: Seamlessly switch between the new virtual hierarchy and the filesystem for efficient navigation.
- **Flagging Files** 🚩: Mark files from various directories to move them simultaneously. Selection of the sample's category will be facilitated through an interactive up/down arrow interface.
- **Global Settings** ⚙️: Customize settings such as all-caps filenames, general file name format, and an option to prompt for the pack name.
- **Hierarchy Management** 📁: Capability to reload previous hierarchies for ongoing projects.
- **Startup Tutorial** 📚: An introductory guide on startup to familiarize users with the tool's functionality.

## Current Progress 🚧

The project is under active development, with several key functionalities already implemented. We are working diligently to integrate the planned features to realize the full vision of the Simple Sample Sorter.

### Source Directory Structure 📂
```
└───src
│ dcs.py # File decorator constants 
│ file_util.py # File utilities for operations
│ main.py # Main application entry point
│ names.py # Labels for prompts and application constants
│ panes.py # Pane management for UI
│ test.py # Testing utilities
│ widgets.py # UI widgets for enhanced interaction
│ w_id.py # Widget identification and management
```
This structure is designed to keep the codebase organized and modular, facilitating easy updates and feature additions.

### How to Contribute 🤝

Contributions are welcome! Whether it's through suggesting new features, improving the code, or reporting bugs, every bit of help counts. Feel free to fork the repository and submit your pull requests.

