import ast

def string_to_dict(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return None  # Or handle the error as appropriate