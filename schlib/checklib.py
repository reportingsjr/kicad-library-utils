#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from schlib import *
from print_color import *
from rules import *

parser = argparse.ArgumentParser(description='Execute checkrule scripts checking 3.* KLC rules in the libraries')
parser.add_argument('libfiles', nargs='+')
parser.add_argument('-c', '--component', help='check only a specific component (implicitly verbose)', action='store')
parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
parser.add_argument('--nocolor', help='does not use colors to show the output', action='store_true')
parser.add_argument('-v', '--verbose', help='show status of all components and extra information about the violation', action='count')
args = parser.parse_args()

printer = PrintColor(use_color = not args.nocolor)

# force to be verbose if is looking for a specific component
if not args.verbose and args.component: args.verbose = 1

# get all rules
all_rules = []
for f in dir():
    if f.startswith('rule'):
        all_rules.append(globals()[f].Rule)

for libfile in args.libfiles:
    lib = SchLib(libfile)
    n_components = 0
    printer.purple('library: %s' % libfile)
    for component in lib.components:
        # skip components with non matching names
        if args.component and args.component != component.name: continue
        n_components += 1

        printer.green('checking component: %s' % component.name)

        n_violations = 0
        for rule in all_rules:
            rule = rule(component)
            if rule.check():
                n_violations += 1
                printer.yellow('Violating ' +  rule.name, indentation=2)
                if args.verbose:
                    printer.light_blue(rule.description, indentation=4, max_width=100)

                    # example of customized printing feedback by checking the rule name
                    # and a specific variable of the rule
                    # note that the following text will only be printed when verbosity level is greater than 1
                    if rule.name == 'Rule 3.1' and args.verbose > 1:
                        for pin in rule.violating_pins:
                            printer.red('pin: %s (%s), posx %s, posy %s' %
                                       (pin['name'], pin['num'], pin['posx'], pin['posy']), indentation=4)

                    if rule.name == 'Rule 3.2' and args.verbose > 1:
                        for pin in rule.violating_pins:
                            printer.red('pin: %s (%s), length %s' %
                                       (pin['name'], pin['num'], pin['length']), indentation=4)

            if args.fix:
                rule.fix()

        if n_violations == 0:
            printer.light_green('No violations found', indentation=2)

    if args.fix:
        lib.save()
