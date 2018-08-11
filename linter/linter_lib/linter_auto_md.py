from linter_defaults import *
import textwrap

# REGEX_FIND_YML = re.compile(r"(?<=^---\s)[\s\S]+?(?=\r?\n---)", re.DOTALL)
REGEX_FIND_YML = re.compile(r"^---[\s\S]*?---", re.DOTALL)
REGEX_FIND_TITLES = re.compile(r" *(\w+) *: *(.*)")

REGEX_4_CODEBLOCKS = '```[\s\S]*?```|`[\s\S]*?`'

REGEX_PARAGRAPHS = re.compile(r' *```[\s\S]*?```|`[\s\S]*?`|(((?<=\n\n)|(?<=(\r\n){2}))( *)([a-zA-ZæøåÆØÅ][\s\S]*?)(?=(\r?\n){2}))', re.DOTALL)
REGEX_LISTS = re.compile(
    r' *```[\s\S]*?```|`[\s\S]*?`|(((?<=\n\n)|(?<=(\r\n){2}))( *)((- \[ \]|[1-2]?[1-9]\.|\-|\+|\*) \w[\s\S]*?)(?=\n\n|(\r\n){2}|$))'
    , re.DOTALL)

PROGRAMMING_LANGUAGES = [
    'apache', 'blocks', 'c', 'clojure', 'cpp', 'crystal',
    'csharp', 'css', 'csv', 'diff', 'elixir',
    'erb', 'elm', 'go', 'html', 'http', 'java',
    'javascript', 'js', 'json', 'julia', 'kotlin', 'less',
    'lua', 'markdown', 'matlab', 'pascal', 'processing',
    'PHP', 'Perl', 'python', 'rust', 'salt',
    'scala', 'scratch', 'shell', 'sh' , 'zsh' ,
    'text', 'bash', 'scss', 'sql', 'svg', 'swift', 'rb',
    'jruby', 'ruby', 'xml', 'yaml'
]

VOID_HTML = [
    "area", "base", "br", "col", "command", "embed", "hr", "img", "input",
    "keygen", "link", "menuitem", "meta", "param", "source", "track", "wbr"
]

VOID_HTML_STR = 'area|base|br|col|command|embed|hr|img|input|keygen|link|menuitem|meta|param|source|track|wbr'

REGEX_PARAGRAPH = '([\s\S]+?)((\r?\n{2})|$)'

'''
The first line matches -, * or -
Second matches 10-19 if not found, it matches 1-9
this line matches 1.1 , 1.1.1.1. , eg sublists with elements lower than 19
this line matches the checkbox type of lists - [ ]
'''
REGEX_LST = [
    '-|\*|\+', '(1[0-9]|[1-9])\.', '((1[0-9]|[1-9])\.)+(1[0-9]|[1-9])\.?',
    '- \[ \]'
]


def sort_yml_in_md(yaml, filepath):
    '''Sorts and corrects titles in YAML header. Example

    BEFORE                                   AFTER
    ---                                      ---
    languagr: nb                             title: Tegning med SVG
    ttitle: "Tegning med SVG"                author: Teodor Heggelund
    level: 3                                 language: nb
    aauthor: 'Teodor Heggelund'              ---
    ---

    Details:
    * Remvoves ' and " unless the line contains special characters
    * Fixes simple spelling mistakes, for more severe spelling mistakes a menu
      shows up
    * Sorts the keys in order see linter_defaults.py for the specific sorting
      order
    * Saves the titles in MOVE_TITLES in a temp file called FILE_INFO (this is
      put into the lesson.yml file)
    '''

    matches = re.finditer(REGEX_FIND_TITLES, yaml)
    new_title = [''] * len(YAML_TITLES)
    extra_title = []
    for match in matches:
        title = match.group(1)
        content = generate_content(match.group(2), title)
        title_and_content = '{}: {}'.format(title, content)
        if title in MOVE_TITLES:
            save_titles_to_be_moved_2_lesson_yml(title, title_and_content, filepath)
            continue

        if title in YAML_TITLES:
            new_title[YAML_TITLES_REVERSE_[title]] = title_and_content
            continue
        title_2 = levenshtein_lst(title, YAML_TITLES, title_and_content)
        if title_2:
            title_and_content_2 = '{}: {}'.format(title_2, content)
            new_title[YAML_TITLES_REVERSE_[title_2]] = title_and_content_2
        else:
            extra_title.append(title_and_content)

    return '---\n' + '\n'.join(filter(None, new_title)) + '\n---'


def generate_content(temp_content, title):
    content = re.sub(r' *(\"|\')(.*)(\"|\') *', r'\2', temp_content)
    if title == 'level':
        content = '{}'.format(min(max(int(content), MIN_LEVEL), MAX_LEVEL))
    elif title == 'language' and (content not in TAGS_['language']):
        error_line = '{}: {}'.format(title, content)
        content = levenshtein_lst(content, TAGS_['language'], error_line)
    # Changes all internal quotations to ' and ' while outer quotation is " and "
    content = re.sub(r'\"(.*)\"', r"'\1'", content)
    if re.search(r"[^\w\sæøåÆØÅ]", content):
        content = '"{}"'.format(content)
    return content


def save_titles_to_be_moved_2_lesson_yml(title, title_and_content, md_filepath):
    yml_lesson_path = re.sub(r'\w+\.md', LESSON_YML, md_filepath)
    if not Path(yml_lesson_path).is_file():
        return
    file_info = load_FILE_INFO()
    try:
        file_info['move'][yml_lesson_path]
    except KeyError:
        file_info['move'][yml_lesson_path] = dict()
    file_info['move'][yml_lesson_path][title] = title_and_content
    save_FILE_INFO(file_info)


def check_if_table(i, md_data_lst):
    '''Tables looks something like:

    word | word    OR  | word | word | word |
    ---  | ---         | ---  |:----:|---:  |

    Thus, the smallest line that could possibly contain a table (with two
    columns) is 7 characters.

    Then, if we are not at the last line of the file it checks if the following
    line is on the form

    ---  | --- | ---

    e.g. Three or more - followed by | and at most one :
    '''

    line = md_data_lst[i].strip()
    if not line or len(line) < 7 or not '|' in line:
        return False
    is_last_line = i + 1 == len(md_data_lst)
    if is_last_line:
        return
    next_line = md_data_lst[i + 1].strip()
    # Finds ---| many times followed by an --- followed by 0 or 1 |
    if re.search('^\|?( *:?-{3,}:? *\|){1,}( *:?-{3,}:? *\|?)$', next_line):
        return True


def count_columns_in_table(line):
    '''Every table looks like
    | title | title |
    or
      title | title
    This removes the first and last | and counts the remaining number of |.
    The number of colums is then 1 more than this number.
    '''
    return line[1:-1].strip().count('|') + 1


def format_table(table, columns=0):

    # Formats the table into a matrix of size rows, columns
    matrix = [row.split('|') for row in table.split('\n')]
    rows, columns = len(matrix), len(matrix[0])

    indent = len(table) - len(table.lstrip())

    # Finds the longest string in each column, also strips whitespace
    lengths = [0] * columns
    for row in range(rows):
        for column in range(columns):
            element = matrix[row][column].strip()
            lengths[column] = max(len(element), lengths[column])
            matrix[row][column] = element

    empty_columns = [i for i, length in enumerate(lengths) if length == 0]
    if empty_columns:
        for i, row in enumerate(matrix):
            matrix[i] = [column for j, column in enumerate(row) if j not in empty_columns]
        lengths = [length for k, length in enumerate(lengths) if k not in empty_columns]
        columns -= len(empty_columns)

    # This creates the formating string for the new table
    formating = [''] * columns
    for i, length in enumerate(lengths):
        length = str(length)
        line = matrix[1][i].replace(" ", "")
        if line.startswith(':-'):
            if line.endswith('-:'):
                formating[i] = '{:^' + length + '}'
                matrix[1][i] = ':{}:'.format('-' * (int(length) - 2))
            else:
                formating[i] = '{:' + length + '}'
                matrix[1][i] = ':{}'.format('-' * (int(length) - 1))
        elif line.endswith('-:'):
            formating[i] = '{:>' + length + '}'
            matrix[1][i] = '{}:'.format('-' * (int(length) - 1))
        else:
            formating[i] = '{:' + length + '}'
            matrix[1][i] = '{}'.format('-' * (int(length)))

    line_format = '{}| {} |'.format(' '*indent, ' | '.join(formating))
    new_table_lines = [line_format.format(*row) for row in matrix]
    return '\n'.join(new_table_lines)


def fix_leading_trailing_whitespace(line):
    ''' Removes all trailing whitespace in line, it also
    makes sure that the leading whitespace is a multiple
    of TAB INDENT'''

    leading_indent_len = len(line) - len(line.lstrip())
    if leading_indent_len:
        leading_indent_len -= leading_indent_len % TAB_INDENT
    return ' ' * leading_indent_len + line.strip()


def split_md(md_data_lst):

    def append_if_new(md_data_, line, current, nxt=''):
        if current != md_data_['last']:
            md_data_['last'] = current
            md_data_['lst'].append(line)
            md_data_[current].append(md_data_['counter'])
            md_data_['counter'] += 1
        else:
            md_data_['lst'][-1] += '\n' + line
        return md_data_ if not nxt else append_if_new(md_data_, '', nxt)

    md_data_ = dict(
        lst=[],
        textblocks=[],
        codeblocks=[],
        html=[],
        yaml=[],
        tables=[],
        counter=0,
        last='')

    html_key = ''
    backticks_start = ''
    yaml_count = 0
    table_columns = 0

    for i, line in enumerate(md_data_lst):

        if line:
            line = fix_leading_trailing_whitespace(line)

        # This codeblocks extracts the first yaml header
        if yaml_count == 0:
            if len(md_data_['textblocks']) > 1 or md_data_['codeblocks'] or md_data_['html'] or md_data_['tables']:
                # If anything is found before the YAML, ignore the yaml
                yaml_count == 2
            elif line.strip().startswith('--'):
                yaml_count = 1
                # md_data_ = append_if_new(md_data_, '---', 'yaml')
                continue
        elif yaml_count == 1:
            if line.strip().startswith('--'):
                yaml_count = 2
                # md_data_ = append_if_new(md_data_, '---', 'yaml')
                md_data_ = append_if_new(md_data_, '', 'textblocks')
            else:
                if line.strip():
                    md_data_ = append_if_new(md_data_, line, 'yaml')
            continue

        if md_data_['last'] == 'tables':
            # If the number of columns in this line, is the same
            # as in the current table, append to table. Otherwise
            # add to paragraph.
            columns_in_current_line = count_columns_in_table(line)
            if columns_in_current_line >= 2:
                is_table = abs(table_columns - columns_in_current_line) < 3
                if is_table:
                    md_data_ = append_if_new(md_data_, line, 'tables')
                    continue
            md_data_ = append_if_new(md_data_, line, 'textblocks')
            continue

        # If we are not in a html block, check if we are in a codeblock
        if not (md_data_['last'] == 'html'):

            is_codeblock = md_data_['last'] == 'codeblocks'
            codeblock_start_end = re.search('^ *((`{3,}([^`\n]+)`{3,})|([^`\n\r]*(`{3,})(.*)))', line)
            # The regex above checks both for starting and ending backticks
            if codeblock_start_end or is_codeblock:
                md_data_ = append_if_new(md_data_, line, 'codeblocks')
                if codeblock_start_end:
                    current_backticks = codeblock_start_end.group(5)
                    is_oneliner = True if codeblock_start_end.group(2) else False
                    if is_oneliner or (is_codeblock and current_backticks == backticks_start):
                        backticks_start = ''
                        md_data_ = append_if_new(md_data_, '', 'textblocks')
                    elif not backticks_start:
                        backticks_start = current_backticks
                continue


        # If we are in a html block, use regex to check for end of block, else append
        if md_data_['last'] == 'html':
            # Searches for expressions of the form: </hide>
            match = re.search(r'( *< */ *({}).*?> *$)'.format(html_key), line)
            md_data_ = append_if_new(md_data_, line, 'html', 'textblocks' if match else '')
            continue

        # This regex searches for html
        match = re.search(
            r'^ *(< *(\w+).*?>.*?< *\/\2.*?>|(< *(\w+).*?>)) *(\r?\n|$)|^ *(!?\[.*\]\(.*\)) *$',
            line)
        if match:
            if match.group(4):
                # Finds codeblocks with no end. Example: <style>
                html_key = match.group(4)
                md_data_ = append_if_new(md_data_, line, 'html')
                if html_key in VOID_HTML:
                    md_data_ = append_if_new(md_data_, '', 'textblocks')
            elif match.group(1) or match.group(6):
                # group 1: Matches html, that starts and ends on the same line
                # Example: <div id="boks"></div>
                # group 6: matches images and links of the form ![]() or []()
                md_data_ = append_if_new(md_data_, line, 'html', 'textblocks')
            continue

        # If we are not in a html, codeblock or yaml, check if table
        if check_if_table(i, md_data_lst):
            md_data_ = append_if_new(md_data_, line, 'tables')
            table_columns = count_columns_in_table(line)
            continue

        # Finally, if we are not in a table, html, codeblock or yaml add to text
        md_data_ = append_if_new(md_data_, line, 'textblocks')

    return md_data_


def format_paragraph(paragraph, paragraph_type):
    '''Formats paragraphs into lines of max CODE_WIDTH (usually 80) length.
    The first line remove all tabs, spaces, newlines etc from the paragraph.
    Then the textwrap commands fills in the lines according to the rules set.
    '''

    line = paragraph.split('\n')[0]
    initial_indent = subsequent_indent = len(line) - len(line.lstrip())
    if initial_indent and initial_indent % 4 == 0:
        # Multiples of four are reserved for code and should not be formated
        return paragraph

    if paragraph_type == 'list':
        subsequent_indent += TAB_INDENT

    return textwrap.fill(
        " ".join(paragraph.split()),
        width=CODE_WIDTH,
        initial_indent=' ' * initial_indent,
        subsequent_indent=' ' * subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False)


def get_header_class(header):
    match = re.search(r'((\r?\n|^)#+ .*){\.(\w+)}', header)
    if not match:
        return (None, None)
    return (match.group(1), match.group(3).strip())


def fix_class_name_in_header(header):
    ''' Searches through header with classes, if the class
    is not in CLASSES_LIST; it corrects the mistake. Based on
    the severity of the mistake either it is fixed automatically
    or a simple menu shows up, showing the user for the closest matches
    Example:
              first_part_of_header   class_name = "intror"
                /              \       /    \
                 # introduction      {.intror}
                \                             /
                           header
    '''

    first_part_of_header, class_name = get_header_class(header)
    if class_name and class_name not in CLASSES_LIST:
        new_class_name = levenshtein_lst(class_name, CLASSES_LIST,
                                         header.strip())
        header = '{} {{.{}}}'.format(first_part_of_header.rstrip(),
                                         new_class_name)
    return header


def fix_headers(header):
    header_2 = re.search(r'^([^=\r\n]*)=+$', header)
    if header_2:
        return fix_headers('# ' + header_2.group(1).strip())
    header_3 = re.search(r'^([^=\r\n]*)-+$', header)
    if header_3:
        return fix_headers('## ' + header_3.group(1).strip())

    # Makes sure every title has exactly one space after the last #
    header = re.sub(r'^ *(#+) *(.)', r'\1 \2', header)

    # Removes all punctuation from titles
    header = re.sub(r'(#+ .*)(\.|\,|\;) *$', r'\1', header)

    # This fixes mistakes in the class, eg {{.intro} or .intro
    header = re.sub(r'^(#.*[^ {]) *(?:{*)(\.\w+)(?:}*)$', r'\1 {\2}',
                    header)

    # Makes sure the class name is spelled correctly. Example: {.intro}
    header = fix_class_name_in_header(header)

    # Makes sure every main header has an extra line above
    if header.startswith('# '):
        header = '\n{}'.format(header)
    return header


def fix_list(line):
    # This makes sure checklists look like - [ ] not -[] or -[ ] etc
    line = re.sub(r'^( *-) *\[ *\] *(.)', r'\1 [ ] \2', line)

    # This makes sure -, +, * look like '* ' not '*' or '*   ' etc
    line = re.sub(r'^( *(\*|\-|\+)) *(.)', r'\1 \3', line)

    # This makes sure '1.', '1.2.3.' look like '1. text' and not '1.text'
    line = re.sub(
        r'^((?:(?:1[0-9]|[1-9])\.)+(?:1[0-9]|[1-9])?)( *)(?![0-9\.])', r'\1 ',
        line)

    return line


def is_header_or_list(line, symbol, text, can_be_quickfixed=True):
    print('''
    {} ERROR: The following line starts with a \'{}\'\n\n  {}
'''.format(text.upper(), symbol, line))
    ask = input(
        'Every {typ} needs to start with \'{sym} \' ({sym} then space) is the line above a {typ}? [y/n]: '.
        format(typ=text, sym=symbol))
    if can_be_quickfixed:
        print(
            'You can avoid this error by writing \'\{sym}\' whenever a \'{sym}\' starts a line\n'.
            format(sym=symbol))
    return ask.lower() in ['yes', 'ok', 'y', 'j', 'ja']


def is_header(line):
    '''First it uses some simple regex to determine whether the line starts with a
    #. If it does not it is obviously not an header. Then it checks if this #
    is followed by a space. If it is, then the line is an header, otherwise it
    asks the user to confirm whether the line is an header.
    '''

    header = re.search(r'^(#+)( *)(.)', line)
    if not header:
        header_2 = re.search(r'^([^=\r\n]+)=+$', line)
        header_3 = re.search(r'^([^=\r\n]+)-+$', line)
        if header_2 or header_3:
            return True
        return False
    if header.group(2):
        return True
    if re.search(r'^(#+)$', line):
        return True
    if header.group(3).isdigit():
        return  False
    return is_header_or_list(line, '#', 'header')


def is_list_symbol(line, i, lines, number_of_lines):
    lst = re.search(r'^(\*|\-|\+)( *).', line)
    if not lst:
        return False
    symbol = lst.group(1)
    spacing = lst.group(2)
    if symbol == '*' and re.search(r'^\*.*\*', line):
            return False
    elif symbol == '-':
        if line[1].isdigit():
            return False
        if re.search(r'^ *---', line) or re.search(r'^ *-->', line):
            return False
    if spacing:
        return True
    else:
        if symbol == '*':
            for i in range(i, min(number_of_lines, i+10)):
                next_line = lines[i].strip()
                if next_line.startswith('* '):
                    break
                elif next_line.endswith('*'):
                    return False
    return is_header_or_list(line, symbol, 'element')


def is_list_number(line):
    number_lst = re.search(
        r'^((?:(?:1[0-9]|[1-9])\.)+(?:1[0-9]|[1-9])?)( *)(?![0-9\.])', line)
    if not number_lst:
        return False
    enumeration = number_lst.group(1)
    spacing = number_lst.group(2)
    if spacing:
        return True
    if any(line.startswith(enumeration + symbol) for symbol in [')',']','}']):
        return False
    return is_header_or_list(line, enumeration, 'element', False)


def update_text(text_, next_category):
    if text_['paragraph']:
        line = ' '.join(text_['paragraph'])
        formated_paragraph = format_paragraph(line, text_['category'])
        text_['text_new'].append(formated_paragraph)
        text_['paragraph'] = []
        text_['category'] = next_category
    return text_


def fix_md_text(text):
    '''This function takes in a long textstring
    and searches it line by line for headers (# some title here)
    or lists (- []). If it is none of the above it is classified as generic text.
    Lists or text are stored in a variable called paragraph. Then when a blank line
    is found, the current paragraph is then formated to 80 characters width.
    '''

    text_ = dict(
        text_new = [],
        category = '',
        paragraph = [],
        )

    lines =  text.split('\n')
    number_of_lines = len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            text_ = update_text(text_, '')
            continue

        lline = line.lstrip()
        if is_header(lline):
            text_ = update_text(text_, 'header')
            text_['text_new'].append(fix_headers(line))
            text_ = update_text(text_, '')
        elif is_list_symbol(lline, i, lines, number_of_lines) or is_list_number(lline):
            text_ = update_text(text_, 'list')
            text_['paragraph'].append(fix_list(line))
            text_['category'] = 'list'
        else:
            if not text_['category']:
                text_['category'] = 'text'
            text_['paragraph'].append(line)

    text_ = update_text(text_, '')
    return '\n\n'.join(text_['text_new'])


def fix_codeblocks(codeblock, has_looped = False):
    codelines = codeblock.split('\n')
    is_oneliner = len(codelines) == 1

    first_line, last_line = codelines[0], codelines[-1]

    # This makes sure that the codeblocks has 3 backticks or more
    first_line = re.sub(r'^( *)`` *(\w+|$)', r'\1```\2', first_line)
    last_line = re.sub(r'^( *)`` *(\w+|$)', r'\1```\2', last_line)

    # This makes sure the spelling of programming languages is right
    # This block might be removed if many new languages emerges
    # The supported languages can be changed in the PROGRAMMING_LANGUAGE
    # variable. Located in 'linter_defaults'
    has_language = re.search('( *)(`{3,}) *(\w*)(.*)', first_line)
    indent = has_language.group(1)
    backticks = has_language.group(2)
    if has_language.group(3).strip():
        language = has_language.group(3)
        remaining = has_language.group(4)
        if language not in PROGRAMMING_LANGUAGES:
            language = levenshtein_lst(language,
                                       PROGRAMMING_LANGUAGES,
                                       first_line)
        first_line = '{}{}{}'.format(indent, backticks, language.strip())
        if remaining:
            first_line += '\n' + remaining.strip()

    ''' The following if sentence does the following transformation:

    Before:        |     After:
                   |
    code } ```text |     code }
                   |     ```
                   |
                   |     text
    '''
    has_trailing_text = re.search('([^`\r\n]*)(`{3,})(.*)', last_line)
    if has_trailing_text:
        code_text = has_trailing_text.group(1)
        trailing = has_trailing_text.group(3).strip()
        last_line = code_text + '\n' + indent + backticks if code_text.strip() else indent + backticks
        last_line += '\n\n' + trailing if trailing else ''

    codelines[0] = first_line
    codelines[-1] = last_line

    codeblock = '\n'.join(codelines)

    if is_oneliner and not has_looped:
        return fix_codeblocks(codeblock, True)
    return codeblock


def fix_leading_trailing_newlines(line, before=0, after=0):
    if not line.strip():
        return '\n' * (before + after)
    for i in range(len(line)):
        if line[i] != '\n':
            break
    return '{}{}{}'.format(line.rstrip()[i::], '\n' * before, '\n' * after)


def add_newline_end_of_file(md_data):
    if md_data:
        return fix_leading_trailing_newlines(md_data, 0, 1)
    return md_data


def update_md(md_data, filepath):
    # Remove trailing whitespace if it exists
    md_data = [line.rstrip() for line in md_data]

    md_data_ = split_md(md_data)

    for i in md_data_['html']:
        html = md_data_['lst'][i]

    for i in md_data_['tables']:
        table = md_data_['lst'][i]
        md_data_['lst'][i] = format_table(table)

    for i in md_data_['codeblocks']:
        codeblock = md_data_['lst'][i]
        # print(codeblock)
        # print()
        md_data_['lst'][i] = fix_codeblocks(codeblock)

    for i in md_data_['textblocks']:
        text = md_data_['lst'][i]
        if not text.strip():
            md_data_['lst'][i] = ''
        else:
            md_data_['lst'][i] = fix_md_text(text)

    # print(md_data_['lst'])

    if md_data_['yaml']:
        number = md_data_['yaml'][0]
        yaml = md_data_['lst'][number]
        md_data_['lst'][number] = sort_yml_in_md(yaml, filepath)

    md_data = '\n\n'.join(filter(None, md_data_['lst']))
    return add_newline_end_of_file(md_data)


def auto_lint_md(filename):
    temp_file = create_temp_path(filename)

    with open(filename, "r") as md:
        data_md_new = update_md(md, filename)
        # By creating the data_md_new first, it avoids creating the
        # temp file if errors is found in the function 'update_md'.
        with open(temp_file, "w") as md_new:
            for line in data_md_new:
                md_new.write(line)
            if data_md_new:
                if not line.endswith('\n'):
                    md_new.write('\n')

    if filecmp.cmp(filename, temp_file):
        # File has not changed, removing temp
        os.remove(temp_file)
    else:
        # File has changed, renaming temp to perm
        os.rename(temp_file, filename)


def main(files_md):
    '''This file autoformats md files, which can be broken into four parts:

    1. Sort and fix yaml titles.
    See sort_yml_in_md() for a detailed explenation. This fixes the order of
    the titles in the YAML header, removes titles that should be moved, as well
    as adding quotation marks " " only where deemed neccecary.

    2. Save titles to be moved.
    See save_titles_to_be_moved_2_lesson_yml(). The purpose is to save the
    lines to be moved in a temp file. This temp file is then accessed by
    auto_lint_md.py, which puts the lines into lesson.yml file and then deletes
    the file.

    3. Fixing spelling mistakes.
    This is done several places in the code. In short it corrects very minor
    mistakes automatically, while more severe mistakes triggers a menu and user
    interaction. For a detailed explanation of how mistakes are fixed see the
    'levenshtein_distance()' functions in the 'linter_defaults.py' module.

    4. Style the files accoding to the style guide.
    This fixes everything from trailing whitespace, to incorrect spacing in
    headers see 'update_md()' for the full list of changes.
    '''

    for file_md in files_md:
        print(file_md)
        auto_lint_md(file_md)


if __name__ == "__main__":

    # print("Please run LKK_linter.py in the directory above instead")
    files_md = [sys.argv[1]]
    main(files_md)
