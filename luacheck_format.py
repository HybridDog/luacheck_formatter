# /usr/bin/env python3

import subprocess


def get_luacheck_errors(code):
    """Execute luacheck to find errors for the specified code"""
    errors = subprocess.run(
        ["luacheck", ".", f"--only={code}", "--formatter=plain"], stdout=subprocess.PIPE
    ).stdout
    result = []
    for line in errors.split(b"\n"):
        if line == b"":
            continue
        splitpos = line.find(b": ")
        location = line[:splitpos].split(b":")
        message = line[splitpos + 2 :]
        if len(location) != 3:
            print(f'Could not determine the location for "{line}"')
            continue
        file_path = location[0]
        problem_row = int(location[1]) - 1
        problem_col = int(location[2]) - 1
        result.append((file_path, problem_row, problem_col, message))
    return result


def fix_unused_arguments():
    """Remove unused arguments at the end and replace them with _ in the middle"""
    unused_args = get_luacheck_errors("212")
    current_file_path = None
    current_lines = None
    # The unused arguments are printed in order of their occurence
    for file_path, problem_row, problem_col, message in reversed(unused_args):
        if b"unused argument" not in message:
            print(f"Could not decode unused parameter name: {message}")
            continue
        param_name = message[len(b"unused argument '") : -1]
        # ~ print(param_name, file_path, problem_row, problem_col)
        if current_file_path != file_path:
            if current_file_path is not None:
                with open(current_file_path, "wb") as outfile:
                    outfile.write(b"\n".join(current_lines))
            current_file_path = file_path
            with open(current_file_path, "rb") as infile:
                current_lines = infile.read().split(b"\n")
        problem_line = current_lines[problem_row].decode("utf-8")
        before_param = problem_line[:problem_col]
        after_param = problem_line[problem_col + len(param_name) :]
        # ~ print(f"problem_line: {problem_line}")
        # ~ print(f"before_param: '{before_param}', after_param: '{after_param}'")
        is_last_param = after_param.lstrip()[0] == ")"
        if is_last_param:
            # Remove the parameter
            before_param = before_param.rstrip()
            if before_param[-1] == ",":
                before_param = before_param[:-1]
            new_line = before_param + after_param.lstrip()
        else:
            # Replace the parameter with _
            new_line = before_param + "_" + after_param.lstrip()
        current_lines[problem_row] = new_line.encode()
    if current_file_path is not None:
        with open(current_file_path, "wb") as outfile:
            outfile.write(b"\n".join(current_lines))


def fix_tab_after_space():
    """Replace spaces with tabs in indentations if both are used at once"""
    spacing_errors = get_luacheck_errors("621")
    current_file_path = None
    current_lines = None
    for file_path, problem_row, problem_col, message in spacing_errors:
        if current_file_path != file_path:
            if current_file_path is not None:
                with open(current_file_path, "wb") as outfile:
                    outfile.write(b"\n".join(current_lines))
            current_file_path = file_path
            with open(current_file_path, "rb") as infile:
                current_lines = infile.read().split(b"\n")
        problem_line = current_lines[problem_row].decode("utf-8")
        after_indent = problem_line.lstrip()
        indent = problem_line[: len(problem_line) - len(after_indent)]
        # Use tab for indentation
        tab_length = 4
        indent_length = sum(1 if c == " " else 4 for c in indent)
        indent = "\t" * (indent_length // 4) + " " * (indent_length % 4)
        new_line = indent + after_indent
        current_lines[problem_row] = new_line.encode()
        print(problem_line)
        print(new_line)
        # ~ print(f'"{indent}" "{after_indent}"')

    if current_file_path is not None:
        with open(current_file_path, "wb") as outfile:
            outfile.write(b"\n".join(current_lines))


def main():
    fix_unused_arguments()
    fix_tab_after_space()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
