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

CLASSES = "intro|activity|check|flag|challenge|tip|save|protip|try|sjekkliste"

CLASSES_LIST = CLASSES.split("|")
LANGUAGE_LIST = LANGUAGE.split("|")

REGEX_ALT_OUTSIDE_CODE = r"```.*?```|`.*?`|(<img(?!.*?alt=(['\"]).*?\2)[^>]*)(>)|(!\[\]\()"
REGEX_LONG_LINES_OUTSIDE_CODE = r"```(.|\n)*?```|`.*?`|(.{100,})"
REGEX_FIND_YML = re.compile(r"^---[\s\S]+?---", re.DOTALL)

PATH_2_ERROR_FREE_MD = "./error_free_md.pkl"
PATH_2_SRC = '../src'


def load_error_free_md(path_2_error_free_lesson_yml):
    error_free_yml = Path(path_2_error_free_lesson_yml)
    if error_free_yml.is_file():
        # file exists
        # read python dict back from the file
        pkl_file = open(path_2_error_free_lesson_yml, 'rb')
        error_free_md_ = pickle.load(pkl_file)
        pkl_file.close()
    else:
        error_free_md_ = defaultdict(int)
    return error_free_md_


def save_error_free_md(error_free_md_, path_2_error_free_md):
    # write python dict to a file
    output = open(path_2_error_free_md, 'wb')
    pickle.dump(error_free_md_, output)
    output.close()


def error_msg(string):
    return '{}'.format(colored(string, 'red'))


def find_missing_alts(data):
    missing_alts = []
    matches = re.finditer(REGEX_ALT_OUTSIDE_CODE, data, re.DOTALL)
    for match in matches:
        if match.group(1):
            missing_alts.append((match.start(1), error_msg('ALT'),
                                 match.group(1)))
    return missing_alts


def find_long_lines(data):
    long_lines = []
    matches = re.finditer(REGEX_LONG_LINES_OUTSIDE_CODE, data)
    for match in matches:
        if match.group(2):
            banned_words = re.search(
                r'!\[|http|img|png|jpg|svg|script|\[.*\]\(', match.group(2))
            if not banned_words:
                long_lines.append((match.start(2), error_msg('80>'),
                                   match.group(2)))
    return long_lines


def find_missing_or_wrong_yaml_title(title_match, title):
    missing_title = ''
    wrong_title = ''
    if not title_match:
        missing_title = (5, error_msg('missing'), title)
    else:
        if not title_match.group(2):
            wrong_title = (title_match.start(0), error_msg('empty'),
                           title_match.group(1))
        elif "language" == title:
            iso = title_match.group(2)
            if iso not in LANGUAGE_LIST:
                wrong_title = (title_match.start(0), error_msg('iso'),
                               '{} {}'.format(
                                   title_match.group(1), colored(iso, 'red')))
    return missing_title, wrong_title


def find_incorrect_yaml(data, path):
    match = re.findall(REGEX_FIND_YML, data)
    if not match:
        if is_oppgaver(path):
            return [(1, error_msg('YAML'), 'Missing YAML header')]
        else:
            return []

    yaml_header = match[0]
    empty_yaml_titles = []
    wrong_yaml_titles = []

    title = re.search(r"(title:) *(.*)", yaml_header)
    author = re.search(r"(author:) *(.*)", yaml_header)
    external = re.search(r"(external:) *(.*)", yaml_header)
    lang = re.search(r"(language:) *(\w*) *", yaml_header)

    empty_title, wrong_title = find_missing_or_wrong_yaml_title(title, "title")
    empty_yaml_titles.append(empty_title) if empty_title else ''
    wrong_yaml_titles.append(wrong_title) if wrong_title else ''

    empty_title, wrong_title = find_missing_or_wrong_yaml_title(
        lang, "language")
    empty_yaml_titles.append(empty_title) if empty_title else ''
    wrong_yaml_titles.append(wrong_title) if wrong_title else ''

    # Oppgaver needs either author or external
    if is_oppgaver(path):
        empty_author, wrong_author = find_missing_or_wrong_yaml_title(
            author, 'author')
        empty_external, wrong_external = find_missing_or_wrong_yaml_title(
            external, 'external')
        if (empty_author and empty_external):
            empty_yaml_titles.append('author/external')
        elif not empty_author:
            wrong_yaml_titles.append(wrong_author) if wrong_author else ''
        elif not empty_external:
            wrong_yaml_titles.append(wrong_external) if wrong_external else ''

    empty_yaml_titles.extend(wrong_yaml_titles)
    return empty_yaml_titles


# Colors the words from bad_words red in the line
def color_incorrect(bad_words, line):
    line = re.sub(r'\b(' + '|'.join(bad_words) + r')\b', '{}', line)
    return line.format(*[colored(w, 'red') for w in bad_words])


def find_incorrect_class_in_headers(data):
    matches = re.finditer(r'#+ .*{?\.(\w+)}?\s\n', data)
    incorrect_classes = []
    for m in matches:
        if m.group(1) not in CLASSES_LIST:
            line_w_fixed_brackets = m.group(0).replace('{', '{{').replace(
                '}', '}}').strip()
            incorrect_classes.append((m.start(0), error_msg('class'),
                                      color_incorrect([m.group(1)],
                                                      line_w_fixed_brackets)))
    return incorrect_classes


def find_correct_line_numbers(lines_with_errors, data):
    # Files are read as one long line, this converts
    # the character where the error was found to a line number
    char_list = [i[0] for i in lines_with_errors]
    line_numbers = []
    prev = 0
    line = 1
    for char in char_list:
        line += data[prev:char].count('\n')
        line_numbers.append(line)
        prev = char
    return line_numbers


def find_lines_with_errors(data, path):
    # Returns a sorted list of errors, where each element is a tuple:
    #   (char, error_msg, line)
    # char is the first character of the error, line is the first
    # 80 characters in the line with the error.
    return sorted(
        find_missing_alts(data) + find_long_lines(data) +
        find_incorrect_class_in_headers(data) +
        find_incorrect_yaml(data, path))


def is_oppgaver(filepath):
    # Every oppgave has a lesson.yml in the same folder
    yml_path = Path(re.sub(r'\w+\.md', 'lesson.yml', filepath))
    return yml_path.is_file()


def print_lines_with_errors(filename, md_data, lines_with_errors):
    # Read file into one long string called data

    # If oppgaver then the file needs an author / external.
    line_numbers = find_correct_line_numbers(lines_with_errors, md_data)
    print('\n{}'.format(colored(filename, 'yellow')))
    for i, line in enumerate(lines_with_errors):
        print('{:>15}:{:<18} {}'.format(
            colored(str(line_numbers[i]), 'yellow'), line[1],
            (line[2][:80] + '...') if len(line[2]) > 80 else line[2]))


def get_md_files(path):
    return glob.glob(path + '/**/*.md', recursive=True)


def md_linter(path=PATH_2_SRC):

    error_free_md_ = load_error_free_md(PATH_2_ERROR_FREE_MD)
    for md_file in get_md_files(path):
        last_modified_md = os.path.getmtime(md_file)
        if last_modified_md <= error_free_md_[md_file]:
            continue
        with open(md_file, "r") as f:
            md_data = f.read()

        lines_with_errors = find_lines_with_errors(md_data, md_file)
        if not lines_with_errors:
            error_free_md_[md_file] = time.time()
            save_error_free_md(error_free_md_,
                               PATH_2_ERROR_FREE_MD)
            continue
        print_lines_with_errors(md_file, md_data, lines_with_errors)


if __name__ == "__main__":

    # print("Please run LKK_linter instead")
    md_linter()
