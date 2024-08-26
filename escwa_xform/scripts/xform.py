# Transforms an MRK file as per specifacations

import sys, re, string
from datetime import date
from argparse import ArgumentParser
from dlx import DB, Config
from dlx.marc import BibSet, Bib, Auth, Linked

def get_args():
    parser = ArgumentParser()
    parser.add_argument('--connect', help='', required=True)
    parser.add_argument('--database', help='', required=True)
    parser.add_argument('--input_file', help='The MRK file to convert', required=True)
    parser.add_argument('--output_file', help='Path to write the output file to')
    parser.add_argument('--write_db', action='store_true', help='Commit the records directly to the DB')
    
    return parser.parse_args()

def run():
    args = get_args()
    DB.connect(args.connect, database=args.database)

    if path := args.output_file:
        OUT = open(path, '+')

    with open(args.input_file, 'r') as IN:
        text = IN.read()
        bibs = BibSet.from_mrk(text, auth_control=False)

        for bib in bibs.records:
            if 'eng' not in bib.get_values('041', 'a'):
                continue

            bib = xform(bib)

            if args.output_file:
                OUT.write(bib.to_mrk(write_id=False))
            elif args.write_db:
                # confirm?
                print(bib.to_mrk())
                prompt = input('import record? y/n: ')

                if prompt.lower() == 'y':
                    bib.commit(user='ESCWAi')
                    print(f'Imported with bib# {bib.id}\n')
            else:
                print(bib.to_mrk())

    if args.output_file:
        OUT.close()       

def xform(record):
    # 092/191
    for field in record.get_fields('092'):
        # check if the symbol exists
        if Bib.from_query({'191.subfields.value': field.get_value('a')}, projection={'_id': 1}):
            continue

        field.tag = '191'
        field.subfields = [x for x in field.subfields if x.code != 'b']
        #field.set('b', 386566, auth_control=True)
        field.subfields.append(Linked(code='b', xref=386566))

    # 110/710
    for field in record.get_fields('110'):
        field.tag = '710'

    # 260/264
    for field in record.get_fields('264'):
        if record.get_field('260'):
            record.delete_field(field)
        else:
            field.tag = '260'
        
        _260 = record.get_field('260')
        _260.set('a', _260.get_value('a') + ' :')
        _260.set('b', _260.get_value('b') + ';')

    # 269
    record.set('269', 'a', record.get_value('260', 'c'))

    # 651
    for field in record.get_fields('651'):
        field.tag = '650'

    # 999
    datestr  = date.today().isoformat().replace('-', '')
    record.set('999', 'a', f'ESCWAi{datestr}', address='+')
    place = len(record.get_fields('999')) - 1
    record.set('999', 'b', datestr, address=[place])
    record.set('999', 'c', 'i', address=[place])

    # assign auths
    for field in record.datafields:
        field = assign_auth(field)

    return record

def assign_auth(field):
    if subfields := [x for x in field.subfields if Config.is_authority_controlled('bib', field.tag, x.code)]:
        for subfield in [x for x in subfields if not isinstance(x, Linked)]:
            subfield.value = re.sub(r'\.([^\s])', r'. \1', subfield.value) # values might not have spaces after period

        if xref := Auth.resolve_ambiguous(tag=field.tag, subfields=subfields, record_type='bib'):
            field.subfields = [x for x in field.subfields if x.code != '9'] # escwa's xref

            for subfield in subfields:
                subfield.xref = xref
        else:
            # set to a non auth controlled field
            field.set('x', field.tag)
            field.tag = '917'

###

if __name__ == '__main__':
    run()
