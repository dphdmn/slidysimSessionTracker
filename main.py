import math
import os
import subprocess
import tkinter as tk
import pyperclip
import sqlite3
import time
import json
import base64
import zlib
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.dialogs.dialogs import Messagebox, Querybox
from ttkbootstrap import Scrollbar
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.tableview import Tableview
from datetime import datetime
from datetime import timedelta
import webbrowser
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from PIL import Image, ImageTk, ImageDraw, ImageFont
import configparser
from tktimepicker import SpinTimePickerModern
import locale
from cairosvg import svg2png
import shutil

# pyinstaller -F --clean --noconsole --icon=icon.ico main.py

DESCENDING_SORTING_TK = 1
FIRST_COLUMN_ID = 0
LENGTH_LIMIT_LINK = 5300
CONFIG_FILE_NAME = "sessionTrackerResources/sessionTracker.cfg"
ERROR_NON_CONSECUTIVE = "Unable to calculate average.\nReason: non-consecutive solves are selected.\nPease sort by SID and make sure to use 'Include skipped/failed solves' mode.\n"
WARNING_MIXED_SOLVES = "Warning: you have selected mixed solves, be careful using results of this export.\n"
DB_WAS_NOT_FOUND_ERROR_1 = "Slidysim DB was not found, please specify the different path.\nYou can also instead run script from slidysim folder\nApp will remember path if it is correct\nYou can always change it in config file manually"
DB_WAS_NOT_FOUND_ERROR_2 = "Critical error. Slidysim DB file was not found despite all my effort to prevent that.\nMaybe it was deleted? (Not my fault) \nExiting."
DB_ERROR_FETCHING_1 = "Critical error when fetching categories from database. \nExiting."
DB_ERROR_FETCHING_2 = "Critical error when fetching latest solve. \nExiting."
DB_ERROR_FETCHING_3 = "Critical error when fetching first solve. \nExiting."
DB_ERROR_FETCHING_4 = "Critical error when fetching Solves by categories. \nExiting."
DB_ERROR_FETCHING_5 = "Critical error when fetching Single solves. \nExiting."
DB_ERROR_FETCHING_6 = "Critical error when fetching Single solves as Main. \nExiting."
ENTER_SLIDYSIM_PATH_REQUEST = "Enter Slidysim folder path\n(press Cancel to close the App)"
MY_WINDOW_WIDTH = 1600
MY_WINDOW_HEIGHT = 900
MY_APP_TITLE = "Slidysim Session Tracker v2.0.0 beta"
SLIDYSIM_DEFAULT_PATH = ""
TABLE_SEPARATOR = ";"
singleHeaders = ["Parent", "Puzzle", "Completed", "Time", "Moves", "TPS", "Scramble", "Solution", "Movetimes",
                 "Reconstruction"]

tableColumnsMapping = {
    "Time": "time",
    "Moves": "moves",
    "TPS": "tps",
    "Display type": "display_type",
    "Size": "puzzle",
    "Controls": "controls",
    "Date": "date",
    "Completed": "fullyCompleted",
    "Solve Type": "solve_type",
    "BLD memo": "BLD memo",
    "SID": "SID"
}

# #SHORT VERSION (NOT CURRENTLY USING)
# display_type_options = {
#     "Standard": "",
#     "Minimal": "Min",
#     "Row minimal": "RowMin",
#     "Fringe minimal": "FringeMin",
#     "Inverse permutation": "InvPerm",
#     "Manhattan": "Manhattan",
#     "Vectors": "Vecs",
#     "Incremental vectors": "IncrVecs",
#     "Inverse vectors": "InvVecs",
#     "RGB": "RGB",
#     "Chess": "Chess",
#     "Adjacent tiles": "AdjTiles",
#     "Adjacent sum": "AdjSum",
#     "Last move": "LastMove",
#     "Fading tiles": "FadeTiles",
#     "Vanish on solved": "VanishSolved",
#     "Minesweeper": "Minesweeper",
#     "Minimal unsolved": "MinUnsolved",
#     "Maximal unsolved": "MaxUnsolved",
#     "Rows and columns": "RowsCols"
# }

display_type_options = {
    "Standard": "",
    "Minimal": "Minimal",
    "Row minimal": "Row minimal",
    "Fringe minimal": "Fringe minimal",
    "Inverse permutation": "Inverse permutation",
    "Manhattan": "Manhattan",
    "Vectors": "Vectors",
    "Incremental vectors": "Incremental vectors",
    "Inverse vectors": "Inverse vectors",
    "RGB": "RGB",
    "Chess": "Chess",
    "Adjacent tiles": "Adjacent tiles",
    "Adjacent sum": "Adjacent sum",
    "Last move": "Last move",
    "Fading tiles": "Fading tiles",
    "Vanish on solved": "Vanish on solved",
    "Minesweeper": "Minesweeper",
    "Minimal unsolved": "Minimal unsolved",
    "Maximal unsolved": "Maximal unsolved",
    "Rows and columns": "Rows and columns"
}

solve_type_options = {
    "Standard": "Single",
    "2-N relay": "Relay",
    "Height relay": "H-Relay",
    "Width relay": "W-Relay",
    "Everything-up-to relay": "EUT-Relay",
    "Marathon": "Marathon",
    "BLD": "BLD"
}

controls_options = {
    "Mouse": "[M]",
    "Keyboard": "[K]"
}

CATEGORY_CHECKBOX_MAPPING = {
    "displayType": "checkboxes_display",
    "solveType": "checkboxes_solve",
    "puzzleSize": "checkboxes_puzzles",
    "controlType": "checkboxes_controls"
}

DIFS_MAP_HISTOGRAM = {
    (0, 5): 0.1,
    (5, 15): 0.5,
    (15, 60): 1,
    (60, 120): 2,
    (120, 400): 5,
    (400, 1000): 10,
    (1000, 2000): 20,
    (2000, 5000): 50,
    (5000, 10000): 100
}


def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME)
    return config


def update_config(section, option, value):
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section][option] = value
    with open(CONFIG_FILE_NAME, 'w') as configfile:
        config.write(configfile)


def drawErrorImage(width):
    height = int(width * 0.6)
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    text = "No valid data points of less than 10000"
    font = ImageFont.load_default(32)
    text_width = draw.textlength(text, font=font)
    text_height = font.getbbox(text)[3] - font.getbbox(text)[1]
    text_position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(text_position, text, fill='black', font=font)
    return img


def getBinEdges(data):
    average_value = sum(data) / len(data)
    bin_width = None
    for (start, end), diff in DIFS_MAP_HISTOGRAM.items():
        if start <= average_value < end:
            bin_width = diff
            break
    if bin_width is None:
        bin_width = 1000
    min_value = round(min(data) // bin_width * bin_width, 1)
    max_value = max(data)
    num_bins = int((max_value - min_value) / bin_width) + 1
    bin_edges = [round(min_value + i * bin_width, 1) for i in range(num_bins + 1)]
    length = len(bin_edges)
    if length > 50:
        bin_edges = bin_edges[::2]
    if length > 100:
        bin_edges = bin_edges[::5]
    if length > 200:
        bin_edges = bin_edges[::10]
    return bin_edges


def plotToImage(fig, max_width):
    img = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba())
    width_percent = max_width / float(img.size[0])
    height_size = int(float(img.size[1]) * float(width_percent))
    img = img.resize((max_width, height_size))
    return img


def plotData(data, title, max_width):
    data = [x for x in data if x <= 10000]
    if len(data) == 0:
        return drawErrorImage(max_width)
    bin_edges = getBinEdges(data)
    plt.style.use('dark_background')
    plt.rcParams['axes.facecolor'] = '#222222'
    plt.rcParams['figure.facecolor'] = '#222222'
    plt.rcParams['grid.color'] = 'green'
    plt.rcParams['xtick.color'] = '#00FFFF'
    plt.rcParams['ytick.color'] = '#00FFFF'
    figsize = (max_width / 100, 0.6 * (max_width / 100))
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(data, bins=bin_edges, color='green', width=0.8 * (bin_edges[1] - bin_edges[0]))
    ax.set_title(title, color='#00FFFF')
    ax.grid(True)
    ax.tick_params(axis='x', which='major', labelsize=9, rotation=90)
    ax.set_xticks(bin_edges)
    ax.set_xticklabels(bin_edges, fontsize=9, rotation=90)
    ax.tick_params(axis='y', which='major', labelsize=9)
    for i, patch in enumerate(ax.patches):
        ax.text(patch.get_x() + patch.get_width() / 2, patch.get_height() * 1,
                str(len([x for x in data if bin_edges[i] <= x < bin_edges[i + 1]])), ha='center', va='bottom',
                color='white', fontsize=8, fontweight='bold')
    fig.canvas.draw()
    img = plotToImage(fig, max_width)
    plt.close()
    return img


def plotDataWithLabels(data, data_labels, title, max_width):
    plt.style.use('dark_background')
    plt.rcParams['axes.facecolor'] = '#222222'
    plt.rcParams['figure.facecolor'] = '#222222'
    plt.rcParams['grid.color'] = 'green'
    plt.rcParams['xtick.color'] = '#00FFFF'
    plt.rcParams['ytick.color'] = '#00FFFF'
    figsize = (max_width / 100, 0.6 * (max_width / 100))
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(data_labels, data, color='green')
    ax.set_title(title, color='#00FFFF')  # Cyan color for title
    ax.grid(True)
    ax.tick_params(axis='x', which='major', labelsize=9, rotation=90, colors='#00FFFF')
    ax.tick_params(axis='y', which='major', labelsize=9, colors='#00FFFF')
    offset = 0.02 * max(ax.get_ylim())
    for i, value in enumerate(data):
        if i % 2 == 0:
            ax.text(i, value - offset - offset / 2, str(value), ha='center', va='bottom', color='white', fontsize=7,
                    fontweight='bold')
        else:
            ax.text(i, value + offset - offset / 2, str(value), ha='center', va='bottom', color='white', fontsize=7,
                    fontweight='bold')

    fig.canvas.draw()
    img = plotToImage(fig, max_width)
    plt.close()
    return img


def renderGraphImage(imageLabel, data, histogram, iteration=0, data_labels=None):
    iteration = iteration % 3
    max_width = int(MY_WINDOW_WIDTH / 2.7)
    title = ["Time", "Moves", "TPS"][iteration]
    if histogram:
        title = title + " distribution"
        graphImage = plotData(data[iteration], title, max_width=max_width)
    else:
        data_labels = [] if data_labels is None else data_labels
        title = title + " per puzzle in relay"
        graphImage = plotDataWithLabels(data[iteration], data_labels, title, max_width=max_width)
    imgobj = ImageTk.PhotoImage(graphImage)
    imageLabel.configure(image=imgobj)
    imageLabel.image = imgobj
    imageLabel.configure(cursor='hand2')
    imageLabel.bind('<ButtonRelease-1>', lambda event: renderGraphImage(imageLabel,
                                                                        data,
                                                                        histogram,
                                                                        iteration=iteration + 1,
                                                                        data_labels=data_labels))


def renderPuzzleImage(scramble, imageLabel, reconstructionLink, iLoveEgg=False):
    if iLoveEgg:
        file = 'sessionTrackerResources/i_love_egg.png'
        imageLabel.configure(cursor='arrow')
        imageLabel.bind('<ButtonRelease-1>',
                        lambda event: toastUpdate("I love Egg!\n(Clicking Egg does nothing, do solves already"))
    else:
        try:
            file = 'scramble_tmp.png'
            command = [
                "slidy",
                "render",
                "--output",
                "img_tmp.svg",
                scramble
            ]
            subprocess.run(command)
            with open("img_tmp.svg", 'r') as mysvg:
                svg2png(output_height=int(MY_WINDOW_HEIGHT / 2.5), output_width=int(MY_WINDOW_WIDTH / 2.7),
                        bytestring=mysvg.read(), write_to=file)
        except FileNotFoundError:
            Messagebox.show_error(
                "Slidy-cli was not found, please put it in the folder of the script and call 'slidy' (slidy.exe)\nYou can download it from github at https://github.com/benwh1/slidy-cli/releases/tag/v0.2.0")
            exit()
        if reconstructionLink:
            imageLabel.configure(cursor='hand2')

            def _open_link(event):
                try:
                    webbrowser.open(reconstructionLink)
                except ValueError as e:
                    if "startfile: filepath too long" in str(e).lower():
                        import pyperclip
                        pyperclip.copy(reconstructionLink)
                        toast = ToastNotification(
                            title="Link is too long to open.",
                            message="It has been copied to your clipboard!",
                            duration=2000,
                            bootstyle="warning",
                            icon="🥚",
                            position=(500, 500, 'se')
                        )
                        toast.show_toast()
                    else:
                        raise

            imageLabel.bind('<ButtonRelease-1>', _open_link)
        else:
            imageLabel.unbind('<ButtonRelease-1>')
            imageLabel.configure(cursor='arrow')
    imgobj = tk.PhotoImage(file=file)
    imageLabel.configure(image=imgobj)
    imageLabel.image = imgobj


def toastUpdate(message):
    toast = ToastNotification(
        title=MY_APP_TITLE,
        message=message,
        duration=2000,
        bootstyle="primary",
        icon="🥚",
        position=(50, 50, 'se')
    )
    toast.show_toast()


def duration(time1, time2):
    start_time = datetime.utcfromtimestamp(time1 / 1000)
    end_time = datetime.utcfromtimestamp(time2 / 1000)
    duration = end_time - start_time
    return format_duration(duration)


def format_duration(duration):
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_duration = ""
    if days:
        formatted_duration += "{:d}d ".format(days)
    if hours:
        formatted_duration += "{:d}h ".format(hours)
    if minutes:
        formatted_duration += "{:d}m ".format(minutes)
    formatted_duration += "{:d}s".format(seconds)

    return formatted_duration.strip()


def convert_unix_timestamp_ms(timestamp_ms):
    timestamp_sec = timestamp_ms / 1000.0
    dt_object = datetime.fromtimestamp(timestamp_sec)
    formatted_datetime = dt_object.strftime('%Y.%m.%d %H:%M:%S')
    return formatted_datetime


def createSolvesFrameUI(frame):
    cbframe = ttk.Frame(frame, bootstyle="black")
    cbframe.pack(fill=tk.X)
    include_checkbox = ttk.Checkbutton(cbframe, text="Include skipped/failed solves", bootstyle="info")
    include_checkbox.pack(ipady=10, padx=10, side="left")
    fake_singles_checkbox = ttk.Checkbutton(cbframe, text="Singles from ALL solve types", bootstyle="info")
    fake_singles_checkbox.pack(ipady=10, padx=10, side="left")
    includeStatsTableCheckbox = ttk.Checkbutton(cbframe, text="Detailed info on bulk selection", bootstyle="info")
    includeStatsTableCheckbox.pack(ipady=10, padx=10, side="left")
    dt = Tableview(
        master=frame,
        searchable=True,
        bootstyle="info",
        paginated=False,
        autoalign=False,
        autofit=True,
        height=10,
        delimiter=";"
    )
    yscrollbar = Scrollbar(frame, orient="vertical", bootstyle="info", command=dt.view.yview)
    yscrollbar.pack(expand=False, fill=Y, side="right")
    dt.pack(fill=BOTH, side="left", expand=YES, padx=10, pady=10)
    dt.configure(yscrollcommand=yscrollbar.set)
    dt.view.tag_configure("Skipped", background='#2E0505', foreground='#FF6666')
    dt.view.tag_configure("Incomplete", background='#331A00', foreground='#FF9933')
    dt.view.tag_configure("OK", background='#004D26', foreground='#66FF99')
    dt.view.tag_configure("Single", background='#666600', foreground='#FFFF00')
    dt.view.bind("<Control-a>", lambda event: [dt.view.selection_add(item) for item in dt.view.get_children()])

    return {"solvesTable": dt,
            "include_checkbox": include_checkbox,
            'fakeSingles_checkbox': fake_singles_checkbox,
            'includeStatsTableCheckbox': includeStatsTableCheckbox}


def getCategoryStringSimple(categoryDict):
    size = categoryDict["puzzleSize"]
    dispalyType = display_type_options.get(categoryDict['displayType'], "Error")
    solveType = solve_type_options.get(categoryDict['solveType'], "Marathon")
    controls = controls_options.get(categoryDict['controlType'], "Error")
    if solveType == "Marathon":
        solveType = categoryDict['solveType'].split()[0]
    return " ".join(filter(None, [controls, dispalyType, size, solveType]))


def getCategoryString(categoryDict):
    size = f"{categoryDict['width']}x{categoryDict['height']}"
    dispalyType = display_type_options.get(categoryDict['display_type'], "Error")
    solveType = solve_type_options.get(categoryDict['solve_type'], "Error")
    controls = controls_options.get(categoryDict['controls'], "Error")
    if solveType == "Marathon":
        solveType = f"x{categoryDict['marathon_length']}"
    return " ".join(filter(None, [controls, dispalyType, size, solveType]))


def updateLimitCheckboxesUI(controller, frames, limits, oldFilters=None):
    for frame in frames.values():
        for widget in frame.winfo_children():
            widget.destroy()
    sf_display = frames["sf_display"]
    sf_solve = frames["sf_solve"]
    sf_puzzles = frames["sf_puzzles"]
    sf_controls = frames["sf_controls"]
    sf_presets = frames["sf_presets"]
    display_data = limits["display_types"]
    solve_data = limits["solve_types"]
    puzzles_data = limits["puzzle_sizes"]
    controls_data = limits["control_types"]
    combined_data = limits["combined"]
    categories = []
    for categoryDict in combined_data:
        categoryString = getCategoryString(categoryDict)
        categories.append(categoryString)

    def create_checkboxes_with_title(scroll_frame, data, title, old_filters=None, presets=False):
        frame = ttk.Frame(scroll_frame)
        if presets:
            titleLabel = ttk.Label(frame, text=title, style="info")
            titleLabel.pack(anchor=tk.CENTER)
        else:
            titleLabel = ttk.Label(frame, text=title, style="light")
            titleLabel.pack(anchor=tk.W, padx=5)
        frame.pack(side=tk.TOP, fill=tk.X)
        checkboxes = {}
        if presets and data:
            data.append("ALL (may be laggy!)")
        for index, item in enumerate(data):
            var = tk.BooleanVar()
            if old_filters and item in old_filters:
                var.set(True)
            var.trace("w", lambda *args: checkboxes[item].get())
            if presets:
                chk = tk.Checkbutton(frame, text=item, variable=var,
                                     command=lambda item=item: controller.updateByPresets(item))
            else:
                chk = tk.Checkbutton(frame, text=item, variable=var, command=controller.updateByCheckBoxes)
            chk.pack(anchor=tk.W)
            checkboxes[item] = var
            if item == "ALL (may be laggy!)":
                chk.config(foreground="yellow")
        return checkboxes

    checkboxes_display = create_checkboxes_with_title(sf_display, display_data, "Display Types",
                                                      oldFilters['checkboxes_display'] if oldFilters else None)
    checkboxes_solve = create_checkboxes_with_title(sf_solve, solve_data, "Solve Types",
                                                    oldFilters['checkboxes_solve'] if oldFilters else None)
    checkboxes_puzzles = create_checkboxes_with_title(sf_puzzles, puzzles_data, "Puzzles",
                                                      oldFilters['checkboxes_puzzles'] if oldFilters else None)
    checkboxes_controls = create_checkboxes_with_title(sf_controls, controls_data, "Controls",
                                                       oldFilters['checkboxes_controls'] if oldFilters else None)
    checkboxes_presets = create_checkboxes_with_title(sf_presets, categories, "Presets",
                                                      oldFilters['checkboxes_presets'] if oldFilters else None,
                                                      presets=True)

    return {"checkboxes_display": checkboxes_display,
            "checkboxes_solve": checkboxes_solve,
            "checkboxes_puzzles": checkboxes_puzzles,
            "checkboxes_controls": checkboxes_controls,
            "checkboxes_presets": checkboxes_presets,
            "presets_data": combined_data}


def replaceText(textbox, newtext, bad=False):
    textbox["state"] = 'normal'
    textbox.delete(1.0, tk.END)
    textbox.insert(tk.END, newtext)
    if bad:
        textbox.configure(background='#222222', foreground='#CC0000')
    else:
        textbox.configure(background='#222222', foreground='#00CC00')
    textbox["state"] = 'disabled'


def createGraphsFrameUI(frame):
    singleSolvesInfoContainer = ttk.Frame(frame, bootstyle="darkly")
    graphContainer = ttk.Frame(frame, bootstyle="darkly")
    singleSolvesInfoContainer.pack(side=tk.RIGHT, expand=False, fill=Y)
    textBoxLabel = tk.Label(master=singleSolvesInfoContainer,
                            text="It's solves data (sometimes is readable) it's in your buffer!")
    textBoxLabel.config(borderwidth=2, relief="groove", highlightthickness=2)
    textBoxLabel.pack(side=tk.TOP, fill=tk.BOTH, ipadx=10, ipady=2, expand=False, anchor="center", )
    textbox = ttk.Text(master=singleSolvesInfoContainer)
    textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    textbox.configure(width=int(MY_WINDOW_WIDTH / 28))
    graphContainer.pack(side=tk.LEFT, fill=BOTH, expand=True, padx=10)
    graphLabel = tk.Label(master=graphContainer, text="It's place for a graph / puzzle Image (Try clicking it)!")
    graphLabel.config(borderwidth=2, relief="groove", highlightthickness=2)
    graphLabel.pack(side=tk.TOP, fill=tk.BOTH, ipadx=10, ipady=2, expand=False, anchor="center")
    yscrollbar = Scrollbar(singleSolvesInfoContainer, orient="vertical", bootstyle="info", command=textbox.yview)
    yscrollbar.pack(expand=False, fill=Y, side=tk.RIGHT)
    textbox.configure(yscrollcommand=yscrollbar.set)
    textbox["state"] = 'disabled'
    imageLabel = tk.Label(master=graphContainer)
    imageLabel.pack(side=tk.TOP, pady=5)
    return {"textbox": textbox,
            "imageLabel": imageLabel}


def createCategoryLimiterFrameUI(frame):
    sf_presets = ScrolledFrame(frame, bootstyle="info", width=int(MY_WINDOW_WIDTH * 0.2))
    sf_display = ScrolledFrame(frame, width=int(MY_WINDOW_WIDTH * 0.1))
    sf_solve = ScrolledFrame(frame, width=int(MY_WINDOW_WIDTH * 0.1))
    sf_puzzles = ScrolledFrame(frame, width=int(MY_WINDOW_WIDTH * 0.1))
    sf_controls = ScrolledFrame(frame, width=int(MY_WINDOW_WIDTH * 0.1))

    sf_presets.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)
    sf_display.pack(side=tk.LEFT, fill=tk.BOTH)
    sf_solve.pack(side=tk.LEFT, fill=tk.BOTH)
    sf_puzzles.pack(side=tk.LEFT, fill=tk.BOTH)
    sf_controls.pack(side=tk.LEFT, fill=tk.BOTH)

    return {"sf_display": sf_display,
            "sf_solve": sf_solve,
            "sf_puzzles": sf_puzzles,
            "sf_controls": sf_controls,
            "sf_presets": sf_presets}


def copy_tree_to_clipboard(event, tree):
    item_ids = tree.get_children()
    rows = ""
    for item_id in item_ids:
        values = tree.item(item_id, 'values')
        rows += '\t'.join(values) + "\n"
    pyperclip.copy(rows)
    toastUpdate("Generic session stats All copied to clipboard!")


def setTimeSelected(unixtimestampMs, dateEntry, timeEntry):
    dt_obj = datetime.fromtimestamp(unixtimestampMs / 1000)
    dateEntry.set(dt_obj.strftime("%d.%m.%y"))
    timeEntry.set24Hrs(dt_obj.hour)
    timeEntry.setMins(dt_obj.minute)


def setAllDatePickers(datePickerElements, firstTimestampMS, secondTimestampMS):
    setTimeSelected(firstTimestampMS, datePickerElements.get('dateEntryFrom'), datePickerElements.get('timeEntryFrom'))
    setTimeSelected(secondTimestampMS, datePickerElements.get('dateEntryTo'), datePickerElements.get('timeEntryTo'))


def getTimeSelected(dateEntry, timeEntry):
    dateString = dateEntry.get()
    timeH, timeM, _ = timeEntry.time()
    selected_datetime = datetime.strptime(dateString, '%d.%m.%y').replace(hour=timeH, minute=timeM)
    return int(selected_datetime.timestamp() * 1000)


def getPickedTimestamps(datePickerElements):
    first = getTimeSelected(datePickerElements.get('dateEntryFrom'), datePickerElements.get('timeEntryFrom'))
    second = getTimeSelected(datePickerElements.get('dateEntryTo'), datePickerElements.get('timeEntryTo'))
    return first, second


def createSessionControlFrameUI(frame, dbpath):
    buttonsContainer = ttk.Frame(frame, bootstyle="darkly", padding=10)
    buttonsContainer.pack(side=tk.LEFT, padx=10, pady=5)

    labelConnected = ttk.Label(buttonsContainer, text=f"Connected successfully to\n{dbpath}", bootstyle='success')
    labelConnected.pack()
    progress = tk.IntVar()
    updateProgressBar = ttk.Progressbar(buttonsContainer, bootstyle="success-striped", variable=progress)
    updateProgressBar.pack(side=tk.TOP, fill=BOTH, padx=10, pady=10)
    dateEntryContainer = ttk.Frame(buttonsContainer, bootstyle="darkly")
    dateEntryContainerTwo = ttk.Frame(buttonsContainer, bootstyle="darkly")
    dateFromVar = ttk.StringVar()
    dateToVar = ttk.StringVar()
    dateEntryFromLabel = ttk.Label(master=dateEntryContainer, bootstyle="info", text="From", width=5)
    dateEntryFromLabel.pack(side=tk.LEFT, fill=BOTH)
    dateEntryFrom = ttk.DateEntry(master=dateEntryContainer, bootstyle="darkly", firstweekday=0, width=10,
                                  dateformat="%d.%m.%y")
    dateEntryFrom.entry.configure(textvariable=dateFromVar)
    dateEntryToLabel = ttk.Label(master=dateEntryContainerTwo, bootstyle="info", text="To", width=5)
    dateEntryToLabel.pack(side=tk.LEFT, fill=BOTH)
    dateEntryTo = ttk.DateEntry(master=dateEntryContainerTwo, bootstyle="darkly", firstweekday=0, width=10,
                                dateformat="%d.%m.%y")
    dateEntryTo.entry.configure(textvariable=dateToVar)
    dateFromVar.set("12.04.23")
    dateToVar.set("12.05.23")
    timeEntryFrom = SpinTimePickerModern(dateEntryContainer)
    timeEntryFrom.addAll(1)
    options = {
        "background": "#333333",
        "foreground": "#ffffff",
        "hovercolor": "#ffffff",
        "hoverbg": "#555555",
        "clickedcolor": "#ffffff",
        "clickedbg": "#555555",
        "width": 5
    }
    timeEntryFrom.configureAll(**options)
    timeEntryFrom.configure_separator(**{"background": "#333333"})

    timeEntryTo = SpinTimePickerModern(dateEntryContainerTwo)
    timeEntryTo.addAll(1)
    timeEntryTo.configureAll(**options)
    timeEntryTo.configure_separator(**{"background": "#333333"})

    updateButton = ttk.Button(buttonsContainer, bootstyle="info", text="Update", width=40)

    setToLatestVar = tk.BooleanVar()
    setToLatestVar.set(True)
    setToLatestVar.trace("w", lambda *args: setToLatestVar.get())
    setToLatestVarCB = tk.Checkbutton(buttonsContainer, text="Preset by latest Solve", variable=setToLatestVar)

    autoUpdateVar = tk.BooleanVar()
    autoUpdateVar.set(True)
    autoUpdateVar.trace("w", lambda *args: autoUpdateVar.get())
    autoUpdateVarCB = tk.Checkbutton(buttonsContainer, text="Auto-update on focus", variable=autoUpdateVar)

    updateButton.pack(side=tk.TOP, padx=10, pady=5)
    dateEntryContainer.pack(fill=tk.BOTH, pady=5)
    dateEntryContainerTwo.pack(fill=tk.BOTH, pady=5)
    setToLatestVarCB.pack(side=tk.LEFT, fill=BOTH)
    autoUpdateVarCB.pack(side=tk.RIGHT, fill=BOTH)

    dateEntryFrom.pack(side=tk.LEFT, fill=tk.BOTH, padx=15)
    timeEntryFrom.pack(side=tk.LEFT, fill=tk.BOTH, padx=15)

    dateEntryTo.pack(side=tk.LEFT, fill=tk.BOTH, padx=15)
    timeEntryTo.pack(side=tk.LEFT, fill=tk.BOTH, padx=15)

    datePickerElements = {'dateEntryFrom': dateFromVar, 'timeEntryFrom': timeEntryFrom, 'dateEntryTo': dateToVar,
                          'timeEntryTo': timeEntryTo}
    tree = ttk.Treeview(frame, columns=("Stat", "Info"), show="headings", bootstyle='darkly')
    tree.column("Stat", anchor="e")
    tree.heading("Stat", text="Stat")
    tree.column("Info", anchor="w")
    tree.heading("Info", text="Info")
    tree.unbind("<Configure>")
    tree.tag_configure("odd", background="#1A1A1A", foreground="#00CC00")
    tree.tag_configure("even", background="#252525", foreground="#00CCCC")

    def disable_resizing(event):
        if tree.identify_region(event.x, event.y) == "separator":
            return "break"

    tree.bind("<Button-1>", disable_resizing)
    tree.bind("<ButtonRelease-1>", lambda event: copy_tree_to_clipboard(event, tree))
    tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    return {"updateButton": updateButton,
            "sessionTree": tree,
            "updateProgress": progress,
            "setToLatest": setToLatestVar,
            "autoUpdateVar": autoUpdateVar,
            "datePickerElements": datePickerElements}


def createFramesUI(root):
    left_frame = ttk.Frame(root, padding=10)
    frame1 = ttk.Frame(left_frame, padding=2, style=SECONDARY)
    frame2 = ttk.Frame(left_frame, padding=2, style=SECONDARY)
    frame3 = ttk.Frame(left_frame, padding=2, style=SECONDARY)
    frame4 = ttk.Frame(root, padding=5, style=SECONDARY)
    frame1.pack(fill=BOTH, expand=False)
    frame2.pack(fill=BOTH, expand=False)
    frame3.pack(fill=BOTH, expand=False)
    left_frame.pack(side=LEFT, fill=BOTH, expand=False)
    frame4.pack(side=LEFT, fill=BOTH, expand=True)
    return frame1, frame2, frame3, frame4


def sqlConnectCheck(path):
    if path is None:
        return False
    db_path = path + '/solves.db'
    if not os.path.exists(db_path):
        Messagebox.show_error(DB_WAS_NOT_FOUND_ERROR_1)
        return False
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        return True
    except sqlite3.Error as e:
        Messagebox.show_error(DB_WAS_NOT_FOUND_ERROR_1)
        return False


def makeDBrequest(dbpath, requestFunction, requestErrorMessage, requestData):
    if not os.path.exists(dbpath):
        Messagebox.show_error(DB_WAS_NOT_FOUND_ERROR_2)
        exit()
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    try:
        output = requestFunction(cursor, requestData)
    except sqlite3.Error as e:
        Messagebox.show_error(f"{requestErrorMessage}\nError message:\n {e}")
        exit()
    finally:
        cursor.close()
        conn.close()
    return output


def addCategoryFilters(query, params, categoryFilters):
    for group_name, group_values in categoryFilters.items():
        if group_name == 'checkboxes_display':
            query += " AND display_type IN ({})".format(','.join(['?'] * len(group_values)))
            params += tuple(group_values)
        elif group_name == 'checkboxes_solve':
            if group_values:
                query += " AND solve_type IN ('Marathon', {})".format(','.join(['?'] * len(group_values)))
                params += tuple(group_values)
                allowed_marathon_lengths = []
                for solveType in group_values:
                    if "Marathon" in solveType:
                        allowed_marathon_lengths.append(int(solveType.split()[0].replace("x", "")))
                query += " AND (marathon_length IS NULL OR marathon_length IN ({}))".format(
                    ','.join(['?'] * len(allowed_marathon_lengths)))
                params += tuple(allowed_marathon_lengths)
        elif group_name == 'checkboxes_puzzles':
            if group_values:
                puzzle_conditions = []
                for puzzle in group_values:
                    width, height = map(int, puzzle.split('x'))
                    puzzle_conditions.append("(width = ? AND height = ?)")
                    params += (width, height)
                query += " AND (" + " OR ".join(puzzle_conditions) + ")"
        elif group_name == 'checkboxes_controls':
            query += " AND controls IN ({})".format(','.join(['?'] * len(group_values)))
            params += tuple(group_values)
    return query, params


def getSingleSolves(dbpath, firstID, lastID):
    def getSingleSolvesRequest(cursor, requestData):
        firstID = requestData.get("firstID")
        lastID = requestData.get("lastID")
        query = """
            SELECT single_solves.*, GROUP_CONCAT(move_times.time) AS move_times
            FROM single_solves
            LEFT JOIN move_times ON single_solves.move_times_start_id <= move_times.id AND single_solves.move_times_end_id >= move_times.id
            WHERE single_solves.id BETWEEN ? AND ?
            GROUP BY single_solves.id
        """
        cursor.execute(query, (firstID, lastID))
        return cursor.fetchall()

    return makeDBrequest(dbpath, getSingleSolvesRequest, DB_ERROR_FETCHING_5, {
        "firstID": firstID,
        "lastID": lastID,
    })


def modify_query_output(query):
    replacements = ['timestamp', 'display_type', 'width', 'height', 'controls']
    split_query = query.split("Random permutation", 1)
    replaced_part = split_query[1]
    for replacement in replacements:
        replaced_part = replaced_part.replace(replacement, f'b.{replacement}')
    replaced_part = replaced_part.replace('b.width', 'a.width')
    replaced_part = replaced_part.replace('b.height', 'a.height')
    newquery = split_query[0] + "Random permutation" + replaced_part
    return newquery


def indexExists(cursor, index_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    return cursor.fetchone() is not None


def getSingleSolvesAsMain(dbpath, timestamp_min, timestamp_max, categoryFilters):
    def getSingleSolvesAsMainRequest(cursor, requestData):
        timestamp_min = requestData.get("timestamp_min")
        timestamp_max = requestData.get("timestamp_max")
        categoryFilters = requestData.get("categoryFilters")
        if not indexExists(cursor, 'idx_main_query'):
            cursor.execute(
                'CREATE INDEX "idx_main_query" ON "solves" ("scrambler", "timestamp", "display_type", "width", "height", "controls");')
        if any(not sublist for key, sublist in categoryFilters.items() if key != 'checkboxes_presets'):
            return []
        query = f"select NULL, a.id, a.id, a.width, a.height, b.memo_time, a.time, a.moves, a.tps, 'Standard', b.display_type, b.controls, b.scrambler, NULL, NULL, NULL, NULL, b.success, a.completed, b.timestamp, b.solve_type, b.marathon_length, b.time, b.moves, b.tps, b.completed, b.width, b.height, b.id from (single_solves a join solves b on a.id between b.single_start_id and b.single_end_id) where b.solve_type!='Standard' AND b.scrambler='Random permutation'"
        params = ()
        query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
        query, params = addCategoryFilters(query, params, categoryFilters)
        query = modify_query_output(query)
        cursor.execute(query, params)
        return cursor.fetchall()

    return makeDBrequest(dbpath, getSingleSolvesAsMainRequest, DB_ERROR_FETCHING_6, {
        "timestamp_min": timestamp_min,
        "timestamp_max": timestamp_max,
        "categoryFilters": categoryFilters
    })


def getFilteredSolves(table, dbpath, timestamp_min, timestamp_max, categoryFilters):
    def getFilteredSolvesRequest(cursor, requestData):
        timestamp_min = requestData.get("timestamp_min")
        timestamp_max = requestData.get("timestamp_max")
        categoryFilters = requestData.get("categoryFilters")
        if any(not sublist for key, sublist in categoryFilters.items() if key != 'checkboxes_presets'):
            return []
        query = f"SELECT * FROM {table} WHERE scrambler='Random permutation'"
        params = ()
        query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
        query, params = addCategoryFilters(query, params, categoryFilters)
        cursor.execute(query, params)
        return cursor.fetchall()

    return makeDBrequest(dbpath, getFilteredSolvesRequest, DB_ERROR_FETCHING_4, {
        "timestamp_min": timestamp_min,
        "timestamp_max": timestamp_max,
        "categoryFilters": categoryFilters
    })


def getSkippedScrambles(dbpath, timestamp_min, timestamp_max, categoryFilters, ADD_SINGLES_AS_MAIN):
    if ADD_SINGLES_AS_MAIN:
        newCategoryFilters = {key: value for key, value in categoryFilters.items() if key != 'checkboxes_solve'}
        skipped = getFilteredSolves("skipped_scrambles", dbpath, timestamp_min, timestamp_max, newCategoryFilters)
    else:
        skipped = getFilteredSolves("skipped_scrambles", dbpath, timestamp_min, timestamp_max, categoryFilters)
    return skipped


def getSolvesFromDB(dbpath, timestamp_min, timestamp_max, categoryFilters, ADD_SINGLES_AS_MAIN):
    mainData = getFilteredSolves("solves", dbpath, timestamp_min, timestamp_max, categoryFilters)
    if ADD_SINGLES_AS_MAIN:
        newCategoryFilters = {key: value for key, value in categoryFilters.items() if key != 'checkboxes_solve'}
        singlesData = getSingleSolvesAsMain(dbpath, timestamp_min, timestamp_max, newCategoryFilters)
        return mainData, singlesData
    else:
        return mainData, []


def addTimestamps(query, params, timestamp_min, timestamp_max):
    if timestamp_min is not None:
        query += " AND timestamp >= ?"
        params += (timestamp_min,)

    if timestamp_max is not None:
        query += " AND timestamp <= ?"
        params += (timestamp_max,)

    return query, params


def getLatestSolve(dbpath, timestamp_min=None, timestamp_max=None):
    def getLatestSolveRequest(cursor, requestData):
        timestamp_min = requestData.get("timestamp_min")
        timestamp_max = requestData.get("timestamp_max")

        query = "SELECT * FROM solves WHERE scrambler='Random permutation'"
        params = ()
        query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
        query += " ORDER BY ID DESC LIMIT 1"

        cursor.execute(query, params)
        return cursor.fetchone()

    return makeDBrequest(dbpath, getLatestSolveRequest, DB_ERROR_FETCHING_2, {
        "timestamp_min": timestamp_min,
        "timestamp_max": timestamp_max
    })


def getCategoryLimits(dbpath, loadSinglesAsMain, timestamp_min=None, timestamp_max=None):
    def getCategoryLimitsRequest(cursor, requestData):
        timestamp_min = requestData.get("timestamp_min")
        timestamp_max = requestData.get("timestamp_max")

        def fetch_unique_values_combined(cursor, columns, timestamp_min, timestamp_max):
            query = f"""
                SELECT {", ".join(columns)}, MAX(id) AS max_id
                FROM solves
                WHERE scrambler='Random permutation'
            """
            params = ()
            query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
            query += f" GROUP BY {', '.join(columns)}"
            query += " ORDER BY max_id DESC"
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                result_dict = {}
                for i, column in enumerate(columns):
                    result_dict[column] = row[i]
                results.append(result_dict)
            return results

        def fetch_unique_values(cursor, column, timestamp_min, timestamp_max, singleSolves=False):
            if singleSolves:
                query = "SELECT MIN(single_start_id) AS min_start_id, MAX(single_end_id) AS max_end_id FROM solves WHERE scrambler='Random permutation'"
                params = ()
                query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
                cursor.execute(query, params)
                min_start_id, max_end_id = cursor.fetchone()
                if min_start_id is None or max_end_id is None:
                    return []
                query = f"SELECT DISTINCT {column} FROM single_solves WHERE id BETWEEN {min_start_id} AND {max_end_id}"
                params = ()
            else:
                query = f"SELECT DISTINCT {column} FROM solves WHERE scrambler='Random permutation'"
                params = ()
                query, params = addTimestamps(query, params, timestamp_min, timestamp_max)
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]

        solve_types = fetch_unique_values(cursor, "solve_type", timestamp_min, timestamp_max)
        if loadSinglesAsMain and ("Standard" not in solve_types) and solve_types:
            solve_types.append("Standard")
        display_types = fetch_unique_values(cursor, "display_type", timestamp_min, timestamp_max)
        control_types = fetch_unique_values(cursor, "controls", timestamp_min, timestamp_max)
        marathon_lengths = fetch_unique_values(cursor, "marathon_length", timestamp_min, timestamp_max)
        if None in marathon_lengths:
            marathon_lengths.remove(None)
        puzzle_sizes = fetch_unique_values(cursor, "width || 'x' || height", timestamp_min, timestamp_max,
                                           loadSinglesAsMain)
        if "Marathon" in solve_types:
            solve_types.remove("Marathon")
            for length in marathon_lengths:
                solve_types.append(f"x{length} Marathon")
        combined_values = fetch_unique_values_combined(cursor,
                                                       ["solve_type", "display_type", "controls", "marathon_length",
                                                        "width", "height"], timestamp_min, timestamp_max)
        return {
            "solve_types": solve_types,
            "display_types": display_types,
            "puzzle_sizes": puzzle_sizes,
            "control_types": control_types,
            "combined": combined_values
        }

    return makeDBrequest(dbpath, getCategoryLimitsRequest, DB_ERROR_FETCHING_1, {
        "timestamp_min": timestamp_min,
        "timestamp_max": timestamp_max
    })


def getPathFromUser(root):
    if sqlConnectCheck(SLIDYSIM_DEFAULT_PATH):
        return SLIDYSIM_DEFAULT_PATH
    while True:
        path_by_user = Querybox.get_string(prompt=ENTER_SLIDYSIM_PATH_REQUEST, title=MY_APP_TITLE, parent=root)
        if sqlConnectCheck(path_by_user):
            return path_by_user
        if path_by_user is None:
            exit()


def parseRowForCategory(solveRow):
    solveList = list(solveRow)
    displayType = solveList[10]
    solveType = solveList[9]
    if solveType == "Marathon":
        marathon_length = solveList[13]
        solveType = f"x{marathon_length} Marathon"
    puzzleSize = f"{solveList[3]}x{solveList[4]}"
    controlType = solveList[11]
    return {
        "displayType": displayType,
        "solveType": solveType,
        "puzzleSize": puzzleSize,
        "controlType": controlType
    }


def getSelectedCategories(checkboxes):
    filtered_checkboxes = {
        'checkboxes_display': [],
        'checkboxes_solve': [],
        'checkboxes_puzzles': [],
        'checkboxes_controls': [],
        'checkboxes_presets': [],
    }

    for group_name, group in checkboxes.items():
        if group_name not in filtered_checkboxes:
            continue
        for item_name, value in group.items():
            if value.get():
                filtered_checkboxes[group_name].append(item_name)
    return filtered_checkboxes


def clearCategories(checkboxes):
    for group_name, group in checkboxes.items():
        if type(group) == list:
            continue
        for item_name, value in group.items():
            value.set(False)


def setCategoriesToLatest(checkboxes, latestSolve):
    clearCategories(checkboxes)
    category = parseRowForCategory(latestSolve)
    categoryShortString = getCategoryStringSimple(category)
    for key, value in checkboxes["checkboxes_presets"].items():
        if key == categoryShortString:
            value.set(True)
    for category_name, category_value in category.items():
        checkboxes_group_name = CATEGORY_CHECKBOX_MAPPING[category_name]
        if checkboxes_group_name in checkboxes:
            if category_value in checkboxes[checkboxes_group_name]:
                checkboxes[checkboxes_group_name][category_value].set(True)


def clearSessionTree(sessionTree):
    for child in sessionTree.get_children():
        sessionTree.delete(child)


def parseSingleSolves(singleSolvesData):
    newSingleSolvesData = []
    for row in singleSolvesData:
        solveData = {"puzzle": f"{row[1]}x{row[2]}",
                     "time": float(row[3] / 1000),
                     "moves": int(row[4] / 1000),
                     "tps": float(row[5] / 1000),
                     "scramble": row[6],
                     "solution": row[7],
                     "completed": True if row[8] == 1 else False
                     }
        if row[11] is not None:
            solveData["movetimes"] = list(map(int, row[11].split(',')))
        else:
            solveData["movetimes"] = []

        newSingleSolvesData.append(solveData)
    return newSingleSolvesData


def parseSkippedScrambles(skippedScramblesData):
    newSkippedScramblesData = []
    for row in skippedScramblesData:
        solveData = {"puzzle": f"{row[1]}x{row[2]}",
                     "scramble": row[3],
                     "solve_type": row[4],
                     "controls": row[6],
                     "display_type": row[5],
                     "timestamp": row[12],
                     "date": convert_unix_timestamp_ms(row[12]),
                     "time": 9999999,
                     "moves": 9999999,
                     "tps": 0,
                     "fullyCompleted": False
                     }
        if solveData["solve_type"] == "Marathon":
            solveData["solve_type"] = f"x{row[8]} Marathon"
            solveData["marathon_length"] = row[8]
        newSkippedScramblesData.append(solveData)
    return newSkippedScramblesData


def parseMainSolveData(mainSolvesData):
    newMainSolveData = []
    for row in mainSolvesData:
        solveData = {}
        solveData["id"] = row[0]
        solveData["singles_range_ids"] = (row[1], row[2])
        solveData["puzzle"] = f"{row[3]}x{row[4]}"
        solveData["solve_type"] = row[9]
        if solveData["solve_type"] == "BLD":
            solveData["bldinfo"] = {"memo_time": float(row[5] / 1000), "success": True if row[17] == 1 else False}
        if solveData["solve_type"] == "Marathon":
            solveData["solve_type"] = f"x{row[13]} Marathon"
            solveData["marathon_length"] = row[13]
        solveData["controls"] = row[11]
        solveData["display_type"] = row[10]
        solveData["time"] = float(row[6] / 1000)
        solveData["moves"] = int(row[7] / 1000)
        solveData["tps"] = float(row[8] / 1000)
        solveData["timestamp"] = row[19]
        solveData["date"] = convert_unix_timestamp_ms(row[19])
        solveData["completed"] = True if row[18] == 1 else False
        if len(row) > 20:
            solveData["true_solve_type"] = row[20]
            if solveData["true_solve_type"] == "Marathon":
                solveData["true_solve_type"] = f"x{row[21]} Marathon"
            solveData["true_time"] = float(row[22] / 1000)
            solveData["true_moves"] = int(row[23] / 1000)
            solveData["true_tps"] = float(row[24] / 1000)
            solveData["true_completed"] = True if row[25] == 1 else False
            solveData["true_size"] = f"{row[26]}x{row[27]}"
            solveData["parent_id"] = row[28]
            if solveData["true_solve_type"] == "BLD":
                solveData["bldinfo"] = {"memo_time": float(row[5] / 1000), "success": True if row[17] == 1 else False}
        solveData["fullyCompleted"] = isCompleted(solveData)
        newMainSolveData.append(solveData)
    return newMainSolveData


def isCompleted(item):
    completed = item.get("completed", False)
    bldinfo = item.get("bldinfo")
    success = bldinfo is None or bldinfo.get("success", False)
    return completed and success


def getReconstructionLink(solution, tpsintform, scramble, movetimeslist=-1):
    input_array = [solution, tpsintform, scramble, movetimeslist]
    json_string = json.dumps(input_array)
    compressed_data = zlib.compress(json_string.encode(), level=9)
    base64_encoded_string = base64.b64encode(compressed_data).decode()
    return "https://slidysim.online/replay?r=" + ''.join(
        c if c.isalnum() or c in ['-', '_', '.', '~'] else f"%{ord(c):02X}" for c in base64_encoded_string)


def parseBulkSinglesCompact(solves, isMarathon, tableseparator=" " * 4):
    tableseparator = "\t"
    parentData = solves[0]['parent_data']
    parent_solve_type = parentData['solve_type']
    parent_time = parentData['time']
    parent_moves = parentData["moves"]
    parent_tps = parentData["tps"]
    parent_completed = parentData["completed"]
    parent_size = parentData["puzzle"]
    dispalyType = display_type_options.get(parentData['display_type'], "Error")
    solveType = solve_type_options.get(parent_solve_type, "Marathon")
    controls = controls_options.get(parentData['controls'], "Error")
    if solveType == "Marathon":
        solveType = parent_solve_type.split()[0]
    parentCategory = " ".join(filter(None, [controls, dispalyType, parent_size, solveType]))
    if not parent_completed:
        parentCategory = "[Not finished] " + parentCategory
    parentScore = f"{parent_time:.3f}s ({parent_moves}/{parent_tps:.3f})"
    parentFinal = f"{parentCategory} {parentScore} solve done at {parentData['date']}\n```\n"
    textOutput = parentFinal

    # Define column widths
    if isMarathon:
        col_widths = [7, 7, 5, 7]  # Total time, Time, Moves, TPS
        headers = ["Total", "Time", "Moves", "TPS"]
    else:
        col_widths = [7, 7, 5, 7]   # Puzzle, Time, Moves, TPS
        headers = ["Puzzle", "Time", "Moves", "TPS"]

    # Format header row
    header_row = []
    for i, header in enumerate(headers):
        header_row.append(f"{header:^{col_widths[i]}}")
    textOutput += tableseparator.join(header_row)
    textOutput += "\n"

    totalTime = 0
    for singleSolve in solves:
        time = singleSolve['time']
        s_time = f"{time:.3f}"
        s_moves = str(singleSolve['moves'])
        s_tps = f"{singleSolve['tps']:.3f}"

        row = []
        if isMarathon:
            totalTime += time
            row.append(f"{totalTime:>{col_widths[0]}.3f}")
            row.append(f"{s_time:>{col_widths[1]}}")
        else:
            puzzle = singleSolve['puzzle']
            row.append(f"{puzzle:>{col_widths[0]}}")
            row.append(f"{s_time:>{col_widths[1]}}")

        row.append(f"{s_moves:^{col_widths[2]}}")
        row.append(f"{s_tps:>{col_widths[3]}}")

        row_text = tableseparator.join(row)
        if not singleSolve['completed']:
            row_text += " [Not finished]"
        textOutput += row_text + "\n"

    textOutput += "```\n"
    return textOutput


def parseSingleToText(singleInfo, tableStyle=False, tableseparator="\t"):
    parentData = singleInfo["parent_data"]
    if parentData.get("true_solve_type"):
        parent_solve_type = parentData["true_solve_type"]
        parent_time = parentData["true_time"]
        parent_moves = parentData["true_moves"]
        parent_tps = parentData["true_tps"]
        parent_completed = parentData["true_completed"]
        parent_size = parentData["true_size"]
    else:
        parent_solve_type = parentData['solve_type']
        parent_time = parentData['time']
        parent_moves = parentData["moves"]
        parent_tps = parentData["tps"]
        parent_completed = parentData["completed"]
        parent_size = parentData["puzzle"]
    if parent_solve_type == "BLD":
        if singleInfo.get('solution'):
            bld_memo = parentData['bldinfo']['memo_time']
            parent_completed = parentData['bldinfo']['success']
            singleInfo['completed'] = parent_completed
    dispalyType = display_type_options.get(parentData['display_type'], "Error")
    solveType = solve_type_options.get(parent_solve_type, "Marathon")
    controls = controls_options.get(parentData['controls'], "Error")
    if solveType == "Marathon":
        solveType = parent_solve_type.split()[0]
    parentCategory = " ".join(filter(None, [controls, dispalyType, parent_size, solveType]))
    if not parent_completed:
        parentCategory = "[Not finished] " + parentCategory
    if singleInfo.get('emulated'):
        parentInfo = f"{parentCategory} solve done at {parentData['date']}"
        return tableseparator.join(
            [parentInfo, singleInfo['puzzle'], str(singleInfo['completed']), f"{singleInfo['time']:.3f}",
             str(singleInfo['moves']), f"{singleInfo['tps']:.3f}"])
    if singleInfo.get('solution'):
        if solveType == "Single":
            parentScore = ""
        else:
            parentScore = f"Single from {parent_time:.3f}s ({parent_moves}/{parent_tps:.3f}) "
            if parent_solve_type == 'BLD':
                parentScore += f"[{bld_memo} memo] "
        parentFinal = f"Parent: {parentCategory} {parentScore}solve done at {parentData['date']}"
        singleBasic = f"{singleInfo['puzzle']} sliding puzzle solved in {singleInfo['time']:.3f}s with {singleInfo['moves']} moves {singleInfo['tps']:.3f} tps"
        if not singleInfo['completed']:
            singleBasic = f"[Not finished] {singleBasic}"
        singleLink = getReconstructionLink(singleInfo['solution'], int(singleInfo['tps'] * 1000),
                                           singleInfo['scramble'],
                                           singleInfo['movetimes'])
        linkToReturn = singleLink
        finalBlock = '\n'.join([
            parentFinal,
            f"[{singleBasic}]({linkToReturn})" if len(linkToReturn) < 1800 else f"{singleBasic}\n{linkToReturn}"
        ])

        if not tableStyle:
            return linkToReturn, f"{finalBlock}\n"
        else:
            return tableseparator.join(
                [parentFinal, singleInfo['puzzle'], str(singleInfo['completed']), f"{singleInfo['time']:.3f}",
                 str(singleInfo['moves']), f"{singleInfo['tps']:.3f}", singleInfo['scramble'], singleInfo['solution'],
                 str(singleInfo['movetimes']), linkToReturn])
    else:
        parentFinal = f"{parentCategory} category skipped solve at {parentData['date']}"
        finalBlock = '\n'.join([parentFinal, f"Scramble: {singleInfo['scramble']}"])
        if not tableStyle:
            return None, f"{finalBlock}\n"
        else:
            return tableseparator.join(
                [parentFinal, singleInfo['puzzle'], 'False', 'Skipped', 'Skipped', 'Skipped', singleInfo['scramble']])


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


def formatStat(mainValue, secValue, secValue2):
    main_truncated = truncate(mainValue, 3)
    sec_truncated = truncate(secValue, 3)
    sec2_truncated = truncate(secValue2, 3)
    return f"{main_truncated:.3f} ({sec_truncated:.3f}/{sec2_truncated:.3f})"


def findBest(validSolves, mainfield, bestIsLower):
    if bestIsLower:
        return min(validSolves, key=lambda solve: solve[mainfield])
    else:
        return max(validSolves, key=lambda solve: solve[mainfield])


def getBestAverageOf(mainfield, amount, solves):
    secondary_field_one, secondary_field_two = {'time': ('moves', 'tps'),
                                                'moves': ('time', 'tps'),
                                                'tps': ('time', 'moves')}.get(mainfield)
    bestIsLower = mainfield != 'tps'
    valid_solves = [solve for solve in solves if solve['parent_data']['fullyCompleted']]
    if not valid_solves:
        return None
    else:
        if amount == 1:
            bestSolve = findBest(valid_solves, mainfield, bestIsLower)
            bestSolveFormatter = formatStat(bestSolve[mainfield],
                                            bestSolve[secondary_field_one],
                                            bestSolve[secondary_field_two])
            return f"Best single: {bestSolveFormatter}\n"
        else:
            best_average = None
            best_secondary_field_one_average = None
            best_secondary_field_two_average = None
            best_date = None  # TESTING
            expectedLen = amount - 2
            for i in range(len(solves) - amount + 1):
                window = solves[i:i + amount]
                if any(not solve['parent_data']['fullyCompleted'] for solve in window):
                    continue
                main_field_values = [solve[mainfield] for solve in window]
                main_field_values.sort()
                main_field_values = main_field_values[1:-1]
                average = sum(main_field_values) / expectedLen
                secondary_field_one_values = [solve[secondary_field_one] for solve in window]
                secondary_field_one_values.sort()
                secondary_field_one_values = secondary_field_one_values[1:-1]
                secondary_field_two_values = [solve[secondary_field_two] for solve in window]
                secondary_field_two_values.sort()
                secondary_field_two_values = secondary_field_two_values[1:-1]
                secondary_field_one_average = sum(secondary_field_one_values) / expectedLen
                secondary_field_two_average = sum(secondary_field_two_values) / expectedLen
                if best_average is None or (average is not None and (
                        (bestIsLower and average < best_average) or (not bestIsLower and average > best_average))):
                    best_average = average
                    best_secondary_field_one_average = secondary_field_one_average
                    best_secondary_field_two_average = secondary_field_two_average
                    best_date = window[-1]['parent_data']["date"]  # TESTING
            if best_average is not None:
                best_average_formatter = formatStat(best_average, best_secondary_field_one_average,
                                                    best_secondary_field_two_average)
                return f"Best ao{amount}: {best_average_formatter} | {best_date}\n"  # TESTING DATE PART
            else:
                return None


def longest_consecutive_valid_solves(solves):
    longest, current = 0, 0
    for solve in solves:
        current = current + 1 if solve['parent_data']['fullyCompleted'] else 0
        longest = max(longest, current)
    return longest


def calculateAvgs(field, solves):
    averages = []
    all = longest_consecutive_valid_solves(solves)
    # amounts = [10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 12, 5, 1]

    # TESTING
    amounts = list(range(4, min(all, 101)))  # creates a list from 4 to `all`
    amounts.append(1)  # adds 1 at the end of the list
    # TESTING

    if all > 5 and all not in amounts:
        amounts.insert(0, all)
    for amount in amounts:
        average = getBestAverageOf(mainfield=field, amount=amount, solves=solves)
        if average is not None:
            averages.append(average)
    stats = ''.join(averages)
    if not averages:
        return ""
    return f"{field.capitalize()} stats:\n{stats}"


def calculateSelectionStats(solves):
    solvesSelected = len(solves)
    solvesValid = sum(1 for solve in solves if solve['parent_data']['fullyCompleted'])
    solvesSkipped = sum(1 for solve in solves if solve['time'] == 9999999)
    timeStats = calculateAvgs(field='time', solves=solves)
    moveStats = calculateAvgs(field='moves', solves=solves)
    tpsStats = calculateAvgs(field='tps', solves=solves)

    return "\n".join([
        f"Solves selected: {solvesSelected}",
        f"Completed solves: {solvesValid}",
        f"Skipped scrambles: {solvesSkipped}",
        timeStats,
        moveStats,
        tpsStats
    ])


def getAvgInfo(solves):
    text = ""
    lowest_sid = solves[0]['parent_data']['SID']
    noGaps = all(solves[i]['parent_data']['SID'] == lowest_sid + i for i in range(len(solves)))
    isSingleCategory = all(solve['parent_data'][key] == solves[0]['parent_data'][key] for key in
                           ['solve_type', 'puzzle', 'display_type', 'controls'] for solve in solves)

    if noGaps:
        if not isSingleCategory:
            text += WARNING_MIXED_SOLVES
        text += calculateSelectionStats(solves)
    else:
        text = ERROR_NON_CONSECUTIVE
    return text


def indexMainData(mainSolvesData):
    mainSolvesData = sorted(mainSolvesData, key=lambda x: x['timestamp'])
    for i, solve in enumerate(mainSolvesData):
        solve['SID'] = i + 1
    return mainSolvesData


class SolvesTableSelectionController:
    def __init__(self, textbox, imageLabel, solvesTableView, mainSolvesData, dbpath, includeBulk):
        self.latestSelection = {}
        self.textbox = textbox
        self.imageLabel = imageLabel
        self.solvesTableView = solvesTableView
        self.mainSolvesData = mainSolvesData
        self.dbpath = dbpath
        self.includeBulk = includeBulk

    def solvesSelectedEvent(self, event):
        self.addSinglesInfo()

    def addSinglesInfo(self, selectedIDs=None):
        bulkInfoNotProvided = selectedIDs is None
        if bulkInfoNotProvided:
            selectedIDs = self.solvesTableView.selection()
        selectedSingles, selectedParents = self.splitIDs(selectedIDs)
        if len(selectedParents) == 0:
            if len(selectedSingles) > 0:
                self.displaySinglesData(selectedSingles, bulkInfoNotProvided)
        else:
            self.deleteSelectedSingles()
            selectedRows = [row for row in self.mainSolvesData if
                            'item_id' in row and row['item_id'] in selectedParents]
            if len(selectedParents) == 1:
                selectedSingles = self.fetchSinglesDataFromParent(selectedRows[0])
                if len(selectedSingles) == 1:
                    solve = selectedSingles[0]
                    text = self.displayOneSolveData(solve)
                    bad = not solve['completed']
                    self.replaceAndCopyText(text, bad)
                else:
                    self.populateTableWithSingles(selectedSingles)
                    self.addSinglesInfo(selectedIDs=self.latestSelection.keys())
            else:
                solves = self.emulateSingleSolvesFromParents(selectedRows)
                text = getAvgInfo(solves)
                text += self.displayMultipleSolvesData(solves, True)
                bad = any(solve.get("completed", False) == False for solve in solves)
                self.replaceAndCopyText(text, bad)

    def expand_all(self, tree, item=''):
        children = tree.get_children(item)
        for child in children:
            tree.item(child, open=True)
            self.expand_all(tree, child)

    def replaceAndCopyText(self, text, bad=False):
        replaceText(self.textbox, text, bad)
        pyperclip.copy(text)
        toastUpdate("Selected singles detailed info copied to clipboard!")

    def displayOneSolveData(self, solve):
        reconLink, text = parseSingleToText(solve)
        renderPuzzleImage(solve['scramble'], self.imageLabel, reconLink)
        return text

    def displayMultipleSolvesData(self, solves, bulkInfoNotProvided):
        isMarathon = solves[0]['parent_data'].get('marathon_length')
        if bulkInfoNotProvided:
            text = ""
        else:
            text = parseBulkSinglesCompact(solves, isMarathon, tableseparator="\t")
        if self.includeBulk:
            text += "Very detailed info:\n"
            text += TABLE_SEPARATOR.join(singleHeaders) + "\n"
        dataToGraph = [[], [], []]
        data_labels = []
        isEmulated = solves[0]['parent_data'] != solves[1]['parent_data']
        makeHistogram = isEmulated or isMarathon
        for solve in solves:
            if self.includeBulk:
                text += parseSingleToText(solve, tableStyle=True, tableseparator=TABLE_SEPARATOR)
                text += "\n"
            dataToGraph[0].append(solve['time'])
            dataToGraph[1].append(solve['moves'])
            dataToGraph[2].append(solve['tps'])
            if not makeHistogram:
                data_labels.append(solve['puzzle'])
        renderGraphImage(self.imageLabel, dataToGraph, histogram=makeHistogram, data_labels=data_labels)
        return text

    def displaySinglesData(self, selectedSinglesIDs, bulkInfoNotProvided):
        solves = [self.latestSelection[id] for id in selectedSinglesIDs]
        if len(selectedSinglesIDs) == 1:
            text = self.displayOneSolveData(solves[0])
        else:
            text = self.displayMultipleSolvesData(solves, bulkInfoNotProvided)
        bad = any(solve.get("completed", False) == False for solve in solves)
        self.replaceAndCopyText(text, bad)

    def splitIDs(self, selectedIDs):
        selectedSingles = []
        selectedParents = []
        for id in selectedIDs:
            if "SINGLE" in id:
                selectedSingles.append(id)
            else:
                selectedParents.append(id)
        return selectedSingles, selectedParents

    def deleteSelectedSingles(self):
        for iid in self.latestSelection.keys():
            self.solvesTableView.delete(iid)
        self.latestSelection = {}

    def emulateSingleSolvesFromParents(self, rows):
        solves = []
        for row in rows:
            if row.get("singles_range_ids"):
                first, last = row["singles_range_ids"]
                singleSolves = parseSingleSolves(getSingleSolves(self.dbpath, first, last))
                solve = singleSolves[0] if len(singleSolves) == 1 else row
                solve["emulated"] = len(singleSolves) != 1
            else:
                solve = row
                solve['completed'] = False
            solve["parent"] = row["item_id"]
            solve["parent_data"] = row
            solves.append(solve)
        return solves

    def fetchSinglesDataFromParent(self, row):
        if row.get("singles_range_ids"):
            first, last = row["singles_range_ids"]
            singleSolves = parseSingleSolves(getSingleSolves(self.dbpath, first, last))
        else:
            singleSolves = [row]
            row['completed'] = False
        for single_solve in singleSolves:
            single_solve["parent"] = row["item_id"]
            single_solve["parent_data"] = row
        return singleSolves

    def populateTableWithSingles(self, selectedSingles):
        for id, solve in enumerate(selectedSingles):
            id = f"SINGLE{id}"
            self.latestSelection[id] = solve
            self.solvesTableView.insert(solve["parent"], 'end', iid=id, tags=("Single",),
                                        values=(
                                            "",
                                            "Single solve",
                                            solve["puzzle"],
                                            solve["time"],
                                            solve["moves"],
                                            solve["tps"],
                                            solve.get("completed", False))
                                        )
            self.expand_all(self.solvesTableView)


def generateTableHeaders(categoryFilters, includeSkipped, includeBLD):
    del categoryFilters['checkboxes_presets']
    for key in list(categoryFilters.keys()):
        categoryFilters[key] = len(categoryFilters[key]) > 1
    coldata = []
    columns = ["SID", "Date", "Size", "Time", "Moves", "TPS"]
    if includeSkipped:
        columns.append("Completed")
    if includeBLD:
        columns.append("BLD memo")
    if categoryFilters['checkboxes_display']:
        columns.append("Display type")
    if categoryFilters['checkboxes_solve']:
        columns.append("Solve Type")
    if categoryFilters['checkboxes_controls']:
        columns.append("Controls")
    for column in columns:
        coldata.append({"text": column})
    return columns, coldata


def generateTableRows(mainSolvesData, includeSkipped, includeBLD, columns):
    rowdata = []
    addedRowIDs = []
    for row_id, row in enumerate(mainSolvesData):
        if includeBLD:
            if row["solve_type"] == "BLD" and row["time"] != 9999999:
                row["BLD memo"] = row["bldinfo"]["memo_time"]
            else:
                row["BLD memo"] = 0
        if row["fullyCompleted"] or includeSkipped:
            solveinfotuple = tuple(
                row[tableColumnsMapping[column]] for column in columns if column in tableColumnsMapping)
            rowdata.append(solveinfotuple)
            addedRowIDs.append(row_id)
    return addedRowIDs, rowdata


def populateTableData(solvesTable, categoryFilters, mainSolvesData, includeSkipped):
    includeBLD = "BLD" in categoryFilters["checkboxes_solve"]
    columns, coldata = generateTableHeaders(categoryFilters, includeSkipped, includeBLD)
    addedRowIDs, rowdata = generateTableRows(mainSolvesData, includeSkipped, includeBLD, columns)
    solvesTable.build_table_data(coldata=coldata, rowdata=rowdata)
    return addedRowIDs, columns


def styleSolvesTable(addedRowIDs, mainSolvesData, solvesTable, includeSKipped, columns):
    if includeSKipped:
        for added_row_id in addedRowIDs:
            row = mainSolvesData[added_row_id]
            item_id = row["item_id"]
            if row["time"] == 9999999:
                solvesTable.view.item(item_id, tags=("Skipped",))
                continue
            if not row["fullyCompleted"]:
                solvesTable.view.item(item_id, tags=("Incomplete",))
                continue
            solvesTable.view.item(item_id, tags=("OK",))
    for column_id, _ in enumerate(columns):
        solvesTable.align_column_center(cid=column_id)

    treeview = solvesTable.view

    def adjustColumns(event=None):
        total_width = treeview.winfo_width()
        num_columns = len(treeview["columns"])
        column_width = total_width // num_columns
        for col in treeview["columns"]:
            treeview.column(col, width=column_width)

    treeview.bind("<Configure>", adjustColumns)
    treeview.unbind("<Button-3>")
    adjustColumns()


def manageSolvesTable(mainSolvesData, dbpath, tableComponents, categoryFilters, includeSkipped, textbox, imageLabel,
                      includeBulk):
    solvesTable = tableComponents["solvesTable"]
    mainSolvesData = indexMainData(mainSolvesData)
    addedRowIDs, columns = populateTableData(solvesTable, categoryFilters, mainSolvesData, includeSkipped)
    selectionController = SolvesTableSelectionController(textbox, imageLabel, solvesTable.view, mainSolvesData, dbpath,
                                                         includeBulk)
    for list_id, item_id in enumerate(solvesTable.view.get_children()):
        mainSolvesData[addedRowIDs[list_id]]["item_id"] = item_id
    styleSolvesTable(addedRowIDs, mainSolvesData, solvesTable, includeSkipped, columns)
    solvesTable.view.bind("<ButtonRelease-1>", selectionController.solvesSelectedEvent)
    solvesTable.view.bind("<Return>", selectionController.solvesSelectedEvent)

    solvesTable.sort_column_data(cid=FIRST_COLUMN_ID, sort=DESCENDING_SORTING_TK)
    selectionController.solvesSelectedEvent(event=None)


def addItemToTree(sessionTree, title, value):
    latest_tag = "odd" if not sessionTree.get_children() or \
                          sessionTree.item(sessionTree.get_children()[-1], option="tags")[0] == "even" else "even"
    sessionTree.insert('', 'end', values=(title, value), tags=(latest_tag,))


def fillSessionTree(sessionTree, mainSolvesData, dynamic, skippedLen, singlesData):
    if len(singlesData) > 0:
        bannedIDs = [solve['id'] for solve in mainSolvesData]
        extraData = [data for data in singlesData if data['parent_id'] not in bannedIDs]
        mainSolvesData = mainSolvesData + extraData
    clearSessionTree(sessionTree)
    addItemToTree(sessionTree, "Dynamically Updated", dynamic)
    if len(mainSolvesData) < 1:
        addItemToTree(sessionTree, "Session is empty", "Do some solves!")
        return []
    timestamps = [solve["timestamp"] for solve in mainSolvesData]
    firstSolveTimestamp = min(timestamps)
    latestSolveTimestamp = max(timestamps)
    solvesDone = len(mainSolvesData)
    solvesDoneCompleted = sum(1 for item in mainSolvesData if item["fullyCompleted"])
    totalSolvingTime = sum(item.get("time", 0) for item in mainSolvesData)
    totalSolvingTimeCompleted = sum(item.get("time", 0) for item in mainSolvesData if item["fullyCompleted"])
    meanMoves = sum(item.get("moves", 0) for item in mainSolvesData if
                    item["fullyCompleted"]) / solvesDoneCompleted if solvesDoneCompleted else 0
    meanTime = totalSolvingTimeCompleted / solvesDoneCompleted if solvesDoneCompleted else 0
    meanTPS = sum(item.get("tps", 0) for item in mainSolvesData if
                  item["fullyCompleted"]) / solvesDoneCompleted if solvesDoneCompleted else 0
    completed_solves = [item for item in mainSolvesData if item["fullyCompleted"]]
    addItemToTree(sessionTree, "Session started", str(convert_unix_timestamp_ms(firstSolveTimestamp)))
    addItemToTree(sessionTree, "Session ended", str(convert_unix_timestamp_ms(latestSolveTimestamp)))
    addItemToTree(sessionTree, "Session duration", duration(firstSolveTimestamp, latestSolveTimestamp))
    addItemToTree(sessionTree, "Total solving time", format_duration(timedelta(seconds=totalSolvingTime)))
    addItemToTree(sessionTree, "Scrambles skipped", skippedLen)
    addItemToTree(sessionTree, "Total solves done", solvesDone)
    addItemToTree(sessionTree, "Total solves done (Completed)", solvesDoneCompleted)
    if len(singlesData) > 0:
        mainSolvesData = mainSolvesData[:len(mainSolvesData) - len(extraData)]
        mainSolvesData = mainSolvesData + singlesData
        completed_solves = [item for item in mainSolvesData if item["fullyCompleted"]]
    if completed_solves:
        addItemToTree(sessionTree, "Total solving time (Completed)",
                      format_duration(timedelta(seconds=totalSolvingTimeCompleted)))

        best_time, best_time_moves, best_time_tps = min(
            ((item["time"], item["moves"], item["tps"]) for item in completed_solves),
            key=lambda x: x[0])

        best_moves, best_moves_time, best_moves_tps = min(
            ((item["moves"], item["time"], item["tps"]) for item in completed_solves),
            key=lambda x: x[0])

        best_tps, best_tps_time, best_tps_moves = max(
            ((item["tps"], item["time"], item["moves"]) for item in completed_solves),
            key=lambda x: x[0])
        best_time_formatted = f"{best_time} ({best_time_moves} / {best_time_tps})"
        best_moves_formatted = f"{best_moves} ({best_moves_time} / {best_moves_tps})"
        best_tps_formatted = f"{best_tps} ({best_tps_time} / {best_tps_moves})"

        addItemToTree(sessionTree, "Mean Time (Completed)", "{:.3f}".format(meanTime))
        addItemToTree(sessionTree, "Mean Moves (Completed)", "{:.3f}".format(meanMoves))
        addItemToTree(sessionTree, "Mean TPS (Completed)", "{:.3f}".format(meanTPS))
        addItemToTree(sessionTree, "Best Time solve (Completed)", best_time_formatted)
        addItemToTree(sessionTree, "Best Moves solve (Completed)", best_moves_formatted)
        addItemToTree(sessionTree, "Best TPS solve (Completed)", best_tps_formatted)
    return mainSolvesData


def was_file_changed(file_path, last_known_mtime):
    try:
        return os.path.getmtime(file_path) != last_known_mtime
    except OSError:
        return True  # File was deleted or inaccessible


class SessionController:
    def __init__(self, dbpath, limitedCategoriesFrames, sessionTree, updateProgress, root, setToLatest,
                 tableComponents, graphComponents, autoUpdateVar, datePickerElements):
        self.includeStatsTableCheckbox_var = ttk.BooleanVar()
        self.loadSinglesAsMain_var = ttk.BooleanVar()
        self.include_checkbox_var = ttk.BooleanVar()
        self.dbpath = dbpath
        self.limitedCategoriesFrames = limitedCategoriesFrames
        self.sessionTree = sessionTree
        self.dynamic = True
        self.focusedOut = False
        self.checkboxes = None
        self.progress = updateProgress
        self.setToLatest = setToLatest
        self.autoUpdateVar = autoUpdateVar
        self.root = root
        self.tableComponents = tableComponents
        self.graphComponents = graphComponents
        self.datePickerElements = datePickerElements
        self.lastKnownChange = 0
        self.configureTableCheckbox()

    def configureTableCheckbox(self):
        tableCB = self.tableComponents["include_checkbox"]
        tableCB.configure(command=self.update, variable=self.include_checkbox_var)
        self.include_checkbox_var.set(True)

        tableCB_fake = self.tableComponents["fakeSingles_checkbox"]
        tableCB_fake.configure(command=self.update, variable=self.loadSinglesAsMain_var)
        self.loadSinglesAsMain_var.set(True)

        tableCB_bulk = self.tableComponents["includeStatsTableCheckbox"]
        tableCB_bulk.configure(command=self.update, variable=self.includeStatsTableCheckbox_var)
        self.includeStatsTableCheckbox_var.set(False)

    def setProgress(self, percent, speed=0.005):
        current_progress = self.progress.get()
        step_size = int((percent - current_progress) / 5)
        if step_size == 0:
            step_size = 1 if percent > current_progress else -1

        if current_progress < percent:
            for i in range(current_progress + step_size, percent + step_size, step_size):
                if i > percent:
                    i = percent
                self.progress.set(i)
                self.root.update_idletasks()
                time.sleep(speed)
        else:
            self.progress.set(percent)
            self.root.update_idletasks()

    def update(self):
        loadSinglesAsMain = self.loadSinglesAsMain_var.get()
        replaceText(self.graphComponents['textbox'], "")
        renderPuzzleImage("", self.graphComponents['imageLabel'], "", iLoveEgg=True)
        setByLatest = self.setToLatest.get()
        self.setProgress(0)
        if self.dynamic:
            self.timestamp_max = int(time.time() * 1000)
        else:
            self.autoUpdateVar.set(False)
        self.setProgress(10)
        if self.checkboxes is None:
            self.checkboxes = updateLimitCheckboxesUI(self, self.limitedCategoriesFrames,
                                                      getCategoryLimits(self.dbpath, loadSinglesAsMain,
                                                                        self.timestamp_min,
                                                                        self.timestamp_max))
            categoryFilters = getSelectedCategories(self.checkboxes)
        else:
            categoryFilters = getSelectedCategories(self.checkboxes)
            self.checkboxes = updateLimitCheckboxesUI(self, self.limitedCategoriesFrames,
                                                      getCategoryLimits(self.dbpath, loadSinglesAsMain,
                                                                        self.timestamp_min,
                                                                        self.timestamp_max),
                                                      categoryFilters)
        self.setProgress(20)
        if setByLatest:
            latestSolve = getLatestSolve(self.dbpath, self.timestamp_min, self.timestamp_max)
            if latestSolve is not None:
                setCategoriesToLatest(self.checkboxes, latestSolve)
                categoryFilters = getSelectedCategories(self.checkboxes)
        ADD_SINGLES_AS_MAIN = 'Standard' in categoryFilters["checkboxes_solve"] and loadSinglesAsMain
        skippedScrambles = getSkippedScrambles(self.dbpath, self.timestamp_min, self.timestamp_max, categoryFilters,
                                               ADD_SINGLES_AS_MAIN)
        self.setProgress(30)
        mainSolvesData, singlesData = getSolvesFromDB(self.dbpath, self.timestamp_min, self.timestamp_max,
                                                      categoryFilters,
                                                      ADD_SINGLES_AS_MAIN)
        self.setProgress(40)
        mainSolvesData = parseMainSolveData(mainSolvesData)
        singlesData = parseMainSolveData(singlesData)
        self.setProgress(50)
        skippedScrambles = parseSkippedScrambles(skippedScrambles)
        self.setProgress(60)
        mainSolvesData = fillSessionTree(self.sessionTree, mainSolvesData, self.dynamic, len(skippedScrambles),
                                         singlesData)
        self.setProgress(70)
        mainSolvesData = mainSolvesData + skippedScrambles
        manageSolvesTable(mainSolvesData, self.dbpath, self.tableComponents, categoryFilters,
                          self.include_checkbox_var.get(), self.graphComponents["textbox"],
                          self.graphComponents["imageLabel"], self.includeStatsTableCheckbox_var.get())
        setAllDatePickers(self.datePickerElements, self.timestamp_min, self.timestamp_max)
        self.setProgress(100)

    def startNewSession(self):
        toastUpdate("Starting new session...")
        self.dynamic = True
        self.setToLatest.set(True)
        self.timestamp_min = int(time.time() * 1000)
        self.update()

    def clearPresets(self):
        for key, value in self.checkboxes["checkboxes_presets"].items():
            value.set(False)

    def clearPresetsExcept(self, item):
        for key, value in self.checkboxes["checkboxes_presets"].items():
            if item != key:
                value.set(False)

    def clearCheckboxes(self):
        for group_name, group in self.checkboxes.items():
            if type(group) == list or group_name == "checkboxes_presets":
                continue
            for item_name, value in group.items():
                value.set(False)

    def setCheckboxesByPresets(self):
        presets = self.checkboxes["checkboxes_presets"]
        presets_data = self.checkboxes["presets_data"]
        if presets.get("ALL (may be laggy!)").get():
            for group in ["checkboxes_controls", "checkboxes_display", "checkboxes_solve", "checkboxes_puzzles"]:
                for checkbox in self.checkboxes[group].values():
                    checkbox.set(True)
            return
        for idx, (key, preset) in enumerate(presets.items()):
            if preset.get():
                controls_value = presets_data[idx]['controls']
                if controls_value:
                    self.checkboxes["checkboxes_controls"][controls_value].set(True)
                display_type_value = presets_data[idx]['display_type']
                if display_type_value:
                    self.checkboxes["checkboxes_display"][display_type_value].set(True)
                solve_type_value = presets_data[idx]['solve_type']
                if solve_type_value:
                    if solve_type_value == "Marathon":
                        solve_type_key_marathon = f"x{presets_data[idx]['marathon_length']} Marathon"
                        self.checkboxes["checkboxes_solve"][solve_type_key_marathon].set(True)
                    else:
                        self.checkboxes["checkboxes_solve"][solve_type_value].set(True)
                width = presets_data[idx]['width']
                height = presets_data[idx]['height']
                puzzle_key = f"{width}x{height}"
                if puzzle_key in self.checkboxes["checkboxes_puzzles"]:
                    self.checkboxes["checkboxes_puzzles"][puzzle_key].set(True)

    def updateByCheckBoxes(self):
        if self.checkboxes is None:
            self.startNewSession()
        else:
            self.clearPresets()
            self.setToLatest.set(False)
            #self.update()

    def updateByPresets(self, item):
        if self.checkboxes is None:
            self.startNewSession()
        else:
            self.clearCheckboxes()
            self.clearPresetsExcept(item)
            self.setCheckboxesByPresets()
            self.setToLatest.set(False)
            self.update()

    def regularUpdate(self):
        self.dynamic = True
        if self.checkboxes is None:
            self.startNewSession()
        else:
            customrange = self.getCustomRange()

            # Convert millisecond timestamps to minutes (discarding seconds and ms)
            millis_per_minute = 60 * 1000  # 60,000 ms in a minute

            # Floor division to get minute-level alignment
            min_start = self.timestamp_min // millis_per_minute
            min_end = self.timestamp_max // millis_per_minute
            custom_min_start = customrange[0] // millis_per_minute
            custom_min_end = customrange[1] // millis_per_minute

            if (min_start == custom_min_start and min_end == custom_min_end):
                self.update()
            else:
                self.customRangeUpdate(customrange)

    def customRangeUpdate(self, customrange):
        self.timestamp_min, self.timestamp_max = customrange
        self.dynamic = self.autoUpdateVar.get()
        self.update()

    def getCustomRange(self):
        return getPickedTimestamps(self.datePickerElements)

    def rootFocusedIn(self, event):
        if event.widget == self.root and self.autoUpdateVar.get() and was_file_changed(self.dbpath, self.lastKnownChange):
            self.lastKnownChange = os.path.getmtime(self.dbpath)
            self.regularUpdate()


def configureSessionControls(sessionControls, dbpath, limitedCategoriesFrames, root, tableComponents, graphComponents):
    session_controller = SessionController(dbpath,
                                           limitedCategoriesFrames,
                                           sessionControls["sessionTree"],
                                           sessionControls["updateProgress"],
                                           root,
                                           sessionControls["setToLatest"],
                                           tableComponents,
                                           graphComponents,
                                           sessionControls["autoUpdateVar"],
                                           sessionControls["datePickerElements"])

    sessionControls.get("updateButton").configure(command=session_controller.regularUpdate)
    root.bind("<FocusIn>", session_controller.rootFocusedIn)


def setIcon(root):
    try:
        icon_path = "sessionTrackerResources/egg.png"
        egg_image = tk.PhotoImage(file=icon_path)
        root.tk.call('wm', 'iconphoto', root._w, egg_image)
    except:
        pass


def connect(root):
    config = load_config()
    global SLIDYSIM_DEFAULT_PATH
    try:
        SLIDYSIM_DEFAULT_PATH = config.get('DEFAULTS', 'db_path')
    except configparser.NoSectionError:
        update_config('DEFAULTS', 'DB_PATH', SLIDYSIM_DEFAULT_PATH)
    dbpath = getPathFromUser(root)
    if dbpath is None:
        exit()
    SLIDYSIM_DEFAULT_PATH = dbpath
    update_config('DEFAULTS', 'DB_PATH', SLIDYSIM_DEFAULT_PATH)
    return dbpath + '/solves.db'


def run():
    locale.setlocale(locale.LC_ALL, "C")
    root = ttk.Window(size=(MY_WINDOW_WIDTH, MY_WINDOW_HEIGHT), title=MY_APP_TITLE, themename='darkly',
                      minsize=(MY_WINDOW_WIDTH, MY_WINDOW_HEIGHT), position=(50, 50))
    setIcon(root)
    if not shutil.which("slidy"):
        Messagebox.show_error(
            "Slidy-cli was not found, please put it in the folder of the script and call 'slidy' (slidy.exe)\nYou can download it from github at https://github.com/benwh1/slidy-cli/releases/tag/v0.2.0")
        exit()
    dbpath = connect(root)
    sessionControlFrame, categoryLimiterFrame, graphsFrame, solvesFrame = createFramesUI(root)
    sessionControls = createSessionControlFrameUI(sessionControlFrame, dbpath)

    limitedCategoriesFrames = createCategoryLimiterFrameUI(categoryLimiterFrame)

    tableComponents = createSolvesFrameUI(solvesFrame)
    graphComponents = createGraphsFrameUI(graphsFrame)
    configureSessionControls(sessionControls, dbpath, limitedCategoriesFrames, root, tableComponents, graphComponents)

    root.mainloop()


if __name__ == "__main__":
    run()
