
from __future__ import print_function
import random, sys

if sys.version_info[0] == 2:
    import Tkinter as tk
    import tkFileDialog
    from tkMessageBox import showwarning, askyesno, showinfo, showerror
else:
    import tkinter as tk
    from tkinter import PhotoImage
    from tkinter import filedialog as tkFileDialog
    from tkinter.messagebox import showwarning, askyesno, showinfo, showerror

import os
import pyaudio
import wave
import re
# import cPickle
import csv
import threading
from numpy import fromstring, linspace
import time
import datetime
import webbrowser
from random import shuffle
import pympi
from label import Variable
# from block import Block, BlockPart
from block import Block, BlockPart
from Chunk import Chunk
from databaseADID import Database

#from matplotlib import lines, style
# import multiprocessing
import logging

#style.use('ggplot')
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#from matplotlib.figure import Figure

import utils
import makeblocks

FOLDERS = ['./input', './labelled_data', './output_inclusion']
for FOLDER in FOLDERS:
    if not os.path.isdir(FOLDER):
        os.mkdir(FOLDER)

# class MyProcess(multiprocessing.Process):
#
#     def __init__(self):
#         multiprocessing.Process.__init__(self)
#         self.exit = multiprocessing.Event()
#
#     def run(self):
#         while not self.exit.is_set():
#             pass
#         print "You exited!"
#
#     def shutdown(self):
#         print "Shutdown initiated"
#         self.exit.set()
logging.basicConfig(filename='log_file.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.info("Started Program")


class Convolabel(object):

    def __init__(self, master):

        self.root = master
        self.root.resizable(width=False, height=False)
        self.root.title('Selection Task')
        self.root.protocol('WM_DELETE_WINDOW',
                           self.check_before_exit)  # register pressing the x button as event and call the corresponding function

        self.eafob = None
        self.start_time=None
        self.label_dict = dict()
        self.is_playing = False
        self.play_thread = None
        program_path = os.getcwd()
        self.chunks_path = os.path.join(program_path, 'output_inclusion')
        self.data = Database(program_path)
        self._data_is_saved = True
        self.current_rec = None
        self.current_chunk = None
        self.player = None
        self.stream = None
        self.current_chunk_obj = None
        self.current_block = None
        self.current_part = None
        
        self.curr_part_len = 0.00

        self.frame = tk.Frame(root)  # , bd = 1, relief = 'sunken')
        self.frame.grid(row=0, column=0, sticky='wns', padx=(30, 30), pady=30)

        # Menu window
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.submenu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Menu', menu=self.submenu)
        # self.submenu.add_command(label='Make blocks', command=self.make_blocks)
        self.submenu.add_command(label='Save data', command=self.save)
        self.submenu.add_command(label='Export to csv', command=self.export)
        # self.submenu.add_command(label='Set ADS sample', command=lambda self=self, kind='ads': self.set_sample(kind))
        # self.submenu.add_command(label='Set CDS sample', command=lambda self=self, kind='cds': self.set_sample(kind))
        readme_link = 'https://github.com/BLLManitoba/NonnativeAD_ID//tree/master/src/app/convolabel#how-it-works'
        self.submenu.add_command(label='Session info', command=self.show_stats)
        self.submenu.add_command(label='Help', command=lambda: webbrowser.open_new(readme_link))

        # Recordings list box
        tk.Label(self.frame, text='Recordings:').grid(row=2, column=0, padx=0, pady=0, sticky='W')
        self.recs_list = tk.Listbox(self.frame, width=20, height=15, exportselection=False, relief=tk.FLAT)
        self.recs_list.bind('<<ListboxSelect>>', self.update_current_rec)
        self.recs_scrollbar = tk.Scrollbar(self.frame, orient='vertical', command=self.recs_list.yview)
        self.recs_list.config(yscrollcommand=self.recs_scrollbar.set)
        self.recs_scrollbar.grid(row=3, column=0, rowspan=10, sticky='NSE')
        self.recs_list.grid(row=3, column=0, rowspan=10, padx=(0, 5), pady=0, sticky='WE')

        # # Chunks list box
        tk.Label(self.frame, text='Chunks:').grid(row=2, column=1, padx=5, pady=0, sticky='W')
        self.chunks_list = tk.Listbox(self.frame, width=20, height=15, exportselection=False, relief=tk.FLAT)
        self.chunks_list.bind('<<ListboxSelect>>', self.update_current_chunks)
        self.chunks_list.bind('<space>', self.play)
        self.chunks_scrollbar = tk.Scrollbar(self.frame, orient='vertical', command=self.chunks_list.yview)
        self.chunks_list.config(yscrollcommand=self.chunks_scrollbar.set)
        self.chunks_scrollbar.grid(row=3, column=1, rowspan=10, sticky='NSE')
        self.chunks_list.grid(row=3, column=1, rowspan=10, padx=(5, 5), pady=0, sticky='WE')

        # # Blocks list box
        tk.Label(self.frame, text='Tiers:').grid(row=2, column=2, padx=5, pady=0, sticky='W')
        self.blocks_list = tk.Listbox(self.frame, width=20, height=15, exportselection=False, relief=tk.FLAT)
        self.blocks_list.bind('<<ListboxSelect>>', self.update_current_block)
        self.blocks_list.bind('<space>', self.play)
        self.blocks_scrollbar = tk.Scrollbar(self.frame, orient='vertical', command=self.blocks_list.yview)
        self.blocks_list.config(yscrollcommand=self.blocks_scrollbar.set)
        self.blocks_scrollbar.grid(row=3, column=2, rowspan=10, sticky='NSE')
        self.blocks_list.grid(row=3, column=2, rowspan=10, padx=(5, 5), pady=0, sticky='WE')

        #
        # # Parts list box
        tk.Label(self.frame, text='Parts:').grid(row=2, column=3, sticky='W', padx=5)
        self.parts_list = tk.Listbox(self.frame, width=20, height=15, exportselection=False, relief=tk.FLAT)
        self.parts_list.bind('<<ListboxSelect>>', self.update_current_part)
		
        self.parts_list.bind('<space>', self.play)
        self.parts_list.bind('1', self.change_confidence1)
        self.parts_list.bind('2', self.change_confidence2)
        self.parts_list.bind('3', self.change_confidence3)
        self.parts_list.bind('4', self.change_confidence4)
        self.parts_list.bind('`', self.change_confidence0)
        self.parts_scrollbar = tk.Scrollbar(self.frame, orient='vertical', command=self.parts_list.yview)
        self.parts_list.configure(yscrollcommand=self.parts_scrollbar.set)
        self.parts_scrollbar.grid(row=3, column=3, rowspan=10, sticky='NSE')
        self.parts_list.grid(row=3, column=3, padx=(5, 10), rowspan=10, sticky='WE')

        # Coder name entry
        self.coder_name = tk.StringVar()
        self.coder_name.set('--> Coder\'s name <--')

        #self.coder_name.set('test')
        self.coder_name_entry = tk.Entry(self.frame, justify=tk.CENTER, textvariable=self.coder_name, relief=tk.FLAT)
        self.coder_name_entry.grid(row=0, column=0, padx=0, pady=(0, 20))
        self.coder_name_entry.bind('<Return>', self.load_recs)

        # Buttons
        self.load_data_button = tk.Button(
            self.frame,
            text='Load',
            command=self.load_recs,
            height=1,
            width=10,
            relief=tk.GROOVE).grid(row=4, column=4, padx=20)
        self.play_button = tk.Button(
            self.frame,
            command=self.play,
            text='Play',
            height=1,
            width=10,
            relief=tk.GROOVE)

        # self.play_button.bind('<space>', lambda event, self=self: self.play_button.configure(text='Play'))
        self.play_button.grid(row=5, column=4, padx=0)

        self.play_button.bind('<space>', self.play)

        #self.root.bind('e', self.select_ads)
        #self.root.bind('i', self.select_cds)
        self.select_ads_cds = tk.IntVar(value=-1)
        tk.Radiobutton(
            self.frame,
            text='Child-Directed Speech',
            variable=self.select_ads_cds,
            value=0
        ).grid(row=6, column=4, padx=50, sticky = 'W')
        tk.Radiobutton(
            self.frame,
            variable=self.select_ads_cds,
            text='Adult-Directed Speech',
            value=1
        ).grid(row=7, column=4, padx=50, sticky = 'W')
        tk.Radiobutton(
            self.frame,
            variable=self.select_ads_cds,
            text='Junk',
            value=2
        ).grid(row=8, column=4, padx=0)
        self.confidence_level = tk.DoubleVar()
        self.scale_tk = tk.Scale(self.frame, from_=0, to=4, orient=tk.HORIZONTAL, label='Confidence',
                                 digits=2, variable=self.confidence_level,
                                 relief=tk.GROOVE, ).grid(row=9, column=4, padx=0)


        # self.submit_button = tk.Button(
        #     self.frame,
        #     text='Submit',
        #     command=self.submit,
        #     height=1,
        #     width=10,
        #     relief=tk.GROOVE).grid(row=10, column=4, padx=0)

        #lower part of the UI with all the option button
        #tk.Label(self.frame,
         #        text='On a scale from 1 to 5, select the options that best reflect how the speaker sounded:',
          #       font='Arial 15 bold').grid(row=22, column=0, columnspan=7, sticky='W', pady=0, padx=0)

        #self.radio_select_happy = tk.IntVar(value=-1)
        #tk.Radiobutton(
        #    self.frame,
        #    text='Neutral',
        #    variable=self.radio_select_happy,
        #    value=0
        #).grid(row=23, column=0, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_happy,
        #    text='Somewhat Happy',
        #    value=1
        #).grid(row=24, column=0, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_happy,
        #    text='Happy',
        #    value=2
        #).grid(row=25, column=0, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_happy,
        #    text='Very Happy',
        #    value=3
        #).grid(row=26, column=0, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_happy,
        #    text='Extremely Happy',
        #    value=4
        #).grid(row=27, column=0, padx=0, sticky='W')

        #self.radio_select_soothing = tk.IntVar(value=-1)
        #tk.Radiobutton(
        #    self.frame,
        #    text='Neutral',
        #    variable=self.radio_select_soothing,
        #    value=0
        #).grid(row=23, column=1, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_soothing,
        #    text='Somewhat Soothing',
        #    value=1
        #).grid(row=24, column=1, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_soothing,
        #    text='Soothing',
        #    value=2
        #).grid(row=25, column=1, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_soothing,
        #    text='Very Soothing',
        #    value=3
        #).grid(row=26, column=1, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_soothing,
        #    text='Extremely Soothing',
        #    value=4
        #).grid(row=27, column=1, padx=0, sticky='W')

#        self.radio_select_loving = tk.IntVar(value=-1)
 #       tk.Radiobutton(
  #          self.frame,
   #         text='Neutral',
    #        variable=self.radio_select_loving,
     #       value=0
      #  ).grid(row=23, column=2, padx=0, sticky='W')
       # tk.Radiobutton(
        #    self.frame,
         #   variable=self.radio_select_loving,
          #  text='Somewhat Loving',
           # value=1
        #).grid(row=24, column=2, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_loving,
        #    text='Loving',
        #    value=2
        #).grid(row=25, column=2, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_loving,
        #    text='Very Loving',
        #    value=3
        #).grid(row=26, column=2, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_loving,
        #    text='Extremely Loving',
        #    value=4
        #).grid(row=27, column=2, padx=0, sticky='W')

        #self.radio_select_excited = tk.IntVar(value=-1)
        #tk.Radiobutton(
        #    self.frame,
        #    text='Neutral',
        #    variable=self.radio_select_excited,
        #    value=0
        #).grid(row=23, column=3, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_excited,
        #    text='Somewhat Excited',
        #    value=1
        #).grid(row=24, column=3, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_excited,
        #    text='Excited',
        #    value=2
        #).grid(row=25, column=3, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_excited,
        #    text='Very Excited',
        #    value=3
        #).grid(row=26, column=3, padx=0, sticky='W')
        #tk.Radiobutton(
        #    self.frame,
        #    variable=self.radio_select_excited,
        #    text='Extremely Excited',
        #    value=4
        #).grid(row=27, column=3, padx=0, sticky='W')
		
		# Comments box
        tk.Label(self.frame, text='Comments:').grid(row=14, column=0, sticky='W', pady=5, padx=0)
        self.comments = tk.Text(self.frame, height = 10, width = 40, state = 'disabled', relief = tk.FLAT)
        self.comments.grid(row = 15, column = 0, columnspan = 4, sticky = 'W', padx = 0, pady = 0)

        # keyboard bind of CTRL+S for saving the current inputs
        self.root.bind('<Control-s>', self.save2)
        self.submit_button = tk.Button(
            self.frame,
            text='Submit',
            font='Arial 15 bold',
            command=self.submit,
            height=1,
            width=10,
            relief=tk.GROOVE).grid(row=10, column=4, padx=0, pady=5)


        # Status bar
        self.status_bar_frame = tk.Frame(self.root)
        self.status_bar_frame.grid(row=2, column=0, sticky='we', padx=20, pady=10)
        self.bar = tk.StringVar()
        self.status_bar = tk.Label(self.status_bar_frame, textvariable=self.bar)
        self.status_bar.grid(row=0, column=0)

        # Waveform graph
        # self.graph_frame = tk.Frame(self.root)  # , bd = 1, relief = 'sunken')
        # self.graph_frame.grid(row=0, column=1, sticky='wns', pady=60)
        # self.fig = Figure(figsize=(5, 5), dpi=60)
        # self.ax = self.fig.add_subplot(111)
        # self.wave_line, = self.ax.plot([], [], color=[0.2, 0.2, 0.2])
        # self.ax.set_ylim(-1, 1)
        # self.ax.set_yticks([self.ax.get_ylim()[0] + i * 0.5 for i in range(5)])
        # self.fig.patch.set_visible(False)
        # self.ax.set_xlabel('Time (s)')
        # self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        # self.canvas.get_tk_widget().grid(row=1, column=0)

        # Session information
        self.session_stats = {
            'start_time': time.time(),
            'labelled_sec': 0,
            'labelled_parts': 0,
            'labelled_blocks': 0
        }

    def show_stats(self):

        text = '''Elapsed time:\t{}\nLabeled blocks:\t{}\nLabeled parts:\t{}\nLabelled time:\t{}\n\n1 min of audio = {} min of labelling\n{} blocks/min'''

        et = datetime.timedelta(seconds=time.time() - self.session_stats['start_time'])
        blocks_sum = self.session_stats['labelled_blocks']
        parts_sum = self.session_stats['labelled_parts']
        time_sum = datetime.timedelta(seconds=self.session_stats['labelled_sec'])
        if time_sum.seconds > 0:
            ratio_sec = round(float(et.seconds) / time_sum.seconds, 2)
            block_per_min = round(blocks_sum * 60.0 / et.seconds, 2)
        else:
            ratio_sec = 0
            block_per_min = 0

        et = str(et).split('.')[0]  # remove microseconds
        time_sum = str(time_sum).split('.')[0]

        showinfo('Session info', text.format(et, blocks_sum, parts_sum, time_sum, ratio_sec, block_per_min))

    def show_block_length(self, event):
        ''' Executes when hover over the play button '''
        if self.current_part:
            assert self.current_block
            t = self.current_block.bytes2sec(self.current_part.bytes)
            self.play_button.configure(text='{:.2f} s'.format(t))
        elif self.current_block:
            t = self.current_block.seconds
            self.play_button.configure(text='{:.2f} s'.format(t))
        elif self.current_chunk_obj:
            t = self.current_chunk_obj.seconds
            self.play_button.configure(text='{:.2f} s'.format(t))

    def data_is_saved(self, value=True):
        self._data_is_saved = value
        if value:
            self.root.title('Mother Affect Labeling ')
        else:
            self.root.title('Mother Affect Labeling *')

    def set_sample(self, kind):
        ''' Defines the path to a sample IDS/ADS clip. kind argument specifies ADS or IDS'''
        if self.current_rec == '':
            showwarning('No recording selected',
                        'Select a recording from the list first. The sample will be attached to that recording')
            return
        file = tkFileDialog.askopenfilename(filetypes=[('wave files', '.wav')])
        if not file:
            return
        file = os.path.abspath(file)
        # coder = self.coder_name.get()
        rec = self.current_rec

        if not self.data.has_key(rec):
            self.data.db[rec] = {}

        if kind == 'ads':
            self.data.db[rec]['_ads_sample'] = file
            self.ads_sample_button.configure(state='normal')
        elif kind == 'cds':
            self.data.db[rec]['_cds_sample'] = file
            self.cds_sample_button.configure(state='normal')

        self.data_is_saved(False)

    def play_sample(self, kind):

        coder = self.coder_name.get()
        rec = self.current_rec

        if kind == 'ads':
            f = wave.open(self.data.db[rec]['_ads_sample'])
        elif kind == 'cds':
            f = wave.open(self.data.db[rec]['_cds_sample'])

        audio = f.readframes(-1)
        n_channels, sample_width, sample_rate, _, _, _ = f.getparams()
        f.close()

        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(sample_width),
                        channels=n_channels,
                        rate=sample_rate,
                        output=True)

        stream.write(audio)
        stream.stop_stream()
        stream.close()
        p.terminate()

    #def junk_selected(self):
     #   if self.labels['junk'].get() == 1:
      #      for label in self.labels.values():
       #         if label.name == 'junk': continue
        #        label.set(0)
         #       label.set_visible(False)
        #else:
         #   self.reset_labels()
          #  self.allow_initial_entries(True)

    def make_blocks(self):

        ans = askyesno('Making blocks', 'Click yes to start processing blocks, no to cancel')
        if ans == 0:
            return

        to_input_data = os.path.join(os.getcwd(), 'input')
        folders = os.listdir(to_input_data)
        if folders == []:
            showwarning('No blocks are found', 'The input directory is empty!')
            return

        for folder in folders:
            if folder.startswith('.'):
                continue
            files = os.listdir(os.path.join(to_input_data, folder))
            # if not any(file.endswith('.cha') for file in files):
            #    showwarning('Files missing', 'No .cha file for {}'.format(folder))
            #    return
            if not any(file.endswith('.wav') for file in files):
                showwarning('Files missing', 'No .wav file for {}'.format(folder))
                return

            wavfile = [file for file in files if file.endswith('.wav')]
            # chafile = [file for file in files if file.endswith('.cha')]

            # if wavfile[0].strip('.wav') != chafile[0].strip('.cha'):
            #    showwarning('Files issue', 'cha and wav file names do not match for {}'.format(folder))
            #    return

        t0 = time.time()
        makeblocks.main('input', 'output')
        t = (time.time() - t0) / 60

        showinfo('All done!', 'Processed {} recordings in {:.3f} min'.format(len(folders), t))

        self.load_recs()

    def load_recs(self, event=None):

        coder = self.coder_name.get()

        if coder == '--> Coder\'s name <--':
            showwarning('Coder\'s name', 'Please enter your name')
            return

        self.data.set_coder(coder)
        coders = [name.replace('.db','') for name in os.listdir(self.data.db_path) if name.endswith('.db')]
        print(coders)
        if coder in coders:
            self.data.load_data()
        else:
            ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
            if ans == 0:
                return

        self.data.connect_sql()
        self.data.create_table_sarah()

        # Remove all recordings and blocks from the list boxes
        # if self.recs_list.get(0, tk.END) != ():
        self.recs_list.delete(0, tk.END)
        self.chunks_list.delete(0, tk.END)
        self.parts_list.delete(0, tk.END)
        self.blocks_list.delete(0, tk.END)
        # Recs are the recordings (e.g C208_20150101). Every folder in the data path is considered a rec
        to_input_data = os.path.join(os.getcwd(), 'output_inclusion')
        files = os.listdir(os.path.join(to_input_data, to_input_data))
        # names = [file for file in files if file.endswith('.wav')]
        names = files
        try:
            regexp = re.compile('\d+')
            names = sorted(names, key=lambda x: int(regexp.search(x).group()))
        except:
            names = sorted(names, key=str)

        for name in names:
            self.recs_list.insert(tk.END, name.split(".wav")[0])
        logging.info("loaded recs for " + coder)
		
    # unused
    def load_recs2(self):

        coder = self.coder_name.get()

        if coder == '--> Coder\'s name <--':
            showwarning('Coder\'s name', 'Please enter your name')
            return

        self.data.set_coder(coder)
        coders = [name.strip('.db') for name in os.listdir(self.data.db_path) if name.endswith('.db')]

        if coder in coders:
            self.data.load_data()
        else:
            ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
            if ans == 0:
                return

        self.data.connect_sql()
        self.data.create_table_sarah()

        # Remove all recordings and blocks from the list boxes
        # if self.recs_list.get(0, tk.END) != ():
        self.recs_list.delete(0, tk.END)
        # if self.blocks_list.get(0, tk.END) != ():
        self.blocks_list.delete(0, tk.END)

        # Recs are the recordings (e.g C208_20150101). Every folder in the data path is considered a rec
        # names = [name for name in os.listdir(self.data.audio_path) if os.path.isdir(os.path.join( self.data.audio_path, name ))]
        to_input_data = os.path.join(os.getcwd(), 'input')
        files = os.listdir(os.path.join(to_input_data, to_input_data))
        names = [file for file in files if file.endswith('.wav')]
        try:
            regexp = re.compile('\d+')
            names = sorted(names, key=lambda x: int(regexp.search(x).group()))
        except:
            names = sorted(names, key=str)

        for name in names:
            self.blocks_list.insert(tk.END, name)

    def update_current_rec(self, event):
        ''' Executes on selection from the recording list box. Recording = rec here '''

        if self.recs_list.get(0,
                              tk.END) == ():  # this is to prevent an error which pops up if user clicks on an empty list
            return
        self.current_block = None
        self.current_part = None
        self.current_chunk = None

        w = event.widget
        self.current_rec = w.get(int(w.curselection()[0]))

        # Plot the emty line = clear the graph
        # self.wave_line.set_data([], [])
        # self.canvas.draw()
		
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'normal')
		
		#reset radiobuttons
        self.select_ads_cds.set(value = -1)
        #self.radio_select_happy.set(value = -1)
        #self.radio_select_soothing.set(value = -1)
        #self.radio_select_loving.set(value = -1)
        #self.radio_select_excited.set(value = -1)
        
		#reset confidence noise slider
        self.confidence_level.set(value = 0)

        ####
        index = int(w.curselection()[0])
        name = w.get(index)
        # path = os.path.join(self.data.audio_path, self.current_rec)

        self.eafob = pympi.Elan.Eaf(os.path.join(self.data.input_path, self.current_rec + ".eaf"))

        # tier_names = self.eafob.get_tier_names()
        # regex= re.compile("FA*|MA*")
        # tier_names = list(filter(regex.match,tier_names))
        # print(tier_names)
        _, dirs, _ = os.walk(os.path.join(self.chunks_path, name)).next()
        try:
            regexp = re.compile('\d+')
            dirs = sorted(dirs, key=lambda x: int(regexp.search(x).group()))
        except:
            dirs = sorted(dirs, key=str)

        # shuffle(dirs)
        self.chunks_list.delete(0, tk.END)
        self.parts_list.delete(0, tk.END)
        self.blocks_list.delete(0, tk.END)
        for chunk_name in dirs:
            self.chunks_list.insert(tk.END, chunk_name)
            # fix all chunks later
            # if self.data.has_key(self.current_rec, chunk_name):
            #     self.chunks_list.itemconfig(tk.END, foreground = 'gray')

        # labelled = self.data.total_labelled(self.current_rec)
        # total = 1
        # self.bar.set('{:.0f}% of blocks are labelled for this recording'.format(100 * labelled / total))

    def select_ads(self, *event):
        self.radio_select_value.set(1)

    def select_cds(self, *event):
        self.radio_select_value.set(0)
        
    #def select_edit(self, *event):
     #   self.radio_select_value.set(2)

    def select_junk(self, *event):
        self.radio_select_value.set(2)

    def change_confidence1(self, *event):
        self.confidence_level.set(1)
    def change_confidence2(self, *event):
        self.confidence_level.set(2)
    def change_confidence3(self, *event):
        self.confidence_level.set(3)
    def change_confidence4(self, *event):
        self.confidence_level.set(4)
    def change_confidence0(self, *event):
        self.confidence_level.set(0)

    def load_labels(self, dic):
        #print(dic)
        annotator_label = -1
        if dic['cds_ads'] == 'cds':
            annotator_label = 0
        elif dic['cds_ads'] == 'ads':
            annotator_label = 1
        elif dic['cds_ads'] == 'junk':
            annotator_label = 2
        
        
        self.select_ads_cds.set(annotator_label)
        self.select_ads_cds.set(annotator_label)
        self.confidence_level.set(dic['confidence_level'])
        
        #self.radio_select_happy.set(dic['sounded_happy'])
        #self.radio_select_soothing.set(dic['sounded_soothing'])
        #self.radio_select_loving.set(dic['sounded_loving'])
        #self.radio_select_excited.set(dic['sounded_excited'])
        #self.comments.set(dic['comments'])
        # for key, value in self.labels.items():
        #     value.set(dic[key])
        #
        #if self.labels['junk'].get() == 2:
         #   self.junk_selected()
        #
        self.comments.delete(1.0, tk.END)
        self.comments.insert(tk.END, dic['comments'])
        self.comments.configure(state='normal')

        self.bar.set('Labeled at {}'.format(dic['insertion_time']))

    def reset_labels(self):
        return
        # for label in self.labels.values():
        #     label.set(0)
        # self.comments.delete(1.0, tk.END)

    def allow_initial_entries(self, value=True):
        return
        # self.labels['ads'].set_visible(value)
        # self.labels['cds'].set_visible(value)
        # self.labels['ocs'].set_visible(value)
        # self.labels['sensitive'].set_visible(value)
        # self.labels['other_langue'].set_visible(value)
        # self.labels['junk'].set_visible(value)
        # if value:
        #     self.comments.configure(state='normal')
        # else:
        #     self.comments.configure(state='disabled')

    def fetch_labels(self):
        x = {key: self.labels[key].get() for key in self.labels.keys()}
        x['comments'] = self.comments.get(1.0, tk.END).strip()
        return x

    def check_labels(self):
        try:
            for label in self.labels.values():
                if label.get() not in range(5):
                    return False
        except ValueError:
            return False

        if self.labels['cds'].get() + self.labels['ads'].get() + self.labels['ocs'].get() > 4:
            return False
        elif self.labels['cds'].get() != 0 and self.labels['cds'].children_sum() != 4:
            return False
        elif self.labels['mother'].get() != 0 and self.labels['mother'].children_sum() != 4:
            return False
        elif self.labels['target_child'].get() != 0 and self.labels['target_child'].children_sum() != 4:
            return False

        return True

    def update_current_chunks(self, event):
        if self.chunks_list.get(0,
                                tk.END) == ():  # this is to prevent an error which pops up if user clicks on an empty blocks list
            return
        self.blocks_list.delete(0, 'end')
        self.current_block = None
        self.current_part = None

        w = event.widget
		
		#Reset all GUI buttons to blank
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'normal')
		
		#reset radiobuttons
        self.select_ads_cds.set(value = -1)
        #self.radio_select_happy.set(value = -1)
        #self.radio_select_soothing.set(value = -1)
        #self.radio_select_loving.set(value = -1)
        #self.radio_select_excited.set(value = -1)
        
		#reset confidence noise slider
        self.confidence_level.set(value = 0)
		

        ####
        index = int(w.curselection()[0])
        name = w.get(index)

        self.current_chunk = w.get(int(w.curselection()[0]))
        path = os.path.join(self.chunks_path, self.current_rec, self.current_chunk)

        self.current_chunk_obj = Chunk(path, name, index)

        # Plot the emty line = clear the graph
        # self.wave_line.set_data([], [])
        # self.canvas.draw()

        # path = os.path.join(self.data.audio_path, self.current_rec)

        # self.eafob = pympi.Elan.Eaf( os.path.join(self.data.input_path, self.current_rec+".eaf"))

        # tier_names = self.eafob.get_tier_names()
        # regex= re.compile("FA*|MA*")
        # tier_names = list(filter(regex.match,tier_names))
        # print(tier_names)
        _, dirs, _ = os.walk(os.path.join(self.chunks_path, self.current_rec, name)).next()
        dirs = sorted(dirs)

        self.blocks_list.delete(0, tk.END)
        self.parts_list.delete(0, tk.END)
        for tier_name in dirs:
            self.blocks_list.insert(tk.END, tier_name)
            if self.data.has_key(self.current_rec, self.current_chunk, name):
                self.blocks_list.itemconfig(tk.END, foreground='gray')

    def update_current_block(self, event):
        ''' Executes on block selection from the list box '''

        if self.blocks_list.get(0,
                                tk.END) == ():  # this is to prevent an error which pops up if user clicks on an empty blocks list
            return
        self.parts_list.delete(0, 'end')
        w = event.widget
		
		#Reset all GUI buttons to blank
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'normal')
		
		#reset radiobuttons
        self.select_ads_cds.set(value = -1)
        #self.radio_select_happy.set(value = -1)
        #self.radio_select_soothing.set(value = -1)
        #self.radio_select_loving.set(value = -1)
        #self.radio_select_excited.set(value = -1)
        
		#reset confidence noise slider
        self.confidence_level.set(value = 0)
		
        index = int(w.curselection()[0])
        name = w.get(index)
        path = os.path.join(self.chunks_path, self.current_rec, self.current_chunk, name)

        self.current_block = Block(path, name, index)

        self.bar.set('')
        self.current_part = None
        self.parts_list.delete(0, tk.END)

        rec = self.current_rec
        block = self.current_block.name

        # List the parts for this block
        _, _, files = os.walk(os.path.join(self.chunks_path, self.current_rec, self.current_chunk, name)).next()
        files = sorted(files, key=str)

        for tier_name in files:
            parts_name = tier_name.split('_')[0] + "-" + tier_name.split('_')[1]
            self.label_dict[parts_name] = (tier_name.split('_')[2]).replace(".wav", "")
            self.parts_list.insert(tk.END, parts_name)
            if self.data.has_key(rec, self.current_chunk, block, parts_name):
                self.parts_list.itemconfig(tk.END, foreground='gray')

    def update_current_part(self, event):

        if self.parts_list.get(0,
                               tk.END) == ():  # this is to prevent an error which pops up if user clicks on an empty blocks list
            return

        w = event.widget
		
		#Reset all GUI buttons to blank
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'normal')
		
		#reset radiobuttons
        self.select_ads_cds.set(value = -1)
        #self.radio_select_happy.set(value = -1)
        #self.radio_select_soothing.set(value = -1)
        #self.radio_select_loving.set(value = -1)
        #self.radio_select_excited.set(value = -1)
        
		#reset confidence noise slider
        self.confidence_level.set(value = 0)
		
        index = int(w.curselection()[0])
        name = w.get(index)
        # length = self.current_block.parts_length_list[index]
        # length = int(name.split('-')[1])-int(name.split('-')[0])

        self.current_part = BlockPart(name, index)

        rec = self.current_rec
        block = self.current_block.name
        try:
            #print('loading labels')
            dic = self.data.db[rec][self.current_chunk][block][name]
            self.load_labels(dic)
        except:
            #print(str(e))
            self.reset_labels()
            self.bar.set('')
        self.allow_initial_entries(True)
        self.start_time = datetime.datetime.now()
        
        audio_file = self.current_block.clips[self.current_part.index]
        wf = wave.open(audio_file, 'rb')
        frames = wf.getnframes()
        rate = wf.getframerate()
        self.curr_part_len = frames/float(rate)
        print("length of current part is: " , self.curr_part_len)
    # def callback(self,frame_count,time_info,status):
    #     data = wf
    def play_audio(self, is_playing):
        # return

        try:
            self.player = pyaudio.PyAudio()
            if self.current_part:
                # x0=self.current_part.start
                # xend = self.current_part.end
                audio_file = self.current_block.clips[self.current_part.index]
                wf = wave.open(audio_file, 'rb')
                self.stream = self.player.open(
                    format=self.player.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
                chunk = 1024  # samples to access on every iteration
                # x1 = x0 + chunk  #
                data = wf.readframes(chunk)
                while data != '':
                    self.stream.write(data)
                    data = wf.readframes(chunk)
                self.stream.stop_stream()
                self.stream.close()
            elif self.current_chunk_obj:
                print(self.current_chunk_obj.clips)
                for clips in self.current_chunk_obj.clips:
                    if not self.is_playing or not is_playing:
                        break
                    wf = wave.open(clips, 'rb')
                    self.stream = self.player.open(
                        format=self.player.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
                    chunk = 1024  # samples to access on every iteration
                    # x1 = x0 + chunk  #
                    data = wf.readframes(chunk)
                    while data != '':
                        self.stream.write(data)
                        data = wf.readframes(chunk)
                    self.stream.stop_stream()
                    self.stream.close()

            self.player.terminate()
            self.is_playing = False
            # self.play_button.configure(text='Play')
        except:
            logging.error('Cannot play audio')

    def play(self, *event):

        ''' Plays selected block '''

        if self.current_chunk is None:
            showwarning('Chunk error', 'Choose a Chunk')
            return

        if not self.is_playing:
            # if self.current_part is None:
            #     self.is_playing=True
            self.is_playing = True
            self.play_thread = threading.Thread(target=self.play_audio, args=(self.is_playing,))
            # self.play_thread= multiprocessing.Process(target=self.play_audio,args=(self.is_playing,))
            self.play_thread.start()
            if not self.current_part:
                self.play_button.configure(text='Pause')
        else:
            # self.player.terminate()

            # self.play_thread =None

            self.is_playing = False
            self.play_thread.join()
            self.play_button.configure(text='Play')
            # self.stream.stop_stream()
            # self.stream.close()
            # self.player.terminate()
            
    def check_values(self):
        if self.current_part is None:
            showwarning('Part error', 'Choose the part')
            return False
        if self.select_ads_cds.get() <0:
            showerror('Select Number Of Speakers', 'Choose either One Speaker or Multiple Speakers.')
            return False
        if self.confidence_level.get() <0:
            showerror('Select Confidence', 'Choose any value for your confidence in your ratings.')
            return False
        #if self.radio_select_happy.get() <0:
        #    showerror('Select Happiness', 'Choose any value from 1-5 for happiness.')
        #    return False
        #if self.radio_select_soothing.get() <0:
        #    showerror('Select Soothing', 'Choose any value from 1-5 for soothingness.')
        #    return False
        #if self.radio_select_loving.get() <0:
        #    showerror('Select Loving', 'Choose any value from 1-5 for lovingness.')
        #    return False
        #if self.radio_select_excited.get() <0:
        #    showerror('Select Excited', 'Choose any value from 1-5 for excitedness.')
        #    return False
        

        return True
    def submit(self, event=None):

        if self.check_values() is False:
            return

        # correct = self.check_labels()
        # if not correct:
        #     showwarning('Labels issue', 'Please check the labels')
        #     return
        #annotator_label = 'ads'
        if self.select_ads_cds.get() == 0:
            annotator_label='cds'
        elif self.select_ads_cds.get() == 1:
            annotator_label = 'ads'
        #elif self.select_ads_cds.get() == 2:
		 #   annotator_label = 'edit_file'
        to_add =dict()# self.fetch_labels()
        to_add['insertion_time'] = time.strftime('%H:%M:%S %d%b%Y')
        to_add['cds_ads']=annotator_label
        to_add['confidence_level'] = int(self.confidence_level.get())
        #to_add['sounded_happy'] = self.radio_select_happy.get()
        #to_add['sounded_soothing'] = self.radio_select_soothing.get()
        #to_add['sounded_loving'] = self.radio_select_loving.get()
        #to_add['sounded_excited'] = self.radio_select_excited.get()
        #to_add['sounded_loving'] = self.radio_select_loving.get()
        #to_add['sounded_exagg'] = self.radio_select_exaggerated.get()
        #to_add['sounded_clear_people'] = self.radio_select_clear_people.get()
        to_add['duration'] = str((datetime.datetime.now()-self.start_time).seconds)
        to_add['original_label']=self.label_dict[self.current_part.name]
        to_add['comments'] = self.comments.get(1.0, tk.END).strip()

        rec = self.current_rec
        part = self.current_part.name
        block = self.current_block.name
        chunk  = self.current_chunk
        
        to_add['part_length'] = self.curr_part_len
        # part='whole'
        #to_add['part_length'] = self.current_part.end-self.current_part.start
        # if self.current_part:

        # length = self.current_block.bytes2sec(self.current_part.bytes)
        # self.parts_list.itemconfig(self.current_part.index, foreground='gray')
        # self.parts_list.focus_set()

        # else:
        #     part = 'whole'
        # length = self.current_block.seconds
        self.parts_list.itemconfig(self.current_part.index, foreground='gray')
        self.session_stats['labelled_parts'] += 1
        self.parts_list.focus_set()

        # to_add['length'] = length
        self.data.submit_labels_sarah(rec, chunk, block, part, to_add)
        self.bar.set('Labels submitted!')
        self.data_is_saved(False)

        self.session_stats['labelled_sec'] += to_add['part_length']

        if self.current_part:
            if len(self.data.db[rec]) == self.parts_list.size():
                self.recs_list.itemconfig(self.current_rec_index, foreground='gray')
                self.session_stats['labelled_rec'] += 1
        logging.info("submitted part "+self.current_part.name+" of rec  "+self.current_rec)
        #autosave with submit
        self.save()

    def save2(self, event):
        ''' Loads the data file, updates the current data, saves the file on the hard drive '''

        self.data.save_data()

        self.bar.set(str(self.session_stats['labelled_parts']) + 'parts are saved!')
        self.data_is_saved(True)

    def save(self):
        ''' Loads the data file, updates the current data, saves the file on the hard drive '''

        self.data.save_data()

        self.bar.set('Data is saved!')
        logging.info(str(self.session_stats) + ' saved.')
        self.data_is_saved(True)

    def export(self):
        ''' Exports the current state of data to csv file. All coders are included '''

        output = tkFileDialog.asksaveasfilename(filetypes=[('Comma-separated file', '.csv')], initialfile='data.csv')
        if output == '':
            return

        d = utils.merge_coders_data(self.data.db_path)

        with open(output, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Date coded', 'Coder', 'Recording', 'Chunk', 'Block', 'Part', 'Length (ms)',
                             'cds_ads',
                             'confidence_level',
                             'Original Label',
                             'Duration',
							 'Comments'])
            for coder_name, coder in d.items():
                for rec_name, rec in coder.items():
                    for chunk_name,chunk in rec.items():
                        for block_name, block in chunk.items():
                            if block_name.startswith('_'): continue  # skip the sample clips
                            for part_name, part in block.items():
                                block_part = '-'.join([block_name, part_name])
                                row = [
                                        part['insertion_time'],
                                        coder_name,
                                        rec_name,chunk_name,
                                        block_name,
                                        part_name,
                                        part['part_length'],
                                        part['cds_ads'],
                                        part['confidence_level'],
                                        part['original_label'] if len(part['original_label'])==1 else part['original_label'][1],
                                        part['duration'],
                                        part['comments'] if part['comments'] != "" else "None",
                                        ]
                                writer.writerow(row)

        self.bar.set('All done!')

    def check_before_exit(self):
        ''' Executes on pressing the 'x' button '''

        if not self._data_is_saved:
            ans = askyesno('Data is not saved', 'Save the data before leaving?')
            if ans == 1:
                self.save()

        self.show_stats()

        self.data.close_sql()
        self.root.quit()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    x = Convolabel(root)
    root.mainloop()
