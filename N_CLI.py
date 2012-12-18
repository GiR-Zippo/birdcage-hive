# encoding: iso-8859-1

#
# Copyright (C) 20011-2012 by Booksize
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
#

import N_CLI
import curses

class N_CLI:
    LastLine = 1
    line_start = 1
    col_start = 1
    MainCLI = None
   

    #Set MasterCaller
    def set_master(self,args):
        N_CLI.MainCLI = args
        
    def __init__(self):
        self.stdscr = self.init_curses()
        # Aktuelle Screengroesse ermitteln
        self.maxy, self.maxx = self.stdscr.getmaxyx()

        #MenuBar
        self.mwin = curses.newwin(3, self.maxx - 2, 0, 1)
        self.show_menu(self.mwin)

        #Status Bar
        self.s_win = curses.newwin(1, self.maxx, 3, 0)

        #TextFenster
        self.twin = curses.newwin(self.maxy - 5, self.maxx, 5, 0)

        #InputZeile
        self.iwin = curses.newwin(2, self.maxx, self.maxy - 3, 0)
        self.iwin = curses.newpad(2, 3000)
        self.iwin.addstr(0, 1, "Command:")

        # Grosses Pad erzeugen
        self.twin = curses.newpad(10000, 3000)
        self.instr = ""


    def init_curses(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLUE)
        self.stdscr.bkgd(curses.color_pair(1))
        self.stdscr.refresh()
        return self.stdscr


    def show_menu(self,win):
        win.clear()
        win.bkgd(curses.color_pair(2))
        win.addstr(1, 2, "[ESC]: Exit", curses.A_BOLD)
        win.addstr(1, 60, "[F10]: Clear", curses.A_BOLD)
        win.box()
        win.refresh()

    def StatusBar(self,item,args):
        if (item == "module"):
            self.s_win.bkgd(curses.color_pair(3))
            self.s_win.addstr(0,1,"Selected Module: " + args, curses.A_BOLD);
            self.s_win.refresh()
        elif (item == "cp"):
            if (args == True):
                self.mwin.addstr(1,self.maxx - 2, "C");
            else:
                self.mwin.addstr(1,self.maxx - 2, " ");


        self.mwin.refresh()

    def writeline(self, args):
        if (N_CLI.LastLine > 999):
            N_CLI.LastLine = 1
            self.twin.clear()
            
        self.twin.addstr(N_CLI.LastLine, 1, str(args))
        N_CLI.LastLine += len(args.split("\n"))
        
        if (N_CLI.LastLine >= 25):
            N_CLI.line_start += 1
                  
    def refresh(self):
        self.iwin.refresh(0, 1, self.maxy-2, 1, self.maxy-2, self.maxx-2)
        self.twin.refresh(N_CLI.line_start , N_CLI.col_start, 4, 1, self.maxy-4, self.maxx-2)
        c = self.stdscr.getch()

        if c == 27:
            self.exit()
            return False
        elif c == curses.KEY_F10:
            N_CLI.line_start = 1;
            N_CLI.line_start = 1;
            N_CLI.LastLine = 1;
            self.twin.clear();
            self.twin.refresh(N_CLI.line_start , N_CLI.col_start, 4, 1, self.maxy-4, self.maxx-2);
        elif c == curses.KEY_DOWN:
            N_CLI.line_start += 1
        elif c == curses.KEY_UP:
            if N_CLI.line_start > 1: N_CLI.line_start -= 1
        elif c == curses.KEY_LEFT:
            if N_CLI.col_start > 1: N_CLI.col_start -= 1
        elif c == curses.KEY_RIGHT:
            N_CLI.col_start += 1
        elif c == 339:
            if N_CLI.line_start > 10: N_CLI.line_start -= 10
        elif c == 338:
            N_CLI.line_start += 10
        elif c == 10:
            self.iwin.clear()
            self.iwin.addstr(0, 1, "Command:")
            self.writeline(">>" + self.instr)
            N_CLI.MainCLI.command(self.instr)
            self.instr=""
        elif c == 263:
            self.instr = self.instr[0:-1]
            self.iwin.clear()
            self.iwin.addstr(0, 1, "Command:")
            self.iwin.addstr(0, 10, self.instr)
        else:
            self.iwin.clear()
            self.iwin.addstr(0, self.maxx -5, str(N_CLI.LastLine))
            try:
                self.instr = self.instr + chr(c)
                self.iwin.addstr(0, 1, "Command:")
                self.iwin.addstr(0, 10, self.instr)
            except (ValueError):
                pass

    def exit(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
