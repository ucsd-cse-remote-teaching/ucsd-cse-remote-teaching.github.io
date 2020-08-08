## Basic Info
The webpage is hosted on [ucsd-cse-remote-teaching.github.io](https://ucsd-cse-remote-teaching.github.io/build/html/index.html).

## Instructions
### Setup
To get started, you need to:
1. Clone this GitHub repository to your local machine
2. Run `make html` in the project's parent directory, which will create the website using the `.md` files in the source directory. If this works, you're all set! If this does not, continue to the next step.
3. Run `pip install sphinx`, then run `pip install recommonmark`, then `pip install sphinx-markdown-tables`, and finally run `pip install sphinx-rtd-theme`. Try running `make html` again. If this fails, let me know (it should not).


### Development
To create a new page (and automatically link it to the sidebar and homepage) you need to perform the following steps on your local machine:
1. Create a new `.md` file under the `source` directory and add whatever content you want.
2. Open `index.rst` and add the name of the `.md` file you created to the existing list. Indentation matters!
3. When you want to view your changes, run `make html` in the project's parent directory. This will generate `.html` files in the `build/html` directory.
4. Once you are completely done developing a lesson, **run `make html` one last time** and then push your changes to GitHub.
