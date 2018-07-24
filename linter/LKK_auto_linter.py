import pickle
import os
import glob
import time
import re

from pathlib import Path
from collections import defaultdict

PATH_2_LAST_LINTED_TIMES = "./last_auto_linted_times.pkl"
PATH_2_SRC = '../src'
PATH_2_LINTER = './LKK_auto_linter.sh'


def load_last_modified_times():
    linted_times_file = Path(PATH_2_LAST_LINTED_TIMES)
    if linted_times_file.is_file():
        # file exists
        # read python dict back from the file
        pkl_file = open(PATH_2_LAST_LINTED_TIMES, 'rb')
        linted_times_ = pickle.load(pkl_file)
        pkl_file.close()
    else:
        linted_times_ = defaultdict(int)
    return linted_times_


def save_last_modified_times(linted_times_):
    # write python dict to a file
    output = open(PATH_2_LAST_LINTED_TIMES, 'wb')
    pickle.dump(linted_times_, output)
    output.close()


def get_md_files(path):
    return glob.glob(path + '/**/*.md', recursive=True)


def is_oppgave(filepath):
    # Every oppgave has a lesson.yml in the same folder
    yml_path = Path(re.sub(r'\w+\.md', 'lesson.yml', filepath))
    return yml_path.is_file()


def main():
    linted_times_ = load_last_modified_times()
    md_files = get_md_files(PATH_2_SRC)

    for md_file in md_files:
        # Check if the file has been updated since last linting
        last_modified_time = os.path.getmtime(md_file)
        if last_modified_time > linted_times_[md_file]:
            # If so auto lint the file again
            os.system('{} {}'.format(PATH_2_LINTER, md_file))
            # If so auto lint the file again
            if is_oppgave(md_file):
                os.system('{} {}'.format('python LKK_sorter.py', md_file))

            # Update when the file was last linted
            # Note this gives time since epoch (1970), avoids messing with the file timestamp
            linted_times_[md_file] = time.time()
    save_last_modified_times(linted_times_)


if __name__ == "__main__":

    main()
