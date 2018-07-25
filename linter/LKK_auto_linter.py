import pickle
import os
import glob
import time
import re

from pathlib import Path
from collections import defaultdict

PATH_LAST_LINTED_MD = "./last_auto_linted_times_md.pkl"
PATH_LAST_LINTED_LESSON_YML = "./last_auto_linted_lesson_yml.pkl"
PATH_SRC = '../src'
PATH_LINTER = './LKK_auto_linter.sh'


def load_last_linted_times(path_2_linted_times):
    linted_times_file = Path(path_2_linted_times)
    if linted_times_file.is_file():
        # file exists
        # read python dict back from the file
        pkl_file = open(path_2_linted_times, 'rb')
        linted_times_ = pickle.load(pkl_file)
        pkl_file.close()
    else:
        linted_times_ = defaultdict(int)
    return linted_times_


def save_last_linted_times(linted_times_, path_2_linted_times):
    # write python dict to a file
    output = open(path_2_linted_times, 'wb')
    pickle.dump(linted_times_, output)
    output.close()


def get_md_files(path):
    return glob.glob(path + '/**/*.md', recursive=True)


def is_oppgave(md_filepath):
    # Every oppgave has a lesson.yml in the same folder
    return path_2_yml_lesson(md_filepath).is_file()


def path_2_yml_lesson(md_filepath):
    return Path(re.sub(r'\w+\.md', 'lesson.yml', md_filepath))


def main():
    last_linted_md_ = load_last_linted_times(PATH_LAST_LINTED_MD)
    last_linted_lesson_yml_ = load_last_linted_times(
        PATH_LAST_LINTED_LESSON_YML)

    for md_file in get_md_files(PATH_SRC):
        # Check if the markdown file has been updated since last linting
        last_modified_md = os.path.getmtime(md_file)
        if last_modified_md > last_linted_md_[md_file]:
            # If so auto lint the file again
            os.system('{} {}'.format(PATH_LINTER, md_file))
            # Update when the file was last linted
            # Note this gives time since epoch (1970), avoids messing with the file timestamp
            last_linted_md_[md_file] = time.time()

            save_last_linted_times(last_linted_md_, PATH_LAST_LINTED_MD)
        if not is_oppgave(md_file):  #Only oppgave files has lesson.yml files
            continue

        yml_lesson_file = path_2_yml_lesson(md_file)
        # Check if the lesson yml file has been updated since last linting
        last_modified_lesson_yml = os.path.getmtime(yml_lesson_file)
        if last_modified_lesson_yml > last_linted_lesson_yml_[yml_lesson_file]:
            os.system('{} {}'.format('python LKK_sorter.py', md_file))
            last_linted_lesson_yml_[yml_lesson_file] = time.time()

            save_last_linted_times(last_linted_lesson_yml_, PATH_LAST_LINTED_LESSON_YML)


if __name__ == "__main__":

    main()
