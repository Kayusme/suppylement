import arguments
import configuration
import data

import os
import sys


''' Basic program structure
Parse command line arguments. Maybe config file?
Read data file, parse into memory
Perform operation
 - Create
 - Edit
 - View
 - Delete
 - Calculate statistics
Write data to disk, if applicable
Display output'''


class Application():
    def __init__(self, args=None):
        '''This seems like a good place to parse our arguments and decide
        the best course of action. We do not read any data here as some
        argument combinations will not require any to be read (help, version
        information). '''
        self.config = configuration.Configuration(
                '/suppylement_defaults.ini',
                '/suppylement.ini')

        self.reader = data.Data(self.config.read_file,
                self.config.write_file)

        self.arguments = arguments.Arguments()
        # If no args provided, default to command line args
        if args is None:
            # If command line args do not include any mode, default to the
            # value from the ini file, finally default to help mode.
            if len(sys.argv) < 2:
                default_args = self.config.parser.get(
                        'defaults',
                        'custom_args',
                        fallback='-h')
                self.args = self.arguments.parse_args(default_args.split())
            # Command line args are long enough
            else:
                self.args = self.arguments.parse_args(sys.argv[1:])
        # We have been given a custom argument list
        else:
            self.args = self.arguments.parse_args(args)

        self.default_read_args = {
                'index_col': 0
            }

    def display(self):
        '''Parse arguments for specifiers such as limit, order, etc
        Read data from disk
        Format data, if necessary
        Display data'''
        data = self.reader.read_data(**self.default_read_args)

        if self.args.mode == 'list':
            if self.args.most_recent == -1:
                # -1 limit calls for display all data, most recent first
                self.args.most_recent = len(data)
            elif self.args.most_recent < -1 or self.args.most_recent == 0:
                raise ValueError(f'''\
Error: most_recent ({self.args.most_recent}) must be greater than 0''')

            if len(self.args.search_name) > 0:
                data = data[data['name'] == self.args.search_name]

            # Filter rows by 'less than'. Search is exclusive.
            if not self.args.search_less == -1:
                if self.args.search_less < -1 or self.args.search_less == 0:
                    raise ValueError(f'''\
Error: search_less ({self.args.search_less}) must be greater than 0''')
                data = data[data['amount'] < self.args.search_less]

            # Filter rows by 'greater than'. Search is inclusive.
            if not self.args.search_more == -1:
                if self.args.search_more < -1 or self.args.search_more == 0:
                    raise ValueError(f'''\
Error: search_more ({self.args.search_more}) must be greater than 0''')
                data = data[data['amount'] >= self.args.search_more]

            # Calculate the slice start index. Because of the zero
            # indexing, we add one to get the proper length. Then
            # multiply by -1 to invert as we are slicing backwards.
            start = (self.args.most_recent+1) * -1
            data = data.iloc[:start:-1]

        # We did *not* call 'list' mode directly, use defaults.
        else:
            # Go through the data backwards by index, grabbing the last
            # five entries. Not sure exactly why it needs to be offset 1.
            data = data.iloc[:-6:-1]

        print(f'Displaying most recent {len(data)} records...')
        if data is None:
            print('No data to display...')
        else:
            print(data)

    def edit(self):
        '''This would make sense to combine delete then create to simplify
        the function. Need to think through how we call these functions.'''
        data = self.reader.read_data(**self.default_read_args)
        self.reader.write_data()

    def create(self):
        '''Parse arguments for data to be written (e.g. name, amount)
        Determine missing data -- timestamp
        Create row to be appended
        Append row to data file on disk'''
        data = self.reader.read_data(**self.default_read_args)
        try:
            entry_df = self.reader.new_entry(self.args.amount, self.args.name)
        except ValueError as error:
            print(f'ValueError caught!\n{error}')
            print('\n\n  Entry NOT added!\n\n')
        else:
            self.reader.write_data(mode='w')

    def delete(self):
        data = self.reader.read_data(**self.default_read_args)

        # Ensure our ID is greater than 0, less than number of rows
        try:
            success = self.reader.delete_row_by_id(self.args.id_to_remove,
                    self.args.rm_interactive)
        except ValueError as error:
            print(f'ValueError caught!\n{error}')
            print('\n\n  Entry NOT deleted!\n\n')
        else:
            if success:
                print('Entry removed!')
                self.reader.write_data()
            else:
                print('Entry not removed!')

    def run(self):
        '''At this point, we have already created our Data instance and parsed
        arguments. We can begin branching off into different execution modes.
        Certain modes should display the data after the action has been
        performed as a sort of verification. In these cases, just call
        self.display() again.'''
        if self.args.mode == 'list':
            self.display()
        elif self.args.mode == 'edit':
            self.edit()
            self.display()
        elif self.args.mode == 'log':
            self.create()
            self.display()
        elif self.args.mode == 'rm':
            self.delete()
            self.display()
        elif self.args.mode == 'stats':
            print('statistics')
        else:
            print('Unknown mode')
