import re
import filecmp
import sys

from pathlib import Path

REGEX_FIND_YML = re.compile(r"(?<=^---\s)[\s\S]+?(?=\n---)", re.DOTALL)
REGEX_FIND_REM = re.compile(
    r"(\n(?!((title|author|translator|language|external|level)))).*")
REGEX_WHITESPACE = re.compile(r'[ \t]+(\n|\Z)|(?<=\n)[ \t]+(?=(\n|\Z|.))')
LESSON_TEMPLATE = """
tags:
  topic: []
  subject: []
  grade: [] """


KEYS = ['topic', 'subject', 'grade']
MIN_LEVEL = 1
MAX_LEVEL = 4 # Change this to change allowed levels.

MOVE_LEVEL_2_LESSON_YML = False

# Uncommenting the line below will remove level from .md file and move it to lesson.yml
# MOVE_LEVEL_2_LESSON_YML = True


LEVEL = '[{}-{}]'.format(MIN_LEVEL, MAX_LEVEL)

def lesson_yml(md_filepath, new_level=float('inf')):
    lesson_yml_path = Path(re.sub(r'\w+\.md', 'lesson.yml', md_filepath))
    if lesson_yml_path.is_file():
        with open(PATH + 'lesson.yml', "r") as f:
            yml_data = f.read()
        with open(PATH + 'lesson.yml', "w") as f:
            for line in update_lesson_yml(yml_data, new_level):
                f.write(line)
    else:
        new_lesson_yml(new_level)


def new_lesson_yml(new_level=float('inf')):
    with open("./lesson.yml", "w") as f:
        f.write(
            "level: {}".format(new_level if new_level != float('Inf') else ''))
        for line in LESSON_TEMPLATE:
            f.write(line)


def update_lesson_yml(yml_data, new_level=float('Inf')):
    yml_data = re.sub('[\t ]', r'', yml_data)  # Remove all tabs/spaces
    yml_data = re.sub(r',(?! )', r', ', yml_data)  #Adds space after comma

    if new_level == float('Inf'):
        lvl = re.search(r' *level *: *({})'.format(LEVEL), yml_data)
        if lvl:
            yml_data_new = 'level: ' + lvl.group(1)
        else:
            yml_data_new = 'level: '
    else:
        yml_data_new = 'level: {}'.format(max(min(new_level, 4), 1))
    yml_data_new += '\ntags:\n'

    # Fixes the order of the tags
    for key_type in KEYS:
        match = re.search(r"({}:)(\[.*\]\n)".format(key_type), yml_data)
        if match:
            yml_data_new += '  {} {}'.format(match.group(1), match.group(2))
        else:
            yml_data_new += '  {}: []\n'.format(key_type)

    return yml_data_new[:-1]


def sort_yml_in_md(md_data, remove_level):
    match = re.findall(REGEX_FIND_YML, md_data)
    if not match:
        return

    yaml_header = match[0]
    empty_yaml_titles = []
    wrong_yaml_titles = []

    # Exctract header
    yaml_header = re.sub(r' *(\"|\')(.*)(\"|\') *', r' \2', yaml_header)

    title = re.search(r"(title:) *(.*)", yaml_header)
    level = re.search(r"(level:) *([1-4])", yaml_header)
    author = re.search(r"(author:) *(.*)", yaml_header)
    external = re.search(r"(external:) *(.*)", yaml_header)
    licence = re.search(r"(licence:) *(.*)", yaml_header)
    lang = re.search(r"(language:) *(\w*) *", yaml_header)
    translator = re.search(r"(translator:) *(.*) *", yaml_header)
    rem = re.finditer(REGEX_FIND_REM, yaml_header)

    if not author and external:
        author = external

    sorted_yaml = ''
    for result in [title, level, author, translator, *rem, licence, lang]:
        if result:
            if result.group(1) == 'level:' and remove_level:
                continue
            sorted_yaml += result.group(0).strip() + "\n"
    if level and remove_level:
        if level.group(2):
            return (sorted_yaml[:-1], level.group(2))
    return (sorted_yaml[:-1], float('Inf'))


def main():
    path_2_md_file = sys.argv[1]
    with open(path_2_md_file, "r") as f:
        md_data = f.read()
    # Sorts the yml header, and removes "".
    sorted_yml, level = sort_yml_in_md(md_data, MOVE_LEVEL_2_LESSON_YML)
    md_data = re.sub(REGEX_FIND_YML, sorted_yml, md_data)
    with open(path_2_md_file, "w") as f:
        for line in md_data:
            f.write(line)

    # Sorts and formats the the lesson.yml file
    # If MOVE_LEVEL_2_LESSON_YML is true, it will
    # use the level value from the yml header in lesson.yml
    if not MOVE_LEVEL_2_LESSON_YML:
        lesson_yml(path_2_md_file)
    else:
        lesson_yml(path_2_md_file, int(level))


if __name__ == "__main__":

    main()
