import Tkinter as tk

class Variable(object):

    def __init__(self, name, entry, *children):
        self.name = name
        self.entry = entry
        self.children = children # a tuple of Lables

        self.var = tk.IntVar()

        self.ok_to_sumbit = False

        if isinstance(self.entry, tk.Entry):
            self.var.trace('w', self.check_entry)
            self.entry.configure(textvariable = self.var)
        elif isinstance(self.entry, tk.Checkbutton):
            self.entry.configure(variable = self.var)

    def set(self, value):
        self.var.set(value)

    def get(self):
        return self.var.get()

    def set_visible(self, yes = True):
        if yes:
            self.entry.configure(state = 'normal')
        else:
            self.entry.configure(state = 'disabled')

    def check_entry(self, *args):
        try:
            if self.get() in range(5):
                self.entry.configure(background = 'white')
            else:
                self.entry.configure(background = '#FFA9A5')

            if self.children:
                if self.get() in range(1, 5):
                    for child in self.children:
                        child.set_visible()
                else:
                    for child in self.children:
                        child.set_visible(False)

        except ValueError:
            self.entry.configure(background = '#FFA9A5')


    def children_sum(self):
        assert self.children, 'no children assigned'

        s = 0
        for child in self.children:
            s += child.get()

        return s



class LabelsGroup(object):
    def __init__(self, *labels):
        for label in labels:
            setattr(self, label.name, label)

    def __iter__(self):
        attributes = (i for i in self.__dict__.keys() if not i.startswith('_'))
        for attr in attributes:
            yield getattr(self, attr)

    def from_dict(self):
        pass

    def to_dict(self):
        pass

    def reset(self):
        pass
