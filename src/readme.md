# **Waymark**
>Minecraft-Tracker Companion App

## 📖 Table of Contents
- [**Waymark**](#waymark)
  - [📖 Table of Contents](#-table-of-contents)
  - [🧐 About the Project](#-about-the-project)
  - [✨ Features](#-features)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation using Python](#installation-using-python)
    - [Installation using .exe](#installation-using-exe)

---

## 🧐 About the Project
We’ve all been there: you finally find a Fortress or a perfect Lush Cave, and your only way of "remembering" it is a cluttered folder of F3 screenshots or a scribbled note on your desk. Waymark v5 is the end of the coordinate struggle. It’s a dedicated "Minecraft-Tracker" designed for vanilla purists who want to keep their world immersion high but their navigation organized. Think of it as your personal GPS and world-log, keeping your progress sorted so you never lose a base—or your way home—ever again.

## ✨ Features
* **World Segregation**
Keep your different adventures distinct. Waymark allows you to create separate profiles for your Survival, Hardcore, and Creative worlds. Switch between them instantly so your "End City" coordinates never get mixed up with your "Iron Farm" location from a different save.
* **Categorized Waypoints**
Don't just save numbers; save context. Tag your coordinates as Structures, Biomes, Bases, or Resources. Use custom icons to visually distinguish a Pillager Outpost from a Village at a single glance.
* **Instant "Quick-Log"**
Designed for speed. With a streamlined input system, you can alt-tab, drop your X/Y/Z, and be back in the game in under three seconds. No more pausing the action to fumble with a notepad or a messy text file.
* **Global Search & Filter**
Lost your "Mending Librarian" in a sea of coordinates? Use the instant search bar to filter by name or category. Whether you have 10 waypoints or 1,000, finding home is always just a few keystrokes away.
* **Portable Data Management**
Your data stays yours. Waymark uses a lightweight, local JSON storage system. It's easy to back up, easy to share with friends on a server, and requires zero cloud accounts or internet connection to function.
* **Responsive Design:** Waymark v5 is built with a fluid-grid architecture that treats your screen real estate like a dynamic inventory system. Instead of static windows that get cut off, the layout intelligently "stacks" and "scales" based on how you’re using it.
* **Cross-Platform:** This uses python and flet, as long as you can run python 3.13.+ it should work

## 🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.

---
### Prerequisites
List the software or tools needed:
* Python 3.13.+
* Package manager (pip)
* For setup exe (Windows 10 - 11)

### Installation using Python
1. **Clone the repository:**
```
   git clone https://github.com/xyelaurel0714/Waymark

   cd /path/to/waymark

   cd src/
```

2. **Create python environment**
```bash
python -m venv <your_env_name>

call <your_env_name>\Scripts\activate

```
3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run python script**
```bash
python waymark_v5.py
```

### Installation using .exe

Just run the **"Waymark_setup_v5.2.exe"** and the installation wizard will guide you

---