# Canvas + Gradescope Workflow

## What is this?
This workflow allows you to deliver exams and quizzes to students using Canvas, but use Gradescope for grading, feedback, and distribution.

<sup>[I've heard enough, just tell me how to implement this!](#implementation-level)</sup>

## Why should I use this?
Canvas provides an excellent interface for delivering exams with benefits ranging from question banking and a wide range of question types to platform familiarity for students. Canvas's grading tools, however, are sluggish at best and erroneous at worst. Gradescope, on the other hand, offers minimal support for delivering exams but has excellent and reliable grading tools.

This workflow allows you to get the best of both softwares; students can take exams directly on Canvas, and you can use this workflow to generate a Gradescope-friendly PDF score report for grading purposes.

## How do I implement this?
### High-Level
Create and deliver an exam (i.e. Quiz) on Canvas as you normally would. The only change is that each question (and version) will need to be tagged with a unique identifier following a specifc format for downstream parsing. Students will take this exam normally.

Download the exam data from Canvas and feed it to our lightweight Python script. The script will process the exam data and output two key files:
1. `submissions.pdf` - A PDF document containing parsed student responses. Each page (or group of multiple pages for longer exams) corresponds to one student
2. `template.pdf` - A PDF document used by Gradescope's software to correctly parse `submissions.pdf`

Create a new Gradescope assignment, upload each of the files, and let Gradescope's software process everything for you. After Gradescope is done, use the **Grade Submissions** dashboard to grade hundreds of student submissions in minutes.

### Implementation-Level
#### Requirements
There are only a few requirements for using this workflow:
* The Python script must be run using Python3.
* The Python script supports the most common question types (full list of supported types is below). Other types may or may not work; we recommend testing them yourself first.
* The script uses the following Python libraries: `os`, `html`, `csv`, `pdfkit`, `functools`, and `string`. You should only have to download `pdfkit` and `functools` (using `pip`).
* The script assumes that no student response to a Free Response question will span more than half the height of a normal 8.5x11 size sheet of paper. You may want to explicitly state that students' should answer concisely (e.g. Limit your answer to no more than X lines (where X ≤ 30)).

#### Step-by-step Process
The workflow has little-to-no overhead and is quick to implement. We have split it into many small steps for clarity.

##### Setting up Canvas
1. Create a Canvas Quiz as you normally would. You can specify whatever settings you would like, but make sure only to use the following question types: `Multiple Choice`, `Multiple Select`, `Short Answer`, `Numerical Answer`, and `Free Response`. 

2. For each question you create, you must reserve the first line for a question identifier used by our script. This identifier should be the only thing on this line; you can start writing the actual question from the second line.

3. The identifier must be in the format `Q#_` where `#` is the question number (1, 2, ... 20, ...), and `_` is the version. The first version should be tagged with `A`, the second with `B`, and so on. For example, the first question in your exam will always be tagged as `Q1A`. If it has multiple versions, you would also have `Q1B`, `Q1C`, and so on. Otherwise, you would move on to `Q2A`. *Note: By "version", we mean that the question is part of a Canvas Question Group in which each student will see one question in that group.*

4. Double check that you did Step 2 correctly. A missing identifier will cause the script to crash. *Note: If this does happen to you, you can recover by editing the exported Canvas data file directly to add the identifier.*

5. Administer the exam per usual.

##### Extracting and Parsing Canvas Exam Data
1. TODO
2. In the top right corner of the page, click **Student Analysis Report**. This will begin downloading the exam data onto your computer. *Note: This will likely download with a long name. You may want to rename it to something like `responses.csv` to make your life a bit easier in the next couple steps.*
3. Download (or copy-paste) the `Canvas_To_PDF.py` Python script from [here](Canvas_To_PDF.py). Open the script in a text editor of your choice. You will only need to worry about the section of the script titled **PARAMETERS**.
4. Set the `response_csv` variable to the location of the `.csv` file you downloaded from Canvas. For example: `response_csv = ~/Downloads/responses.csv`.
5. (Optional) Set the `title` variable to the 
6. Add any Free Response questions to the list represented by the `frq_questions` variable. You should add strings containing their identifiers. For example, `['Q1A', 'Q1B', 'Q5A', 'Q5B']`.
7. Add any versioned questions to the dict represented by the `versioned` variable. Each key should be a string (without a version) in the format `Q#` where `#` is the question number, and the corresponding value should be an int representing the number of versions for that question. For example, `{'Q1':2, 'Q4':3, 'Q5':2}`.
8. Confirm the parameters are correct. Then, simply run the script using Python3: `python3 Canvas_To_PDF.py`.

##### Gradescope Magic
TODO


#### Additional notes
* If you allow multiple submissions, the script will only generate one PDF for each student corresponding to their most recent submission
