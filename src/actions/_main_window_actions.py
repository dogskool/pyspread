#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6 on Sun May 25 23:31:23 2008

# Copyright 2008 Martin Manns
# Distributed under the terms of the GNU General Public License
# generated by wxGlade 0.6 on Mon Mar 17 23:22:49 2008

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------


"""
_main_window_actions.py
=======================

Module for main window level actions.
All non-trivial functionality that results from main window actions
and belongs to the application as whole (in contrast to the grid only)
goes here.

Provides:
---------
  1. ExchangeActions: Actions for foreign format import and export
  2. PrintActions: Actions for printing
  3. ClipboardActions: Actions which affect the clipboard
  4. FindActions: Actions for finding and replacing
  5. MacroActions: Actions which affect macros  
  6. HelpActions: Actions for getting help
  7. AllMainWindowActions: All main window actions as a bundle

"""

import csv
import os
import types

from copy import copy

import wx
import wx.html

from config import DEFAULT_FILENAME, HELP_SIZE, HELP_DIR

from lib._interfaces import Digest
from lib.irange import irange
from gui._printout import PrintCanvas, Printout

class CsvInterface(object):
    """CSV interface class
    
    Provides
    --------
     * __iter__: CSV reader - generator of generators of csv data cell content
     * write: CSV writer
    
    """
    
    def __init__(self, path, dialect, digest_types, has_header):
        self.path = path
        self.csvfilename = os.path.split(path)[1]
        
        self.dialect = dialect
        self.digest_types = digest_types
        self.has_header = has_header
        
        self.first_line = False
        
    def __iter__(self):
        """Generator of generators that yield csv data"""
        
        csv_file = open(self.path, "r")
        csv_reader = csv.reader(csv_file, self.dialect)
        self.first_line = self.has_header
        
        try:
            for line in csv_reader:
                yield self._get_csv_cells_gen(line)
                self.first_line = False
                                              
        except Error, err:
            msg = 'The file "' + self.csvfilename + '" only partly loaded.' + \
                  '\n \nError message:\n' + str(err)
            short_msg = 'Error reading CSV file'
            self.main_window.interfaces.display_warning(msg, short_msg)
        
        csv_file.close()
    
    def _get_csv_cells_gen(self, line):
        """Generator of values in a csv line"""
        
        digest_types = self.digest_types
        
        for j, value in enumerate(line):
            if self.first_line:
                digest_key = None
                digest = lambda x: x
            else:
                try:
                    digest_key = digest_types[j]
                except IndexError:
                    digest_key = digest_types[0]
                    
                digest = Digest(acceptable_types=[digest_key])
                
            try:
                digest_res = digest(value)
                
                if digest_key is not None and digest_res != "\b" and \
                   digest_key is not types.CodeType:
                    digest_res = repr(digest_res)
                elif digest_res == "\b":
                    digest_res = None
                
            except Exception, err:
                digest_res = str(err)
            
            yield digest_res
    
    def write(self, iterable):
        """Writes values from iterable into CSV file"""
        
        csvfile = open(self.path, "wb")
        csv_writer = csv.writer(csvfile, self.dialect)
        
        for line in iterable:
            csv_writer.writerow(line)
        
        csvfile.close()


class TxtGenerator(object):
    """Generator of generators of Whitespace separated txt file cell content"""
        
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        infile = open(self.filename)
        
        for line in infile:
            for col in line.split():
                yield col
        
        infile.close()

class ExchangeActions(object):
    """Actions for foreign format import and export"""
    
    def _import_csv(self, path):
        """CSV import workflow"""

        # Get csv info
        
        try:
            dialect, has_header, digest_types = \
                self.main_window.interfaces.get_csv_import_info(path)
                
        except TypeError:
            return
        
        return CsvInterface(path, dialect, digest_types, has_header)
    
    def _import_txt(self, path):
        """Whitespace-delimited txt import workflow. This should be fast."""
        
        return TxtGenerator(path)
    
    def import_file(self, filepath, filterindex):
        """Imports external file
        
        Parameters
        ----------
        
        filepath: String
        \tPath of import file
        filterindex: Integer
        \tIndex for type of file, 0: csv, 1: tab-delimited text file
        
        """
        
        if filterindex == 0:
            # CSV import option choice
            return self._import_csv(filepath)
        elif filterindex == 1:
            # TXT import option choice
            return self._import_txt(filepath)
        else:
            msg = "Unknown import choice" + str(filterindex)
            short_msg = 'Error reading CSV file'
            
            self.main_window.interfaces.display_warning(msg, short_msg)

    def _export_csv(self, filepath, data):
        """CSV import workflow"""

        # Get csv info
        
        csv_info = self.main_window.interfaces.get_csv_export_info(data)
        
        if csv_info is None:
            return
        
        try:
            dialect, digest_types, has_header = csv_info
        except TypeError:
            return
        
        # Export CSV file
        
        csv_interface = CsvInterface(filepath, dialect, digest_types, 
                                     has_header)
        
        try:
            csv_interface.write(data)
        except IOError, err:
            msg = 'The file "' + path + '" could not be fully written ' + \
                  '\n \nError message:\n' + str(err)
            short_msg = 'Error writing CSV file'
            self.main_window.interfaces.display_warning(msg, short_msg)

    def export_file(self, filepath, filterindex, data):
        """Exports external file. Only CSV supported yet."""
        
        self._export_csv(filepath, data)


class PrintActions(object):
    """Actions for printing"""
    
    def print_preview(self, print_area, print_data):
        """Launch print preview"""
        
        pdd = wx.PrintDialogData(print_data)
        
        # Create the print canvas
        canvas = PrintCanvas(self.main_window, self.grid, print_area)
        
        printout = Printout(canvas)
        printout2 = Printout(canvas)
        
        self.preview = wx.PrintPreview(printout, printout2, print_data)

        if not self.preview.Ok():
            print "Houston, we have a problem...\n"
            return

        pfrm = wx.PreviewFrame(self.preview, self.main_window, "Print preview")

        pfrm.Initialize()
        pfrm.SetPosition(self.main_window.GetPosition())
        pfrm.SetSize(self.main_window.GetSize())
        pfrm.Show(True)
    
    def printout(self, print_area, print_data):
        """Print out print area
        
        See:
        http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3471083
        
        """
        
        pdd = wx.PrintDialogData(print_data)
        printer = wx.Printer(pdd)
        
        # Create the print canvas
        canvas = PrintCanvas(self.main_window, self.grid, print_area)
        
        printout = Printout(canvas)
        
        if printer.Print(self.main_window, printout, True):
            self.print_data = \
                wx.PrintData(printer.GetPrintDialogData().GetPrintData())
        
        printout.Destroy()
        canvas.Destroy()


class ClipboardActions(object):
    """Actions which affect the clipboard"""
    
    def cut(self, selection):
        """Cuts selected cells and returns data in a tab separated string"""
        
        # Copy cells
        data = self.copy(selection)
        
        # Delete cells
        
        for key in self.grid:
            if key in selection:
                self.grid.pop(key)
        
        return data
    
    def copy(self, selection):
        """Returns code from selection in a tab separated string"""
        
        tab = self.grid.current_table
        
        (bb_top, bb_left), (bb_bottom, bb_right) = selection.get_bbox()
        
        data = [[u""] * (bb_right - bb_left)] * (bb_bottom - bb_top)
        
        for __row, __col, __tab in self.grid.code_array:
            if tab == __tab and \
               bb_top <= __row <= bb_bottom and \
               bb_left <= __col <= bb_right and \
               (__row, __col, __tab) in selection:
                   data[row][col] = code
        
        return "\n".join("\t".join(line) for line in data)
    
    def copy_result(self, selection):
        """Returns result strings from selection in a tab separated string"""
        
        tab = self.grid.current_table
        
        data = []
        
        (bb_top, bb_left), (bb_bottom, bb_right) = selection.get_bbox()
        
        for row in irange(bb_top, bb_bottom):
            data.append([])
            for col in irange(bb_left, bb_right):
                if (row, col) in selection:
                    data[-1].append(self.grid.code_array[row, col, tab])
        
        return "\n".join("\t".join(line) for line in data)
    
    def paste(self, key, data):
        data_lines = data.split("\n")
        
        row, col, tab = key
        
        for data_row, line in enumerate(data_lines):
            for data_col, value in enumerate(line.split()):
                self.grid.code_array[row+data_row, col+data_col, tab] = value

class MacroActions(object):
    """Actions which affect macros"""
    
    def show(self):
        raise NotImplementedError
    
    def open(self):
        raise NotImplementedError
        
    def save(self):
        raise NotImplementedError


class HelpActions(object):
    """Actions for getting help"""
    
    def launch_help(self, helpname, filename):
        """Generic help launcher"""
        
        # Set up window
        
        help_window = wx.Frame(self.main_window, -1, helpname, 
                            wx.DefaultPosition, wx.Size(*HELP_SIZE))
        help_htmlwindow = wx.html.HtmlWindow(help_window, -1, 
                            wx.DefaultPosition, wx.Size(*HELP_SIZE))
        
        # Get help data
        current_path = os.getcwd()
        os.chdir(HELP_DIR)
        help_file = open(filename, "r")
        help_html = help_file.read()
        help_file.close()
        
        # Show tutorial window
        
        help_htmlwindow.SetPage(help_html)
        help_window.Show()
        
        os.chdir(current_path)
        
    
class AllMainWindowActions(ExchangeActions, PrintActions, 
                           ClipboardActions, MacroActions, HelpActions):
    """All main window actions as a bundle"""
    
    def __init__(self, main_window, grid):
        self.main_window = main_window
        self.grid = grid
        
        ExchangeActions.__init__(self)
        PrintActions.__init__(self)
        ClipboardActions.__init__(self)
        MacroActions.__init__(self)
        HelpActions.__init__(self)
        
