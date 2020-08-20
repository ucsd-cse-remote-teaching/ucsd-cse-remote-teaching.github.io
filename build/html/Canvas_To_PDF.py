'''Canvas_To_PDF.py: Uses Canvas exam data to generate pdf(s) for uploading to Gradescope.'''
__author__ = 'Laura Xu and Sabeel Mansuri'

##############
# PARAMETERS #
##############
response_csv = 'responses.csv'  # File downloaded using 'Student Analysis Report' button
title = 'Score Report'          # Title displayed at top of each student's PDF
frq_questions = []              # List of all questions (and versions) that are FRQ. Ex: ['Q1A', 'Q1B', 'Q5A', 'Q5B']
# List of all questions (and versions) that are Fill In Multiple Blanks.
# FIMB questions are formatted identically to Multiple Answers questions in the CSV.
fimb_questions = []
versioned = {}                  # Dict where each:
                                #   - key is a string in the format Q# where # is the question number
                                #   - value is an int representing the number of versions for that question
                                # Any omitted questions are assumed to have one version (which must be tagged as Q#A)
                                # Ex: {'Q1':2, 'Q4':3, 'Q5':2}

#############################
# SCRIPT - no need to edit! #
#############################
import os, html, csv, pdfkit, functools, string

name_col = 0
pid_col = 2
attempt_col = 7
pid_to_name = {}
pid_to_col_to_response = {}
col_to_qid = {}

# Track how many FIMB answers there are for a FIMB question
# Needed to generate the template with the correct number of empty slots
fimb_slots = {}

print("Starting PDF generation...\nThis should take less than one minute")
# Parse CSV
with open(response_csv) as f:
    responses = csv.reader(f, delimiter=',',escapechar='\\')

    # Determine col with actual questions and save student responses
    for row in responses:
        # header row
        if row[name_col] == 'name':
            for i,header in enumerate(row):
                if ':' in header:
                    col_to_qid[i] = header
                elif header == 'attempt':
                    col_to_qid[i] = header
            continue
        
        name = row[name_col]
        pid = row[pid_col]

        # Handle multiple submissions (take latest)
        if pid in pid_to_name:
            # Everything is stored as a string, so convert it to a number to compare first
            # Otherwise "10" <= "9"
            if int(pid_to_col_to_response[pid][attempt_col]) > int(row[attempt_col]):
                continue

        pid_to_name[pid] = name
        pid_to_col_to_response[pid] = {}
        for col in col_to_qid.keys():
            response = row[col]
            if not response.strip():
                response = '(empty)'
            pid_to_col_to_response[pid][col] = response

header_html = '''<!DOCTYPE html>
<html>
<head>
    <style>
        @media all {
        .page-break { display: block; page-break-before: always; }
        }

        h1, h2, h3, h4, h5, th {
            font-family: "proxima-nova", "Proxima Nova", "Helvetica Neue", Helvetica, sans-serif;
        }

        table {
          padding: 12px;
          font-size:16px;
          width:1000px;
          border-collapse: collapse;
          table-layout: fixed;
        }



        td {
            border: 2px solid gray;
            font-family: "Comic Sans MS", cursive, sans-serif;
            padding: 12px;
            vertical-align: top;
            white-space:pre;
            width:100%;
            word-break: break-all;
            word-wrap: break-word;
        }
        td div {
            overflow: hidden;         
            text-overflow: ellipsis;
        }

        div.frq {
            height: 1500px; 
            max-height: 1500px;
        }
        
        </style>
</head>
<body>'''

page_break_html = '<div class="page-break"></div>'
footer_html = '</body></html>'

# Descending question order
def question_sort(a, b):
    if int(a[1:-1]) != int(b[1:-1]):
        return -1 if int(a[1:-1]) < int(b[1:-1]) else 1
    else:
        return -1 if a[-1] < b[-1] else 1

# Get HTML for each student
def get_html(pid, is_last=False, is_template=False):
    if is_template:
        name = ' '
    else:
        name = pid_to_name[pid]
    sub_html = '<h1>' + title + '</h1><h2>Name:</h2><table><tr><td>' + name + '</td></tr></table><h2>PID:</h2><table><tr><td>' + pid + '</td></tr></table>'
    to_append = {}
    for col in col_to_qid.keys():
        qid = col_to_qid[col]
        try:
            qid = qid.split(':')[1].strip().splitlines()[0]
        except IndexError:
            continue
        if is_template:
            response = ' '
        else:
            response = pid_to_col_to_response[pid][col]
        
        to_append[qid] = ''.join(filter(lambda x: x in string.printable, response))
    
    for q_key in sorted(to_append.keys(), key=functools.cmp_to_key(question_sort)):
        q_key_pre = q_key[:-1]
        q_key_ver = q_key[-1]
        if q_key_ver != 'A':
            continue
        sub_html += '<h2>' + q_key[:-1] + '</h2><table><tr>'
        # ALL versioned questions
        if q_key_pre in versioned:
            num_vers = versioned[q_key_pre]

            for v in range(num_vers):
                sub_html += '<th><div>Version ' + chr(ord('A') + v) + '</div></th>'
            sub_html += '</tr><tr>'

            # Handle multi-versioned FIMB questions specially
            if q_key in fimb_questions:
                # Determine version that contains the answer
                # Take the first one we see that isn't blank
                ans_ver = -1
                for v in range(num_vers):
                    q_key_check = q_key_pre + str(chr(ord('A') + v))
                    if to_append[q_key_check] != '(empty)' and to_append[q_key_check] != ' ':
                        ans_ver = v
                        break

                # For template.html, need to know how many answers
                # REQUIRES going through submissions first to calculate the # of slots,
                # otherwise fimb_slots is blank
                # Make an empty table with #rows = calculated #, #cols = num_vers
                if ans_ver == -1:
                    for s in range(fimb_slots[q_key_pre]):
                        if s > 0:
                            sub_html += '</tr>'
                        for v in range(num_vers):
                            sub_html += '<td><div> </div></td>'
                        if fimb_slots[q_key_pre] > 1 and s < fimb_slots[q_key_pre]:
                            sub_html += '<tr>'

                # Delimit the answer by ','
                # Calculate how many slots are needed
                else:
                    fimb_answers = to_append[q_key_check].split(',')
                    fimb_slots[q_key_pre] = len(fimb_answers)

                    for ind,curr_ans in enumerate(fimb_answers,0):
                        if ind > 0:
                            sub_html += '</tr>'

                        # Multi-versions: 
                        # Manually insert '(empty)' into any slots that aren't for the correct version
                        for v in range(num_vers):
                            if v == ans_ver:
                                sub_html += '<td><div>' + curr_ans + '</div></td>'
                            else:
                                sub_html += '<td><div>(empty)</div></td>'

                        if len(fimb_answers) > 1 and ind < len(fimb_answers):
                            sub_html += '<tr>'

            # multi-versioned non-FIMB questions
            else:
                for v in range(num_vers):
                    sub_html += '<td><div>' + to_append[q_key_pre + str(chr(ord('A') + v))] + '</div></td>'

        # FRQs
        elif q_key in frq_questions:
            sub_html += '<td><div class="frq">' + to_append[q_key] + '</div></td>'

        # Single-versioned FIMB
        elif q_key in fimb_questions:
            # For template.html, need to know how many answers
            if to_append[q_key] == ' ':
                for s in range(fimb_slots[q_key_pre]):
                    if s > 0:
                        sub_html += '</tr>'
                    sub_html += '<td><div> </div></td>'
                    if fimb_slots[q_key_pre] > 1 and s < fimb_slots[q_key_pre]:
                        sub_html += '<tr>'
            
            # For submissions.html, #answers is calculated by splitting
            else:
                fimb_answers = to_append[q_key].split(",")
                fimb_slots[q_key_pre] = len(fimb_answers)
                for ind,curr_ans in enumerate(fimb_answers,0):
                    if ind > 0:
                        sub_html += '</tr>'
                    sub_html += '<td><div>' + curr_ans + '</div></td>'
                    if len(fimb_answers) > 1 and ind < len(fimb_answers):
                        sub_html += '<tr>'
        
        # All other types of questions
        else:
            sub_html += '<td><div>' + to_append[q_key] + '</div></td>'
        sub_html += '</tr></table>'
    if not is_last:
        sub_html += page_break_html
    return sub_html

all_html = header_html
for i,pid in enumerate(pid_to_name.keys()):
    if i == len(pid_to_name) - 1:
        all_html += get_html(pid, True)
    else:
        all_html += get_html(pid)
    
all_html += footer_html
template_html = header_html + get_html(' ', True, True) + footer_html

f = open('./submissions.html', 'w')
f.write(all_html)
f.close()
pdfkit.from_file('./submissions.html', './submissions.pdf')

f = open('./template.html', 'w')
f.write(template_html)
f.close()
pdfkit.from_file('./template.html', './template.pdf')
