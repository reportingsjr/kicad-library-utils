#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from schlib import *
from print_color import *
from rules import *

parser = argparse.ArgumentParser(description='Execute checkrule scripts checking 3.* KLC rules in the libraries')
parser.add_argument('libfiles', nargs='+')
parser.add_argument('-c', '--component', help='check only a specific component (implicitly verbose)', action='store')
parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
parser.add_argument('--nocolor', help='does not use colors to show the output', action='store_true')
parser.add_argument('--enable-extra', help='enable extra checking', action='store_true')
parser.add_argument('--ignore-errors', help='json file with all errors to be ignored')
parser.add_argument('--json-errors', help='create json file with all errors with supplied argument as filename')
parser.add_argument('--silent', help='only print when a component has violations', action='store_true')
parser.add_argument('-v', '--verbose', help='show status of all components and extra information about the violation', action='count')
args = parser.parse_args()

printer = PrintColor(use_color = not args.nocolor)

if args.ignore_errors:
    with open(args.ignore_errors) as ignore_file:
        ignored_errors = json.load(ignore_file)
else:
    ignored_errors = {}

# dict set up as:
# library is the key and the value is a dict of components with errors
# each component dict has the component as the key and a list of errors as the value
errors = {}

# force to be verbose if is looking for a specific component
if not args.verbose and args.component: args.verbose = 1

# get all rules
all_rules = []
for f in dir():
    if f.startswith('rule'):
        all_rules.append(globals()[f].Rule)

# gel all extra checking
all_ec = []
for f in dir():
    if f.startswith('EC'):
        all_ec.append(globals()[f].Rule)

for libfile in args.libfiles:
    lib = SchLib(libfile)
    # create dict to store components and their errors for this library
    errors[libfile] = {}
    n_components = 0
    if not args.silent:
        printer.purple('library: %s' % libfile)
    for component in lib.components:
        # skip components with non matching names
        if args.component and args.component != component.name: continue
        n_components += 1

        if not args.silent:
            printer.green('checking component: %s' % component.name)

        # create list to store errors for this component
        errors[libfile][component.name] = []

        # check the rules
        n_violations = 0
        for rule in all_rules:
            rule = rule(component)
            if ignored_errors:
                if libfile in ignored_errors:
                    if component.name in ignored_errors[libfile]:
                        if rule.name in ignored_errors[libfile][component.name]:
                            # skip this rule check
                            continue
            if rule.check():
                n_violations += 1
                if not args.silent:
                    printer.yellow('Violating ' +  rule.name, indentation=2)
                errors[libfile][component.name].append(rule.name)
                if args.verbose:
                    printer.light_blue(rule.description, indentation=4, max_width=100)

                    # example of customized printing feedback by checking the rule name
                    # and a specific variable of the rule
                    # note that the following text will only be printed when verbosity level is greater than 1
                    if rule.name == 'Rule 3.1' and args.verbose:
                        for pin in rule.violating_pins:
                            printer.red('pin: %s (%s), posx %s, posy %s' %
                                       (pin['name'], pin['num'], pin['posx'], pin['posy']), indentation=4)

                    if rule.name == 'Rule 3.2' and args.verbose:
                        for pin in rule.violating_pins:
                            printer.red('pin: %s (%s), length %s' %
                                       (pin['name'], pin['num'], pin['length']), indentation=4)

                    if rule.name == 'Rule 3.8' and args.verbose:
                        if rule.only_datasheet_missing:
                            printer.brown("[warn] Please provide a datasheet link if it isn't a generic component",
                                          indentation=4)

            if args.fix:
                rule.fix()

        # extra checking
        if args.enable_extra:
            for ec in all_ec:
                ec = ec(component)
                if ignored_errors:
                    if libfile in ignored_errors:
                        if component.name in ignored_errors[libfile]:
                            if ec.name in ignored_errors[libfile][component.name]:
                                # skip this rule check
                                continue
                if ec.check():
                    n_violations += 1
                    errors[libfile][component.name].append(ec.name)
                    if not args.silent:
                        printer.yellow('Violating ' +  ec.name, indentation=2)

                    if args.verbose:
                        printer.light_blue(ec.description, indentation=4, max_width=100)

                        if ec.name == 'EC01 - Extra Checking':
                            for pin in ec.probably_wrong_pin_types:
                                printer.red('pin %s (%s): %s' %
                                        (pin['name'], pin['num'], pin['electrical_type']), indentation=4)

                        if ec.name == 'EC03 - Extra Checking':
                            if ec.fp_is_missing:
                                printer.brown("[warn] Symbol doesn't have footprint field, please re-save it using KiCad",
                                              indentation=4)

                if args.fix:
                    ec.fix()

        # check the number of violations
        if n_violations == 0:
            if not args.silent:
                printer.light_green('No violations found', indentation=2)
        else:
            printer.green('checking component: %s' % component.name)
            for i in errors[libfile][component.name]:
                printer.yellow('Violating ' +  i, indentation=2)

    if args.fix:
        lib.save()

if args.json_errors:
    # open new json file for writing errors in json format
    errors_file = open(args.json_errors, 'w')
    json.dump(errors, errors_file)
    errors_file.close()
