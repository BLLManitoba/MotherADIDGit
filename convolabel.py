import Tkinter as tk
import tkFileDialog
from tkMessageBox import showwarning, askyesno, showinfo
import os
import pyaudio
import wave
import re
# import cPickle
import csv
from numpy import fromstring, linspace
import time
import datetime
import webbrowser
from label import Variable
from block import Block, BlockPart
from database import Database

from matplotlib import lines, style
style.use('ggplot')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import utils
import makeblocks

FOLDERS = ['./input', './labelled_data', './output']
for FOLDER in FOLDERS:
    if not os.path.isdir(FOLDER):
        os.mkdir(FOLDER)


class Convolabel(object):

    def __init__(self, master):

        self.root = master
        self.root.resizable(width = False, height = False)
        self.root.title('Convolabel - IDS Conversation Labelling')
        self.root.protocol('WM_DELETE_WINDOW', self.check_before_exit) # register pressing the x button as event and call the corresponding function
        self.root.bind('<Control-s>', self.submit)

        program_path = os.getcwd()
        self.data = Database(program_path)
        self._data_is_saved = True
        self.current_rec = None
        self.current_block = None
        self.current_part = None

        self.frame = tk.Frame(root)#, bd = 1, relief = 'sunken')
        self.frame.grid(row = 0, column = 0, sticky = 'wns', padx = (30, 0), pady = 30)


        # Menu window
        self.menu = tk.Menu(self.root)
        self.root.config(menu = self.menu)
        self.submenu = tk.Menu(self.menu, tearoff = 0)
        self.menu.add_cascade(label = 'Menu', menu = self.submenu)
        self.submenu.add_command(label = 'Make blocks', command = self.make_blocks)
        self.submenu.add_command(label = 'Save data', command = self.save)
        self.submenu.add_command(label= 'Export to csv', command = self.export)
        self.submenu.add_command(label = 'Set ADS sample', command = lambda self = self, kind = 'ads': self.set_sample(kind))
        self.submenu.add_command(label = 'Set CDS sample', command = lambda self = self, kind = 'cds': self.set_sample(kind))
        readme_link = 'https://github.com/babylanguagelab/bll_app/tree/master/src/app/convolabel#how-it-works'
        self.submenu.add_command(label = 'Session info', command = self.show_stats)
        self.submenu.add_command(label = 'Help', command = lambda: webbrowser.open_new(readme_link))

        # Recordings list box
        tk.Label(self.frame, text = 'Recordings:').grid(row = 2, column = 0, padx = 0, pady = 0, sticky = 'W')
        self.recs_list = tk.Listbox(self.frame, width = 20, height = 15, exportselection = False, relief = tk.FLAT)
        self.recs_list.bind('<<ListboxSelect>>', self.update_current_rec)
        self.recs_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.recs_list.yview)
        self.recs_list.config(yscrollcommand = self.recs_scrollbar.set)
        self.recs_scrollbar.grid(row = 3, column = 0, rowspan = 10, sticky = 'NSE')
        self.recs_list.grid(row = 3, column = 0, rowspan = 10, padx = (0, 5), pady = 0, sticky = 'W')

        # Blocks list box
        tk.Label(self.frame, text = 'Blocks:').grid(row = 2, column = 1, padx = 5, pady = 0, sticky = 'W')
        self.blocks_list = tk.Listbox(self.frame, width = 15, height = 15, exportselection = False, relief = tk.FLAT)
        self.blocks_list.bind('<<ListboxSelect>>', self.update_current_block)
        self.blocks_list.bind('<space>', self.play)
        self.blocks_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.blocks_list.yview)
        self.blocks_list.config(yscrollcommand = self.blocks_scrollbar.set)
        self.blocks_scrollbar.grid(row = 3, column = 1, rowspan = 10, sticky = 'NSE')
        self.blocks_list.grid(row = 3, column = 1, rowspan = 10, padx = (5, 5), pady = 0, sticky = 'W')

        # Parts list box
        tk.Label(self.frame, text = 'Parts:').grid(row = 2, column = 2, sticky = 'W', padx = 5)
        self.parts_list = tk.Listbox(self.frame, width = 15, height = 15, exportselection = False, relief = tk.FLAT)
        self.parts_list.bind('<<ListboxSelect>>', self.update_current_part)
        self.parts_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.parts_list.yview)
        self.parts_list.configure(yscrollcommand = self.parts_scrollbar.set)
        self.parts_scrollbar.grid(row = 3, column = 2, rowspan = 10, sticky = 'NSE')
        self.parts_list.grid(row = 3, column = 2, padx = (5, 10), rowspan = 10, sticky = 'W')

        # Coder name entry
        self.coder_name = tk.StringVar()
        self.coder_name.set('--> Coder\'s name <--')
        self.coder_name_entry = tk.Entry(self.frame, justify = tk.CENTER, textvariable = self.coder_name, relief = tk.FLAT)
        self.coder_name_entry.grid(row = 0, column = 0, padx = 0, pady = (0, 20))

        # Buttons
        self.load_data_button = tk.Button(
            self.frame,
            text = 'Load',
            command = self.load_recs,
            height = 1,
            width = 10,
            relief = tk.GROOVE).grid(row = 4, column = 3, padx = 20)

        self.play_button = tk.Button(
            self.frame,
            text = 'Play',
            command = self.play,
            height = 1,
            width = 10,
            relief = tk.GROOVE)
        self.play_button.bind('<Enter>', self.show_block_length)
        self.play_button.bind('<Leave>', lambda event, self = self: self.play_button.configure(text = 'Play'))
        self.play_button.grid(row = 5, column = 3, padx = 0)

        self.submit_button = tk.Button(
            self.frame,
            text = 'Submit',
            command = self.submit,
            height = 1,
            width = 10,
            relief = tk.GROOVE).grid(row = 6, column = 3, padx = 0)

        self.ads_sample_button = tk.Button(
            self.frame,
            text = 'ADS',
            command = lambda self = self, kind = 'ads': self.play_sample(kind),
            height = 1,
            width = 3,
            relief = tk.GROOVE,
            state = 'disabled')
        self.ads_sample_button.grid(row = 11, column = 3, padx = (25, 0), sticky = 'W')

        self.cds_sample_button = tk.Button(
            self.frame,
            text = 'CDS',
            command = lambda self = self, kind = 'cds': self.play_sample(kind),
            height = 1,
            width = 3,
            relief = tk.GROOVE,
            state = 'disabled')
        self.cds_sample_button.grid(row = 11, column = 3, padx = (0, 25), sticky = 'E')


################################### Labels ###########################################

        # Default parameters for the entries
        entry_params = {'width': 3, 'state': 'disabled', 'justify': 'center', 'relief': 'flat'}
        entry_grid_params = {'sticky': tk.E, 'padx': (2, 30), 'pady': 3}
        label_grid_params = {'sticky': tk.E, 'padx': 0, 'pady': 2}


        self.labels_frame = tk.Frame(self.root)#, bd = 1, relief = 'sunken')
        self.labels_frame.grid(row = 1, column = 0, padx = 30, columnspan = 2, sticky = tk.W)# columnspan = 20, sticky = tk.W, padx = 10, pady = 20)

        # Adult-directed speech
        tk.Label(self.labels_frame, text = 'Adult-directed speech:').grid(label_grid_params, row = 0, column = 0)
        ads_entry = tk.Entry(self.labels_frame, entry_params)
        ads_entry.grid(entry_grid_params, row = 0, column = 1)

        # Child-directed speech
        tk.Label(self.labels_frame, text = 'Child-directed speech:').grid(label_grid_params, row = 1, column = 0)
        cds_entry = tk.Entry(self.labels_frame, entry_params)
        cds_entry.grid(entry_grid_params, row = 1, column = 1)

        # Other child speech
        tk.Label(self.labels_frame, text = 'Other child speech:').grid(label_grid_params, row = 2, column = 0)
        ocs_entry = tk.Entry(self.labels_frame, entry_params)
        ocs_entry.grid(entry_grid_params, row = 2, column = 1)

        junk_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Junk', command = self.junk_selected, state = 'disabled')
        junk_checkbutton.grid(row = 3, column = 0, sticky = tk.W, padx = (2, 10), pady = (3, 1))

        # Sesitive checkbutton
        sensitive_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Sensitive', state = 'disabled')
        sensitive_checkbutton.grid(row = 4, column = 0, sticky = tk.W, padx = (2, 10), pady = (0, 0))

        # Other language checkbutton
        other_langue_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Other language', state = 'disabled')
        other_langue_checkbutton.grid(row = 5, column = 0, sticky = tk.W, padx = (2, 10), pady = (1, 0))

        # Mother
        tk.Label(self.labels_frame, text = 'Mother:').grid(label_grid_params, row = 0, column = 2)
        mother_entry = tk.Entry(self.labels_frame, entry_params)
        mother_entry.grid(entry_grid_params, row = 0, column = 3)

        # Other females
        tk.Label(self.labels_frame, text = 'Other female(s):').grid(label_grid_params, row = 1, column = 2)
        other_fem_entry = tk.Entry(self.labels_frame, entry_params)
        other_fem_entry.grid(entry_grid_params, row = 1, column = 3)

        # Males
        tk.Label(self.labels_frame, text = 'Male(s):').grid(label_grid_params, row = 2, column = 2)
        male_entry = tk.Entry(self.labels_frame, entry_params)
        male_entry.grid(entry_grid_params, row = 2, column = 3)

        # Unsure
        tk.Label(self.labels_frame, text = 'Unsure:').grid(label_grid_params, row = 3, column = 2)
        unsure_entry = tk.Entry(self.labels_frame, entry_params)
        unsure_entry.grid(entry_grid_params, row = 3, column = 3)

        # Target child
        tk.Label(self.labels_frame, text = 'At target child:').grid(label_grid_params, row = 0, column = 4)
        target_child_entry = tk.Entry(self.labels_frame, entry_params)
        target_child_entry.grid(entry_grid_params, row = 0, column = 5)

        # Other child
        tk.Label(self.labels_frame, text = 'At other child:').grid(label_grid_params, row = 1, column = 4)
        other_child_entry = tk.Entry(self.labels_frame, entry_params)
        other_child_entry.grid(entry_grid_params, row = 1, column = 5)

        # Directive
        tk.Label(self.labels_frame, text = 'Directive:').grid(label_grid_params, row = 0, column = 6)
        directive_entry = tk.Entry(self.labels_frame, entry_params)
        directive_entry.grid(entry_grid_params, row = 0, column = 7)

        # Nondirective
        tk.Label(self.labels_frame, text = 'Nondirective:').grid(label_grid_params, row = 1, column = 6)
        nondirective_entry = tk.Entry(self.labels_frame, entry_params)
        nondirective_entry.grid(entry_grid_params, row = 1, column = 7)

        # Uncertain
        tk.Label(self.labels_frame, text = 'Uncertain:').grid(label_grid_params, row = 2, column = 6)
        uncertain_entry = tk.Entry(self.labels_frame, entry_params)
        uncertain_entry.grid(entry_grid_params, row = 2, column = 7)

        uncertain =    Variable('uncertain', uncertain_entry)
        nondirective = Variable('nondirective', nondirective_entry)
        directive =    Variable('directive', directive_entry)
        other_child =  Variable('other_child', other_child_entry)
        target_child = Variable('target_child', target_child_entry, directive, nondirective, uncertain)
        unsure =       Variable('unsure', unsure_entry)
        male =         Variable('male', male_entry)
        other_fem =    Variable('other_fem', other_fem_entry)
        mother =       Variable('mother', mother_entry, target_child, other_child)
        ocs =          Variable('ocs', ocs_entry)
        cds =          Variable('cds', cds_entry, mother, other_fem, male, unsure)
        ads =          Variable('ads', ads_entry)
        other_langue = Variable('other_langue', other_langue_checkbutton)
        sensitive =    Variable('sensitive', sensitive_checkbutton)
        junk =            Variable('junk', junk_checkbutton)

        self.labels = {
            'ads':          ads,
            'cds':          cds,
            'ocs':          ocs,
            'junk':            junk,
            'sensitive':    sensitive,
            'other_langue': other_langue,
            'mother':       mother,
            'other_fem':    other_fem,
            'male':         male,
            'unsure':       unsure,
            'target_child': target_child,
            'other_child':  other_child,
            'directive':    directive,
            'nondirective': nondirective,
            'uncertain':    uncertain
        }

        # Comments box
        self.comments = tk.Text(self.labels_frame, height = 10, width = 15, state = 'disabled', relief = tk.FLAT)
        self.comments.grid(row = 0, column = 8, rowspan = 6, padx = 0, pady = 0)

        # Status bar
        self.status_bar_frame = tk.Frame(self.root)
        self.status_bar_frame.grid(row = 2, column = 0, sticky = 'we', padx = 20, pady = 10)
        self.bar = tk.StringVar()
        self.status_bar = tk.Label(self.status_bar_frame, textvariable = self.bar)
        self.status_bar.grid(row = 0, column = 0)

        # Waveform graph
        self.graph_frame = tk.Frame(self.root)#, bd = 1, relief = 'sunken')
        self.graph_frame.grid(row = 0, column = 1, sticky = 'wns', pady = 30)
        self.fig = Figure(figsize = (5, 5), dpi = 60)
        self.ax = self.fig.add_subplot(111)
        self.wave_line, = self.ax.plot([], [], color = [0.2, 0.2, 0.2])
        self.ax.set_ylim(-1, 1)
        self.ax.set_yticks( [self.ax.get_ylim()[0] + i*0.5 for i in range(5)] )
        self.fig.patch.set_visible(False)
        self.ax.set_xlabel('Time (s)')
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.graph_frame)
        self.canvas.get_tk_widget().grid(row = 1, column = 0)

        # Session information
        self.session_stats = {
            'start_time': time.time(),
            'labelled_sec': 0,
            'labelled_blocks': 0
        }


    def show_stats(self):

        text = '''Elapsed time:\t{}\nLabelled blocks:\t{}\nLabelled time:\t{}\n\n1 min of audio = {} min of labelling\n{} blocks/min'''

        et = datetime.timedelta(seconds = time.time() - self.session_stats['start_time'])
        blocks_sum = self.session_stats['labelled_blocks']
        time_sum = datetime.timedelta(seconds = self.session_stats['labelled_sec'])
        if time_sum.seconds > 0:
            ratio_sec = round(float(et.seconds) / time_sum.seconds, 2)
            block_per_min = round(blocks_sum * 60.0 / et.seconds, 2)
        else:
            ratio_sec = 0
            block_per_min = 0
		
        et = str(et).split('.')[0] # remove microseconds
        time_sum = str(time_sum).split('.')[0]
		
        showinfo('Session info', text.format(et, blocks_sum, time_sum, ratio_sec, block_per_min))

    def show_block_length(self, event):
        ''' Executes when hover over the play button '''
        if self.current_part:
            assert self.current_block
            t = self.current_block.bytes2sec(self.current_part.bytes)
            self.play_button.configure(text = '{:.2f} s'.format(t))
        elif self.current_block:
            t = self.current_block.seconds
            self.play_button.configure(text = '{:.2f} s'.format(t))


    def data_is_saved(self, value = True):
        self._data_is_saved = value
        if value:
            self.root.title('Convolabel - IDS Conversation Labelling')
        else:
            self.root.title('Convolabel - IDS Conversation Labelling  *')


    def set_sample(self, kind):
        ''' Defines the path to a sample IDS/ADS clip. kind argument specifies ADS or IDS'''
        if self.current_rec == '':
            showwarning('No recording selected', 'Select a recording from the list first. The sample will be attached to that recording')
            return
        file = tkFileDialog.askopenfilename(filetypes = [('wave files', '.wav')])
        if not file:
            return
        file = os.path.abspath(file)
        # coder = self.coder_name.get()
        rec = self.current_rec

        if not self.data.has_key(rec):
            self.data.db[rec] = {}

        if kind == 'ads':
            self.data.db[rec]['_ads_sample'] = file
            self.ads_sample_button.configure(state = 'normal')
        elif kind == 'cds':
            self.data.db[rec]['_cds_sample'] = file
            self.cds_sample_button.configure(state = 'normal')

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
        stream = p.open(format = p.get_format_from_width(sample_width),
            channels = n_channels,
            rate = sample_rate,
            output = True)

        stream.write(audio)
        stream.stop_stream()
        stream.close()
        p.terminate()


    def junk_selected(self):
        if self.labels['junk'].get() == 1:
            for label in self.labels.values():
                if label.name == 'junk': continue
                label.set(0)
                label.set_visible(False)
        else:
            self.reset_labels()
            self.allow_initial_entries(True)


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
            #if not any(file.endswith('.cha') for file in files):
            #    showwarning('Files missing', 'No .cha file for {}'.format(folder))
            #    return
            if not any(file.endswith('.wav') for file in files):
                showwarning('Files missing', 'No .wav file for {}'.format(folder))
                return

            wavfile = [file for file in files if file.endswith('.wav')]
            #chafile = [file for file in files if file.endswith('.cha')]

            #if wavfile[0].strip('.wav') != chafile[0].strip('.cha'):
            #    showwarning('Files issue', 'cha and wav file names do not match for {}'.format(folder))
            #    return

        t0 = time.time()
        makeblocks.main('input', 'output')
        t = (time.time() - t0) / 60

        showinfo('All done!', 'Processed {} recordings in {:.3f} min'.format(len(folders), t))

        self.load_recs()



    def load_recs(self):

        coder = self.coder_name.get()

        if coder == '--> Coder\'s name <--':
            showwarning('Coder\'s name', 'Please enter your name')
            return

        self.data.set_coder(coder)
        coders = [name.strip('.pkl') for name in os.listdir(self.data.db_path) if name.endswith('.pkl')]

        if coder in coders:
            self.data.load_data()
        else:
            ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
            if ans == 0:
                return

        self.data.connect_sql()
        self.data.create_table()

        # Remove all recordings and blocks from the list boxes
        # if self.recs_list.get(0, tk.END) != ():
        self.recs_list.delete(0, tk.END)
        # if self.blocks_list.get(0, tk.END) != ():
        self.blocks_list.delete(0, tk.END)

        # Recs are the recordings (e.g C208_20150101). Every folder in the data path is considered a rec
        to_input_data = os.path.join(os.getcwd(), 'input')
        files = os.listdir(os.path.join(to_input_data, to_input_data))
        names = [file for file in files if file.endswith('.wav')]
        try:
            regexp = re.compile('\d+')
            names = sorted(names, key = lambda x: int(regexp.search(x).group()))
        except:
            names = sorted(names, key = str)

        for name in names:
            self.recs_list.insert(tk.END, name.split(".wav")[0])

    def load_recs2(self):

        coder = self.coder_name.get()

        if coder == '--> Coder\'s name <--':
            showwarning('Coder\'s name', 'Please enter your name')
            return

        self.data.set_coder(coder)
        coders = [name.strip('.pkl') for name in os.listdir(self.data.db_path) if name.endswith('.pkl')]

        if coder in coders:
            self.data.load_data()
        else:
            ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
            if ans == 0:
                return

        self.data.connect_sql()
        self.data.create_table()

        # Remove all recordings and blocks from the list boxes
        # if self.recs_list.get(0, tk.END) != ():
        self.recs_list.delete(0, tk.END)
        # if self.blocks_list.get(0, tk.END) != ():
        self.blocks_list.delete(0, tk.END)

        # Recs are the recordings (e.g C208_20150101). Every folder in the data path is considered a rec
        #names = [name for name in os.listdir(self.data.audio_path) if os.path.isdir(os.path.join( self.data.audio_path, name ))]
        to_input_data = os.path.join(os.getcwd(), 'input')
        files = os.listdir(os.path.join(to_input_data, to_input_data))
        names = [file for file in files if file.endswith('.wav')]
        try:
            regexp = re.compile('\d+')
            names = sorted(names, key = lambda x: int(regexp.search(x).group()))
        except:
            names = sorted(names, key = str)

        for name in names:
            self.blocks_list.insert(tk.END, name)

    def update_current_rec(self, event):
        ''' Executes on selection from the recording list box. Recording = rec here '''

        if self.recs_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty list
            return
        self.current_block = None
        self.current_part = None

        self.blocks_list.delete(0, tk.END)
        self.parts_list.delete(0, tk.END)

        w = event.widget
        self.current_rec = w.get(int(w.curselection()[0]))

        # Plot the emty line = clear the graph
        self.wave_line.set_data([], [])
        self.canvas.draw()

        for label in self.labels.values():
            label.set(0)
            label.set_visible(False)

        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'disabled')

        # If the ADS/IDS samples were set, make the 'Play sample' button available
        if self.data.has_key(self.current_rec, '_ads_sample'):
            self.ads_sample_button.configure(state = 'normal')
        else:
            self.ads_sample_button.configure(state = 'disabled')

        if self.data.has_key(self.current_rec, '_cds_sample'):
            self.cds_sample_button.configure(state = 'normal')
        else:
            self.cds_sample_button.configure(state = 'disabled')


        path = os.path.join( self.data.audio_path, self.current_rec ) # path to the folder containing blocks for the selected rec
        files = os.listdir(path)

        names = [file for file in files if file.endswith('.wav')]
        # Sort the names of the blocks in ascending order. This block of code takes a lot of time

        for name in names:
            self.blocks_list.insert(tk.END, name.split(".wav")[0])
            if self.data.has_key(self.current_rec, name):
                self.blocks_list.itemconfig(tk.END, foreground = 'gray')

        labelled = self.data.total_labelled(self.current_rec)
        total = 1
        self.bar.set('{:.0f}% of blocks are labelled for this recording'.format(100 * labelled / total))


    def load_labels(self, dic):

        for key, value in self.labels.items():
            value.set(dic[key])

        if self.labels['junk'].get() == 1:
            self.junk_selected()

        self.comments.delete(1.0, tk.END)
        self.comments.insert(tk.END, dic['comments'])
        self.comments.configure(state = 'normal')

        self.bar.set('Labeled at {}'.format(dic['time']))


    def reset_labels(self):
        for label in self.labels.values():
            label.set(0)
        self.comments.delete(1.0, tk.END)

    def allow_initial_entries(self, value = True):
        self.labels['ads'].set_visible(value)
        self.labels['cds'].set_visible(value)
        self.labels['ocs'].set_visible(value)
        self.labels['sensitive'].set_visible(value)
        self.labels['other_langue'].set_visible(value)
        self.labels['junk'].set_visible(value)
        if value:
            self.comments.configure(state = 'normal')
        else:
            self.comments.configure(state = 'disabled')


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


    def update_current_block(self, event):
        ''' Executes on block selection from the list box '''

        if self.blocks_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty blocks list
            return

        w = event.widget
        index = int(w.curselection()[0])
        name = w.get(index)
        path = os.path.join(self.data.audio_path, self.current_rec)

        self.current_block = Block(path, name, index)

        self.bar.set('')
        self.current_part = None
        self.parts_list.delete(0, tk.END)

        rec = self.current_rec
        block = self.current_block.name

        # List the parts for this block
        for index, part in enumerate(self.current_block.parts_length_list):
            length_sec = self.current_block.bytes2sec(part)
            self.parts_list.insert(tk.END, '{}: {:.2f} s'.format(index, length_sec) )
            if self.data.has_key(rec, block, str(index)):
                self.parts_list.itemconfig(tk.END, foreground = 'gray')

        # Make a waveform graph
        data = self.current_block.convert_audio()
        if data is False:
            self.bar.set('Unable to show the graph :(')
            return

        times = linspace(0, self.current_block.seconds, len(data)) # numpy function
        try:
            self.wave_line.set_data(times, data)
            self.ax.set_xlim(0 - self.current_block.seconds/20.0, self.current_block.seconds + self.current_block.seconds/20.0)
            self.canvas.draw()
        except:
            self.wave_line.set_data([], [])
            self.canvas.show()
            self.bar.set('Unable to show the graph :(')

        # Load previous labels/allow entries

        if self.data.has_key(rec, block):
            try:
                dic = self.data.db[rec][block]['whole']
                self.allow_initial_entries(True)
                self.load_labels(dic)
            except KeyError:
                self.bar.set('Label parts for this block')
                self.reset_labels()
                self.allow_initial_entries(False)
        else:
            self.reset_labels()
            self.allow_initial_entries(True)


    def update_current_part(self, event):

        if self.parts_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty blocks list
            return

        w = event.widget
        index = int(w.curselection()[0])
        name = w.get(index)
        length = self.current_block.parts_length_list[index]

        self.current_part = BlockPart(name, index, length)

        rec = self.current_rec
        block = self.current_block.name

        try:
            dic = self.data.db[rec][block][str(index)]
            self.load_labels(dic)
        except:
            self.reset_labels()
            self.bar.set('')
        self.allow_initial_entries(True)

    def play(self, *event):
        ''' Plays selected block '''

        if self.current_block is None:
            showwarning('Block error','Choose the block')
            return

        if self.current_part:
            x0, xend = self.current_block.get_startend_idcs()[self.current_part.index]
        else:
            xend = self.current_block.bytes
            x0 = 0 # start index

        chunk = 1024 # samples to access on every iteration
        x1 = x0 + chunk #

        background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        line = self.ax.add_line(lines.Line2D([x0, x0], [-0.95, 0.95], alpha = 0.8, color = '#FFA9A5')) # the sliding bar

        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(self.current_block.sample_width),
                        channels = self.current_block.n_channels,
                        rate = self.current_block.sample_rate,
                        output = True)

        # http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
        while x1 < xend:
            stream.write(self.current_block.audio_data[x0:x1])
            self.fig.canvas.restore_region(background)
            line.set_xdata(self.current_block.bytes2sec(x1)) # offset by 1024 frames; convert to seconds
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

            x0 += chunk
            x1 += chunk
        else:
            stream.write(self.current_block.audio_data[x0:xend]) # play the rest of the audio
            self.fig.canvas.restore_region(background)
            line.set_xdata(self.current_block.bytes2sec(xend))
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

        line.remove()
        self.canvas.draw()

        stream.stop_stream()
        stream.close()
        p.terminate()


    def submit(self, *event):

        if self.current_block is None:
            showwarning('Block error', 'Choose the block')
            return

        correct = self.check_labels()
        if not correct:
            showwarning('Labels issue', 'Please check the labels')
            return

        to_add = self.fetch_labels()
        to_add['time'] = time.strftime('%H:%M, %d %B %Y')
        to_add['comments'] = self.comments.get(1.0, tk.END).strip()

        rec = self.current_rec
        block = self.current_block.name

        if self.current_part:
            part = str(self.current_part.index)
            length = self.current_block.bytes2sec(self.current_part.bytes)
            self.parts_list.itemconfig(self.current_part.index, foreground = 'gray')
            self.parts_list.focus_set()
        else:
            part = 'whole'
            length = self.current_block.seconds
            self.blocks_list.itemconfig(self.current_block.index, foreground = 'gray')
            self.session_stats['labelled_blocks'] += 1
            self.blocks_list.focus_set()

        to_add['length'] = length
        self.data.submit_labels(rec, block, part, to_add)
        self.bar.set('Labels submitted!')
        self.data_is_saved(False)

        self.session_stats['labelled_sec'] += length

        if self.current_part:
            if len(self.data.db[rec][block]) == len(self.current_block.parts_length_list):
                self.blocks_list.itemconfig(self.current_block.index, foreground = 'gray')
                self.session_stats['labelled_blocks'] += 1


    def save(self):
        ''' Loads the data file, updates the current data, saves the file on the hard drive '''

        self.data.save_data()

        self.bar.set('Data is saved!')
        self.data_is_saved(True)


    def export(self):
        ''' Exports the current state of data to csv file. All coders are included '''

        output = tkFileDialog.asksaveasfilename(filetypes = [('Comma-separated file', '.csv')], initialfile = 'data.csv' )
        if output == '':
            return

        d = utils.merge_coders_data(self.data.db_path)

        with open(output, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Date coded', 'Coder', 'Recording', 'Block', 'Length (s)', 'Junk', 'Sensitive',
                            'Other language', 'Adult-directed speech', 'Child-directed speech', 'Other child speech',
                            'Mother', 'Other female(s)', 'Male(s)', 'Unsure', 'Directed at target child',
                            'Directed at other child', 'Directive', 'Nondirective', 'Uncertain', 'Comments'])
            for coder_name, coder in d.items():
                for rec_name, rec in coder.items():
                    for block_name, block in rec.items():
                        if block_name.startswith('_'): continue # skip the sample clips
                        for part_name, part in block.items():
                            block_part = '-'.join([block_name, part_name])
                            row = [
                                    part['time'],
                                    coder_name,
                                    rec_name,
                                    block_part,
                                    part['length'],
                                    part['junk'],
                                    part['sensitive'],
                                    part['other_langue'],
                                    part['ads'],
                                    part['cds'],
                                    part['ocs'],
                                    part['mother'],
                                    part['other_fem'],
                                    part['male'],
                                    part['unsure'],
                                    part['target_child'],
                                    part['other_child'],
                                    part['directive'],
                                    part['nondirective'],
                                    part['uncertain'],
                                    part['comments'],
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
