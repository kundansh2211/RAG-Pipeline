import re
import os
from doc_fetcher import get_raw_stex

import requests
import requests_cache
requests_cache.install_cache('requests_cache', expire_after=3600*24)

file_index = 0 

JUNK_BEGIN_END_TAGS = [
    'center',
    'column',
    'columns', 
    'document',
    'frame',
    'itemize',
    'nparagraph',
    'slideshow',
]
JUNK_TAGS = [
    'documentclass',
    'importmodule',
    'tociftopnotes',
    'libinput',
    'mhgraphics',
    'nvideonugget',
    'symdecl',
    # 'usemodule',
    # 'end'
] #+ [f'end{{{tag}}}' for tag in JUNK_BEGIN_END_TAGS]

SHOW_OPTIONS_TAGS = [
    'begin',
]

SHOW_ENVIRONMENT_TAGS = [
    'frametitle',
]

def clear_cache():
    requests_cache.clear()

def get_raw_stex_url(archive: str, filename: str):
    return f"https://gl.mathhub.info/{archive}/-/raw/main/source/{filename}"


def get_raw_stex(archive: str, filename: str):
    url = get_raw_stex_url(archive, filename)
    # print(f'getting url: {url}')
    return requests.get(url).text
def transform_line(line: str, debug=False):
    line = line.strip()
    if line.startswith('%'):
        return None
    for tag in JUNK_TAGS:
        if line.startswith('\\' + tag):
            return '%% removed: ' + line if debug else None
    return line
    for tag in SHOW_OPTIONS_TAGS:
        if line.startswith('\\' + tag):
            parsed = parse_latex_tag(line)
            options = parsed['Options']
            if options is None:
                options = ''
            if debug:
                return options + f' was ....{line}....'
            return options
    
    for tag in SHOW_ENVIRONMENT_TAGS:
        if line.startswith('\\' + tag):
            parsed = parse_latex_tag(line)
            if parsed is None:
                continue
            env = parsed['Environment']
            if env is None:
                env = ''
            if debug:
                return env + f' was ....{line}....'
            return env
    return line

def sanitize_filename(filename: str) -> str:
   return re.sub(r'[<>:"/\\|?*\s]', '_', filename)

def save_content_to_file(content: str, archive: str, filename: str, original_path: str):
    directory = "data"
    sanitized_archive = sanitize_filename(archive)
    sanitized_filename = sanitize_filename(filename)
    combined_filename = f"{sanitized_archive}_{sanitized_filename}"
    filepath = os.path.join(directory, combined_filename)

    # Ensure the 'data' directory exists
    os.makedirs(directory, exist_ok=True)

    with open(filepath, "w") as file:
        # Include archive and filename as metadata in the file
        file.write(f"Archive: {archive}\n")
        file.write(f"Filepath: {filename}\n\n")
        file.write(content)

def replace_inputref_line(fallback_archive: str, line: str) -> str:
    global file_index
    line = line.strip()
    
    match = re.match(r'\\inputref\*?(?:\[(.*?)\])?\{(.*?)\}', line)
    if match:
        archive, filename = match.groups()
        if archive is None:
            archive = fallback_archive
        file_index += 1
        content = get_recursive_stex(archive, filename + '.tex')
        save_content_to_file(content, archive, filename, f"{archive}/{filename}")
        return f'File: [{archive}]{{{filename}}}\n'
    
    match = re.match(r'\\libinput\{(.*?)\}', line)
    if match:
        filename = match.group(1)
        file_index += 1
        content = get_recursive_stex(fallback_archive, filename + '.tex')
        save_content_to_file(content, fallback_archive, filename, f"{fallback_archive}/{filename}")
        return f'File: [{fallback_archive}]{{{filename}}}\n'

    match = re.match(r'\\mhinput\{(.*?)\}', line)
    if match:
        filename = match.group(1)
        file_index += 1
        content = get_recursive_stex(fallback_archive, filename + '.tex')
        save_content_to_file(content, fallback_archive, filename, f"{fallback_archive}/{filename}")
        return f'File: [{fallback_archive}]{{{filename}}}\n'
    
    return line

def replace_inputref(archive: str, text: str) -> str:
    global file_index
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        processed_lines.append(replace_inputref_line(archive, line))
    return '\n'.join(processed_lines)


def cleanup_stex(text: str):
    return '\n'.join([transform_line(line) for line in text.split('\n')
                     if transform_line(line) is not None])



def get_recursive_stex(archive: str, filename: str) -> str:
    stex = cleanup_stex(get_raw_stex(archive, filename))
    return replace_inputref(archive, stex)

def create_raw_stex_files(output_filename="iwgs.txt", archive="courses/FAU/IWGS/course", filename="course/notes/notes-part1.tex"):
    try:
        res = get_recursive_stex(archive, filename)
        with open(output_filename, "w") as file:
            file.write(res)
        print(f"Successfully wrote processed content to {output_filename}.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # save_content_to_file()
    create_raw_stex_files()
 