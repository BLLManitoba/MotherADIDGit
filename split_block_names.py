import csv
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import os



def load_data(file):

    with open(file, 'rb') as f:
        lines = [l for l in csv.reader(f)]

    colheaders = lines[0]
    data = lines[1:]

    return colheaders, data


def process_line(line):

    block, part = line[3].split('-')
    new_line = line[:3] + [block, part] + line[4:]

    return new_line


def main():

    root = tk.Tk()
    root.withdraw()

    file = tkFileDialog.askopenfilename(filetypes = [('Comma-separated files', '*.csv')],
        initialfile = './data.csv')
    path, name = os.path.split(file)
    name, ext = os.path.splitext(name)
    new_file = os.path.join(path, name + '_processed' + ext)

    if not os.path.isfile(file):
        tkMessageBox.showerror('Error', 'No such file: {}'.format(file))
        return

    colheaders, data = load_data(file)
    new_colheaders = colheaders[:3] + ['Block', 'Part'] + colheaders[4:]
    new_data = []

    with open(new_file, 'wb') as f:

        writer = csv.writer(f)
        writer.writerow(new_colheaders)

        for line in data:
            if not any(line):
                continue
            writer.writerow(process_line(line))

    tkMessageBox.showinfo('Done', 'Saved to {}'.format(new_file))




if __name__ == '__main__':
    main()


