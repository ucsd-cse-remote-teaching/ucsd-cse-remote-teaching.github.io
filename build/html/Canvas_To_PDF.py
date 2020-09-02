'''Canvas_To_PDF.py: Uses Canvas exam data to generate pdf(s) for uploading to Gradescope.'''
__author__ = 'Laura Xu, Sabeel Mansuri, and Erika Auyeung'

##############
# PARAMETERS #
##############
response_csv = 'responses.csv'  # File downloaded using 'Student Analysis Report' button
title = 'Score Report'          # Title displayed at top of each student's PDF
frq_questions = []              # List of all questions (and versions) that are FRQ. Ex: ['Q1A', 'Q1B', 'Q5A', 'Q5B']
# List of all questions (and versions) that are Fill In Multiple Blanks OR Multiple Dropdowns.
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
import os, html, csv, pdfkit, functools, string, math

name_col = 0
pid_col = 2
attempt_col = 7
pid_to_name = {}
pid_to_col_to_response = {}
col_to_qid = {}

# Track how many FIMB answers there are for a FIMB question
# Needed to generate the template with the correct number of empty slots
fimb_slots = {}

# Track max height of every question (how many lines it takes up)
# Necessary for when answers are different lengths to ensure each HTML/PDF,
# especially `template.html`, has space for the longest answer
q_heights = {}

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

# A monospaced font is used in order to facilitate calculating question heights
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
            font-family: "Lucida Console", Monaco, monospace;
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

# get height of each question
# max monospaced characters per line, if n = #versions
#   math.floor(100/n)-3
# works at least up to n=4
def get_question_width(n):
    return math.floor(100/n)-3

def get_question_heights(pid):
    to_append = {}
    for col in col_to_qid.keys():
        qid = col_to_qid[col]
        try:
            qid = qid.split(':')[1].strip().splitlines()[0]
        except IndexError:
            continue
        response = pid_to_col_to_response[pid][col]

        to_append[qid] = ''.join(filter(lambda x: x in string.printable, response))
    
    for q_key in sorted(to_append.keys(), key=functools.cmp_to_key(question_sort)):
        q_key_pre = q_key[:-1]
        q_key_ver = q_key[-1]

        if q_key_pre in versioned:
            num_vers = versioned[q_key_pre]
        else:
            num_vers = 1
        
        q_width = get_question_width(num_vers)

        # handle fimb questions, which are split up into multiple rows,
        # each with their own height
        if q_key in fimb_questions:
            # Get answers for this question
            fimb_answers = to_append[q_key].split(',')
            # Check to find the largest #answers
            if q_key_pre not in fimb_slots or fimb_slots[q_key_pre] < len(fimb_answers):
                fimb_slots[q_key_pre] = len(fimb_answers)
            # For each answer, calculate the height for its individual box
            for i in range(len(fimb_answers)):
                q_length = len(fimb_answers[i])
                q_height = math.floor(q_length/q_width)
                q_key_fimb = q_key_pre + "_" + str(i)
                # Find the longest answer
                if q_key_fimb not in q_heights or q_height > q_heights[q_key_fimb]:
                    q_heights[q_key_fimb] = q_height
        # non-fimb questions - only a single cell to calculate height for
        else:
            q_length = len(to_append[q_key])
            q_height = math.floor(q_length/q_width)
            if q_key_pre not in q_heights or q_height > q_heights[q_key_pre]:
                q_heights[q_key_pre] = q_height

# template_height: templated height, either q_heights[q_key_pre] or q_heights[q_key_fimb]
# answer_text: text of the answer. Either to_append[...]/curr_ans or '' when used in a template
# num_vers: number of versions of this question, used to calculate width of the column
def get_templated_height_html(template_height, answer_text, num_vers):
    return_html = ""
    if template_height > 0:
        return_html += '<td><div>' + answer_text
        q_height = math.floor(len(answer_text)/get_question_width(num_vers))
        for i in range(template_height + 1 - q_height):
            return_html += '\n'
        return_html += '</div></td>'
    else:
        return_html += '<td><div>' + answer_text + ' </div></td>'
    return return_html

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
                if is_template:
                    for s in range(fimb_slots[q_key_pre]):
                        if s > 0:
                            sub_html += '</tr>'
                        for v in range(num_vers):
                            # each row has its own height
                            q_key_fimb = q_key_pre + '_' + str(s)
                            sub_html += get_templated_height_html(q_heights[q_key_fimb], '', 1)
                        
                        if fimb_slots[q_key_pre] > 1 and s < fimb_slots[q_key_pre]:
                            sub_html += '<tr>'

                # Delimit the answer by ','
                # Calculate how many slots are needed
                else:
                    fimb_answers = to_append[q_key_check].split(',')
                    #fimb_slots[q_key_pre] = len(fimb_answers)

                    for ind,curr_ans in enumerate(fimb_answers,0):
                        if ind > 0:
                            sub_html += '</tr>'

                        # Multi-versions: 
                        # Manually insert '(empty)' into any slots that aren't for the correct version
                        for v in range(num_vers):
                            if v == ans_ver:
                                sub_html += '<td><div>' + curr_ans + '</div></td>'
                            else:
                                # insert appropriate # of newlines as needed to extend to template length
                                q_key_fimb = q_key_pre + '_' + str(ind)
                                sub_html += get_templated_height_html(q_heights[q_key_fimb], '(empty)', 1)

                        if len(fimb_answers) > 1 and ind < len(fimb_answers):
                            sub_html += '<tr>'

            # multi-versioned non-FIMB questions
            else:
                for v in range(num_vers):
                    # insert appropriate # of newlines as needed to extend to template length
                    sub_html += '<td><div>' + to_append[q_key_pre + str(chr(ord('A') + v))] + '</div></td>'

        # FRQs
        elif q_key in frq_questions:
            sub_html += '<td><div class="frq">' + to_append[q_key] + '</div></td>'

        # Single-versioned FIMB
        elif q_key in fimb_questions:
            # For template.html, need to know how many answers
            if is_template:
                for s in range(fimb_slots[q_key_pre]):
                    if s > 0:
                        sub_html += '</tr>'
                    q_key_fimb = q_key_pre + '_' + str(s)
                    sub_html += get_templated_height_html(q_heights[q_key_fimb], '', 1)
                    if fimb_slots[q_key_pre] > 1 and s < fimb_slots[q_key_pre]:
                        sub_html += '<tr>'
            
            # For submissions.html, #answers is calculated by splitting
            else:
                fimb_answers = to_append[q_key].split(',')
                for ind,curr_ans in enumerate(fimb_answers,0):
                    if ind > 0:
                        sub_html += '</tr>'
                    # insert appropriate # of newlines as needed to extend to template length
                    q_key_fimb = q_key_pre + '_' + str(ind)
                    sub_html += get_templated_height_html(q_heights[q_key_fimb], curr_ans, 1) 
                    if len(fimb_answers) > 1 and ind < len(fimb_answers):
                        sub_html += '<tr>'
        
        # All other types of questions, single-versioned
        else:
            # insert appropriate # of newlines as needed to extend to template length
            if is_template:
                sub_html += get_templated_height_html(q_heights[q_key_pre], '', 1)
            else:
                sub_html += get_templated_height_html(q_heights[q_key_pre], to_append[q_key], 1)
        sub_html += '</tr></table>'
    if not is_last:
        sub_html += page_break_html
    return sub_html

# Calculate all question heights so that all boxes are consistent across
# all submissions and the template
for pid in pid_to_name.keys():
    get_question_heights(pid)

# Generate the HTML to form the submissions
all_html = header_html
for i,pid in enumerate(pid_to_name.keys()):
    if i == len(pid_to_name) - 1:
        all_html += get_html(pid, True)
    else:
        all_html += get_html(pid)
    
all_html += footer_html

# Generate the HMTL for the template
template_html = header_html + get_html(' ', True, True) + footer_html

# Write the submissions HTML into a PDF
print("Generating submission.html")
f = open('./submissions.html', 'w')
f.write(all_html)
f.close()
pdfkit.from_file('./submissions.html', './submissions.pdf')

# Write the template HTML into a PDF
print("Generating template.html")
f = open('./template.html', 'w')
f.write(template_html)
f.close()
pdfkit.from_file('./template.html', './template.pdf')
