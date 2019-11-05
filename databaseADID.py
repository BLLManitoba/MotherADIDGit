from __future__ import print_function
import sqlite3 as sql
import cPickle
import os
import utils

class Database(object):

    def __init__(self, program_path):
        self.coder = None
        self.db = {}

        self.conn = None
        self.c = None

        self.program_path = program_path
        self.audio_path = os.path.join(self.program_path, 'output')

        self.db_path = os.path.join(self.program_path, 'labelled_data_ADID')
        self.input_path = os.path.join(self.program_path, 'input')
        
    def set_coder(self, name):
        self.coder = name

    @property
    def pkl_file(self):
        return os.path.join(self.db_path, self.coder + '.pkl')


    def submit_labels(self, rec,chunk, block, part, labels_dic):
        if not self.has_key(rec):
            self.db[rec] = {}
        if not self.has_key(rec, chunk):
            self.db[rec][chunk] = {}
        if not self.has_key(rec, chunk,block):
            self.db[rec][chunk][block] = {}

        self.db[rec][chunk][block][part] = labels_dic
        self.insert_block(rec,chunk, block, part, labels_dic) # sql
		
    def submit_labels_sarah(self, rec,chunk, block, part, labels_dic):
        if not self.has_key(rec):
            self.db[rec] = {}
        if not self.has_key(rec, chunk):
            self.db[rec][chunk] = {}
        if not self.has_key(rec, chunk,block):
            self.db[rec][chunk][block] = {}

        self.db[rec][chunk][block][part] = labels_dic
        self.insert_block_sarah(rec,chunk, block, part, labels_dic) # sql


    def has_key(self, rec, chunk = None, block = None, part = None):
        try:
            if part:
                return part in self.db[rec][chunk][block].keys()
            elif block:
                return block in self.db[rec][chunk].keys()
            elif chunk:
                return chunk in self.db[rec].keys()
            else:
                return rec in self.db.keys()
        except KeyError:
            return False

    def total_labelled(self, rec):
        try:
            labelled = len(self.db[rec])
            if '0' in self.db[rec].keys():
                labelled -= 1
            if '1' in self.db[rec].keys():
                labelled -= 1
            if '2' in self.db[rec].keys():
                labelled -= 1
            return labelled
        except KeyError:
            return 0


    def save_data(self):
        with open(self.pkl_file, 'wb') as f:
            cPickle.dump(self.db, f, cPickle.HIGHEST_PROTOCOL)

    def load_data(self):
        if os.path.exists(self.pkl_file):
            with open(self.pkl_file, 'rb') as f:
                self.db = cPickle.load(f)
        #else:
            

################# SQL backups ##################################


    @ property
    def sql_file(self):
        return os.path.join(self.db_path, self.coder + '.db')

    def connect_sql(self):
        self.conn = sql.connect(self.sql_file)
        self.c = self.conn.cursor()
        # print("DB Connected")

    def create_table(self):
        self.c.execute("""CREATE TABLE IF NOT EXISTS {} (
            time            TEXT,
            rec             TEXT,
            chunk           TEXT,
            block           TEXT,
            part            TEXT,
            length          TEXT,
            cds_ads            TEXT,
            confidence  INT,
            original_label TEXT
            )""".format(self.coder))
        print("DB Created")
		
    def create_table_sarah(self):
        self.c.execute("""CREATE TABLE IF NOT EXISTS {} (
            insertion_time            TEXT,
            rec             TEXT,
			chunk           TEXT,
            block           TEXT,
            part            TEXT,
            part_length          INT,
            cds_ads TEXT,
            confidence_level INT,
            original_label TEXT,
            duration TEXT,
			comments TEXT
            )""".format(self.coder))
        print("DB Created")

    def insert_block(self, rec, chunk,block, part, labels_dic):

        labels_dic['rec'] = rec
        labels_dic['block'] = block
        labels_dic['part'] = part
        labels_dic['chunk'] = chunk

        with self.conn:
            self.c.execute("INSERT INTO {} VALUES (:time, :rec, :chunk, :block, :part, :length, :ads_cds,:confidence,:original_label)".format(self.coder), labels_dic)

    def insert_block_sarah(self, rec, chunk, block, part, labels_dic):
        labels_dic['rec'] = rec
        labels_dic['block'] = block
        labels_dic['part'] = part
        labels_dic['chunk'] = chunk
        with self.conn:
            sql = "INSERT INTO "+format(self.coder)+" VALUES ('"+ labels_dic["insertion_time"]+"','"+\
                  labels_dic["rec"]+"','"+labels_dic["chunk"]+"','"+labels_dic["block"]+"','"+\
				  labels_dic["part"]+"',"+str(labels_dic["part_length"])+",'"+labels_dic["cds_ads"]+"',"+\
                  str(labels_dic["confidence_level"])\
                  +",'"+ labels_dic["original_label"]+"','"+labels_dic["duration"]+"','"+labels_dic["comments"]+"');"
            self.c.execute(sql)
	

    def close_sql(self):
        if self.conn:
            self.conn.close()




