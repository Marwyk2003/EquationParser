import re
import random
from datetime import datetime
from sys import argv

class FormatError(Exception):
    pass

class Equation:
    def __init__(self):
        self.variables = {}  # dict for all given/calculated variables
        self.unknowns = {}  # dict for all unknowns/querries
        self.seed = random.seed(datetime.now())  # seed for some randomisation

    # returns the type of a string
    def getType(self, c):
        if re.fullmatch('[0-9.]+', c):
            # number (including decimal point)
            return 1
        elif c in '+-*/^':
            # all operations
            return -1
        elif c in '()':
            return -2
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
        r = re.compile('[\-\+\*\/\(\)\^]|[0-9.]+|[a-zA-Z_][a-zA-Z_0-9]*')
        for x in r.findall(eq):
            tab.append((x, self.getType(x)))
        return tab

    # converts regular equation to an ONP list
    def convertToONP(self, eq):
        try:
            stack = []
            ONPeq = []
            negate = []
            beginning = True
            step = 0

            # replace variables with responding values
            r = re.compile('[a-zA-Z_][a-zA-Z_0-9]*')
            while m := r.search(eq):
                name = eq[m.start(): m.end()]
                s = m.start()
                e = m.end()
                try:
                    eq = eq[:s]+self.variables[name]+eq[e:]
                except KeyError:
                    print(f"UNKNOWN VARIABLE: {name}")
                    return

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
                            print(f"MISSING BEGINNING OF A BRACE: {extEq}")

                        # fix the problem with negative numbers by replacing -x with 0 x -
                        step -= 1
                        beginning = False
                        if step in negate:
                            ONPeq.append('-')
                            negate.remove(step)
                elif t == -1:
                    # if it is an operation
                    if beginning:
                        # fix the problem with negative numbers
                        # if this is the beginning of an equation (or equation in braces)
                        # there is nothing to substract from
                        # replacing -x -> 0 x -
                        if ext == '-':
                            ONPeq.append('0')
                            negate.append(step)
                        elif ext == '+':
                            # +x is possible and equivalent to x
                            pass
                        else:
                            print(
                                f"UNEXPECTED OPERATION IN THE BEGINNING OF AN EQUATION: {extEq}")
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
                else:
                    # else it is a number
                    # add the number to ONP equation
                    # fix negative numbers if an exists in current step
                    ONPeq.append(ext)
                    beginning = False
                    if step in negate:
                        ONPeq.append('-')
                        negate.remove(step)
            while len(stack) > 0:
                # add everything what's left
                ONPeq.append(stack.pop())
            return ONPeq
        except:
            print(f"ERROR WHILE CONVERTING TO ONP: {eq}")
            return

    # function calculates the result given ONP equation
    def calculateONP(self, eq):
        try:
            stack = []
            for c in eq:
                t = self.getType(c)
                if t == 1:
                    # if it is a number
                    stack.append(c)
                elif t == -1:
                    # if it is an operation
                    if len(stack) < 2:
                        print(f"NOT ENOUGH ELEMENTS IN STACK: {eq}")
                        return
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
                        v1 **= v2
                    stack.append(v1)
            return stack[0]
        except:
            print(f"ERROR WHILE CALCULATING ONP: {eq}")
            return

    # Fetches data from problem's content
    # all data are saved in self.variables or self.unknowns
    def FetchFromContent(self, text):
        # fetch given variables
        r = re.compile('([a-zA-Z_][a-zA-Z_0-9]*)=([0-9.]+)')
        for m in r.findall(text):
            self.variables[m[0]] = m[1]

        # fetch given range variables
        r = re.compile('([a-zA-Z_][a-zA-Z_0-9]*)=\[([0-9.]+);([0-9.]+)\]')
        for m in r.findall(text):
            self.variables[m[0]] = str(
                round(random.uniform(float(m[1]), float(m[2])), 2))

        # fetch asked unknowns
        r = re.compile('([a-zA-Z_][a-zA-Z_0-9]*)=\?([a-zA-Z_0-9\/*^\(\)]+)')
        for m in r.findall(text):
            self.unknowns[m[0]] = m[1]

    # Executes single line of EquEx format
    def InterpretLine(self, text, lineNum):
        if text == '':
            # ignore if the line is empty
            return

        # get everything matching pattern
        r = re.compile(
            '([a-zA-Z_][a-zA-Z_0-9]*)=([\+\-\*\/\^0-9.a-zA-Z_\(\)]+)')
        m = r.match(text)

        # return if match is invaid
        if not r.fullmatch(text):
            print(f"INVALID FORMAT AT LINE {lineNum}: {text}")
            return

        # if no mistakes convert/calculate/update dictionaries
        ONPeq = self.convertToONP(m.group(2))
        val = self.calculateONP(ONPeq)
        self.variables[m.group(1)] = str(val)

    # Executes the whole code
    def Execute(self, text):
        phaze = 0
        for i, x in enumerate(text.split('\n')):
            if x == '---':  # indicator of a new type of code
                phaze += 1
            elif phaze == 0:
                # first phaze: parse problem's content
                e.FetchFromContent(x)
            elif phaze == 1:
                # second phaze: execute the rest of code
                e.InterpretLine(x, i)
        for x in self.unknowns:
            # print everything we were looking for
            try:
                print(
                    [f'{x} -> {round(float(self.variables[x]), 2)} {self.unknowns[x]}'])
            except:
                print(f"UNKNOWN VARIABLE: {x}")


# python EquationParser.py < zad.txt
if __name__ == '__main__':
    fname = argv[1] if len(argv)>1 else 'zad.txt'
    e = Equation()
    f = open(fname, 'r', encoding='UTF-8').read()
    e.Execute(f)
