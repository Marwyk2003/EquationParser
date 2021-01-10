from math import nan
import sys
from sys import argv
import re
import random
from datetime import datetime
import numpy as np

numberR = '[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
variableR = '(?<![0-9])[a-zA-Z_][a-zA-Z_0-9]*'
functionsR = '(?:sin|cos|tan)h?r?|abs|exp|ln|log2|log10'

class FormatError(Exception):
    def __init__(self, eq, description):
        print(f"FORMAT ERROR {eq}: {description}")
        sys.exit()
class ConvertionError(Exception):
    def __init__(self, eq, description):
        print(f"CONVERTION ERROR {eq}: {description}")
        sys.exit()
class CalculationError(Exception):
    def __init__(self, eq, description):
        print(f"CALCULATION ERROR {eq}: {description}")
        sys.exit()
class VariableError(Exception):
    def __init__(self, var, description):
        print(f"VARIABLE ERROR {var}: {description}")
        sys.exit()

class Equation:
    def __init__(self):
        self.variables = {}  # dict for all given/calculated variables
        self.unknowns = {}  # dict for all unknowns/querries
        self.seed = random.seed(datetime.now())  # seed for some randomisation

    # returns the type of a string
    def getType(self, c):
        if re.fullmatch(numberR, c):
            # number (including decimal point)
            return 1
        elif c in '+-*/^':
            # all operations
            return -1
        elif c in '()':
            return -2
        elif re.fullmatch(functionsR, c):
            return -3
        else:
            # empty/unwanted character
            return 0

    # returns operation's priority
    def getPrirority(self, c):
        if c in '+-':
            return 1
        elif c in '*/':
            return 2
        elif c in '^':
            return 3
        else:
            return 0

    '''
    function extracts data from equation
    returns list: [expression, type]
    '(30/16)-7' -> [('(',-2), ('30', ), ('/', -1), ('16', 1), (')', -2), ('-', -1), ('7', 1)]
    '''
    def extractEquation(self, eq):
        tab = []
        # pattern: operations or number or variable
        r = re.compile(f'{functionsR}|[\+\-\*\/\^\(\)]|{variableR}|{numberR}')
        for m in r.finditer(eq): 
            tab.append((m.group(0), self.getType(m.group(0))))
        return tab

    # converts regular equation to an ONP list
    def convertToONP(self, eq):
        stack = [] # operation stack
        ONPeq = [] # ONP equation function return
        funcStack = [] # function stack 
        beginning = True
        step = 0
        # replace variables with responding values
        r = re.compile(variableR)
        i = 0 # keep index where last function ended, s we dont have inf loop
        while m := r.search(eq[i:]):             
            s = m.start()+i
            e = m.end()+i
            name = eq[s:e]
            if re.fullmatch(functionsR, name):
                i=e # update index to end of new function
                continue
            try:
                if float(self.variables[name]) < 0:
                    # -var -> (-var)
                    eq = eq[:s]+'('+self.variables[name]+')'+eq[e:]
                else:
                    eq = eq[:s]+self.variables[name]+eq[e:]
            except KeyError:
                raise VariableError(name, 'VAR IN EQUATION DOESNT EXIST')

        # parse equation to a formated list
        extEq = self.extractEquation(eq)

        for ext, t in extEq:
            if t == 0:
                # ignore if empty/unwanted haracter
                continue
            elif t == -2:
                # if it it is a brace
                if ext == '(':
                    # beginning of an inner equation
                    stack.append('(')
                    beginning = True
                    step += 1
                elif ext == ')':
                    # end of an inner equation
                    while len(stack) > 0 and stack[-1] != '(':
                        ONPeq.append(stack.pop())
                    if stack[-1] == '(':
                        stack.pop()
                    else:
                        raise FormatError(eq, 'BRACES')
                    step -= 1
                    beginning = False
            elif t == -1:
                # if it is an operation
                if beginning:
                    # fix the problem with negative numbers
                    # if this is the beginning of an equation (or equation in braces)
                    # there is nothing to substract from
                    # replacing -x -> 0 x -
                    if ext == '-':
                        ONPeq.append('0')
                        funcStack.append((step, '-'))
                    elif ext == '+':
                        # +x is possible and equivalent to x
                        pass
                    else:
                        raise FormatError(ext, 'UNEXPECTED OPERATION')
                else:
                    # if this is not the beginning
                    # handle adding an operation
                    p = self.getPrirority(ext)
                    while len(stack) > 0:
                        # fix the priority of previous operation
                        px = self.getPrirority(stack[-1])
                        if p >= px:
                            break
                        ONPeq.append(stack.pop())
                    stack.append(ext)
                    beginning=True
            elif t==-3:
                funcStack.append((step, ext))
            else:
                # else it is a number
                ONPeq.append(ext)
                beginning = False
            # fix the problem with negative numbers by replacing -x with 0 x -
            # add the number to ONP equation
            # fix negative numbers if an exists in current step
            if (t == 1 or ext == ')'):
                for s, f in funcStack:
                    if s == step:
                        ONPeq.append(f)
        while len(stack) > 0:
            # add everything what's left
            ONPeq.append(stack.pop())
        return ONPeq

    # function calculates the result given ONP equation
    def calculateONP(self, eq):
        stack = []
        for c in eq:
            t = self.getType(c)
            if t == 1:
                # if it is a number
                stack.append(c)
            elif t == -1:
                # if it is an operation
                if len(stack) < 2:
                    raise CalculationError(eq, 'STACK IS EMPTY')
                v2 = float(stack.pop())
                v1 = float(stack.pop())
                if c == '+':
                    v1 += v2
                elif c == '-':
                    v1 -= v2
                elif c == '*':
                    v1 *= v2
                elif c == '/':
                    v1 /= v2
                elif c == '^':
                    v1 = np.pow(v1,v2)
                    if isinstance(v1, complex):
                        raise CalculationError(eq, 'COMPLEX SOLUTION')
                stack.append(v1)
            elif t == -3:
                if len(stack) < 1:
                    raise CalculationError(eq, 'STACK IS EMPTY')
                v = float(stack.pop()) 
                ang = v if c[-1]=='r' else np.radians(v)
                if c == 'abs':
                    v = np.abs(v)
                if c == 'exp':
                    v = np.exp(v)
                elif c == 'ln':
                    v = np.log(v)
                elif c == 'log2':
                    v = np.log2(v)
                elif c == 'log10':
                    c= np.log10(v)
                elif c == 'sin' or 'sinr':
                    v = np.sin(ang)
                elif c == 'cos' or 'cosr':
                    v = np.cos(ang)
                elif c == 'tg' or 'tgr':
                    v = np.tan(ang)
                elif c == 'ctg' or 'ctgr':
                    v = np.cot(ang)
                elif c == 'sinh' or 'sinhr':
                    v = np.sinh(ang)
                elif c == 'cosh' or 'coshr':
                    v = np.cosh(ang)
                elif c == 'tgh' or 'tghr':
                    v = np.tanh(ang)
                elif c == 'ctgh' or 'ctghr':
                    v = np.coth(ang)
                if np.isnan(v):
                    raise CalculationError(c, 'UNEXPECTED NAN VALUE')
                stack.append(v)

        return stack[0]

    # Fetches data from problem's content
    # all data are saved in self.variables or self.unknowns
    def FetchFromContent(self, text):
        # fetch given variables
        r = re.compile(f'({variableR})=({numberR})')
        for m in r.finditer(text):
            self.variables[m.group(1)] = m.group(2)

        # fetch given range variables
        r = re.compile(f'({variableR})=\[({numberR});({numberR})\]')
        for m in r.finditer(text):
            self.variables[m.group(1)] = str(
                round(random.uniform(float(m.group(2)), float(m.group(3))), 2))

        # fetch asked unknowns
        r = re.compile(f'({variableR})=\?([a-zA-Z_0-9\/*^\(\)]+)?')
        for m in r.finditer(text):
            self.unknowns[m.group(1)] = m.group(2)

    # Executes single line of EquEx format
    def InterpretLine(self, text):
        if text == '':
            # ignore if the line is empty
            return

        # get everything matching pattern
        r = re.compile(f'({variableR})=((?:[\+\-\]|{functionsR}?[\^a-zA-Z_0-9.\(\)]+[\*\/\^]?)+)')
        m = r.match(text)

        # return if match is invaid
        if not r.fullmatch(text):
            raise FormatError(text, 'LINE DOESNT MATCH PATTERN')

        # if no mistakes convert/calculate/update dictionaries
        ONPeq = self.convertToONP(m.group(2))
        val = self.calculateONP(ONPeq)
        self.variables[m.group(1)] = str(val)

    # Executes the whole code
    def Execute(self, text):
        phaze = 0
        for x in text.split('\n'):
            if x == '---':  # indicator of a new type of code
                phaze += 1
            elif phaze == 0:
                # first phaze: parse problem's content
                e.FetchFromContent(x)
            elif phaze == 1:
                # second phaze: execute the rest of code
                e.InterpretLine(x)
        for x in self.unknowns:
            try:
                print(
                    f"{x} -> {float(self.variables[x])} {self.unknowns[x] if self.unknowns[x] != None else ''}")
            except:
                raise VariableError(x, 'UNKNOWN VAR DOESNT EXIST')


# python EquationParser.py < zad.txt
if __name__ == '__main__':
    fname = argv[1] if len(argv)>1 else 'zad.txt'
    e = Equation()
    f = open(fname, 'r', encoding='UTF-8').read()
    e.Execute(f)
