import glob
import os
import pickle
import re
import time

from collections import defaultdict
from pathlib import Path
from termcolor import colored

# KEYS START HERE (DO NOT REMOVE THESE LINES)
LANGUAGE = "nb|nn|en"
TOPIC = "app|electronics|step_based|block_based|text_based|minecraft|web|game|robot|animation|sound|cryptography"
SUBJECT = "mathematics|science|programming|technology|music|norwegian|english|arts_and_crafts|social_science"
GRADE = "preschool|primary|secondary|junior|senior"
# KEYS END HERE (DO NOT REMOVE THESE LINES)

PATH_2_ERROR_FREE_LESSON_YML = "./error_free_lesson_yml.pkl"
PATH_2_SRC = '../src'

tags_ = dict(
    level="[1-4]",  #Change this line to change the max allowed level
    topic=TOPIC,
    subject=SUBJECT,
    grade=GRADE,
)


def load_error_free_yml(path_2_error_free_lesson_yml):
    error_free_yml = Path(path_2_error_free_lesson_yml)
    if error_free_yml.is_file():
        # file exists
        # read python dict back from the file
        pkl_file = open(path_2_error_free_lesson_yml, 'rb')
        error_free_yml_lesson_ = pickle.load(pkl_file)
        pkl_file.close()
    else:
        error_free_yml_lesson_ = defaultdict(int)
    return error_free_yml_lesson_


def save_error_free_yml(error_free_yml_lesson_, path_2_error_free_yml_lesson):
    # write python dict to a file
    output = open(path_2_error_free_yml_lesson, 'wb')
    pickle.dump(error_free_yml_lesson_, output)
    output.close()


# If a file starts with "indexed: false" skip it
def is_indexed(filename):
    with open(filename, 'r') as f:
        first_line = f.readline().replace(" ", "").lower().strip()
        return first_line != "indexed:false"


# Colors the words from bad_words red in a line
def color_incorrect(bad_words, line):
    line = re.sub(r'\b(' + '|'.join(bad_words) + r')\b', '{}', line)
    return line.format(*[colored(w, 'red') for w in bad_words])


def find_incorrect_titles(title_count, titles):
    missing = []
    extra = []
    for title in titles:
        if title_count[title.lower()] > 1:
            extra.append(colored(title.lower(), 'red'))
        elif title_count[title.lower()] < 1:
            missing.append(colored(title.lower(), 'red'))
    miss_str = 'missing: ' + ', '.join(missing) if missing else ''
    extra_str = 'extra: ' + ', '.join(extra) if extra else ''
    if miss_str:
        return miss_str + ' | ' + extra_str if extra_str else miss_str
    else:
        return extra_str


def find_incorrect_tags(filename):
    title_count = defaultdict(int)  # Counts number of titles, topics, etc
    incorrect_tags = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            for title, tag in tags_.items():
                if not line.startswith(title.lower()):
                    continue
                title_count[title.lower()] += 1
                n = True

                # Finds every non-legal tag as defined at the start of the file
                regex = r'\b(?!{0}|{1}\b)\w+'.format(title.lower(), tag)
                m = re.findall(regex, line)  # Places the words in a list
                if m:  # If we got any hits, this means the words are wrong
                    line = color_incorrect(m, line)  # color the words

                # This block finds titles without any legal words (empty).
                else:
                    if title != "level":
                        regex_legal = r'{0}: *\[( *({1}),? *)+\]'.format(
                            title.lower(), tag)
                    else:
                        regex_legal = r'{0}: *( *({1}),? *)+'.format(
                            title.lower(), tag)
                        n = re.search(regex_legal, line)
                    # If no legal words has been found, color the line red
                    if not n:
                        line = colored(line, 'red')

                if m or not n:  # Add line to list of incorrect tags
                    incorrect_tags.append(
                        (' ' * 4 if title != "level" else " ") + line)
                break

    # We find if any title, topic, subject does not appear exactly once
    return (incorrect_tags, title_count)


def get_incorrect_titles_and_tags(filename):
    incorrect_tags, title_count = find_incorrect_tags(filename)
    incorrect_titles = find_incorrect_titles(title_count, tags_.keys())
    return (incorrect_titles, incorrect_tags)


def print_incorrect_titles_and_tags(filename, incorrect_titles,
                                    incorrect_tags):
    print(colored(filename, 'yellow') + ": " + incorrect_titles)
    for incorrect_tag in incorrect_tags:
        print(incorrect_tag)


def get_yml_lesson(path):
    return glob.glob(path + '/**/lesson.yml', recursive=True)


def yml_linter(path=PATH_2_SRC):

    error_free_yml_ = load_error_free_yml(PATH_2_ERROR_FREE_LESSON_YML)
    for yml_lesson in get_yml_lesson(path):
        last_modified_lesson_yml = os.path.getmtime(yml_lesson)
        if last_modified_lesson_yml > error_free_yml_[yml_lesson]:
            if not is_indexed(yml_lesson):
                error_free_yml_[yml_lesson] = time.time()
                continue
            incorrect_titles, incorrect_tags = get_incorrect_titles_and_tags(
                yml_lesson)
            if incorrect_titles or incorrect_tags:
                print_incorrect_titles_and_tags(yml_lesson, incorrect_titles,
                                                incorrect_tags)
            else:
                error_free_yml_[yml_lesson] = time.time()
                save_error_free_yml(error_free_yml_,
                                    PATH_2_ERROR_FREE_LESSON_YML)


if __name__ == "__main__":

    # print("Please run LKK_linter instead")
    yml_linter()
