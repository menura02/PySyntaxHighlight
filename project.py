import tkinter as tk
from tkinter import filedialog, messagebox
import os

class Token:
    def __init__(self, type, value, line, column):
        self.type = type  # "KEYWORD", "OPERATOR", "IDENTIFIER", "LITERAL", "ERROR" vb.
        self.value = value
        self.line = line
        self.column = column

class Lexer:
    def __init__(self):
        self.keywords = {
            "def", "for", "if", "else", "while", "elif", "try", "except", "finally",
            "class", "None", "lambda", "with", "as", "import", "from", "async",
            "await", "break", "continue", "pass", "return", "True", "False",
            "global", "nonlocal", "assert", "raise", "del", "match", "case",
            "and", "or", "not", "in", "is"
        }
        self.operators = {
            "+", "-", "*", "/", "=", "==", "<", ">", "<=", ">=", "%", "//", "**",
            "&", "|", "^", "~", "<<", ">>", "@", ":=", "!=", ":", ",", "(", ")",
            "[", "]", "{", "}", ".", ";"
        }
        self.literals = {"True", "False", "None"}  # Özel literaller
        self.current_char = ""
        self.pos = -1
        self.line = 1
        self.column = 0
        self.text = ""

    def set_text(self, text):
        self.text = text
        self.pos = -1
        self.line = 1
        self.column = 0
        self.current_char = ""

    def advance(self):
        self.pos += 1
        self.column += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def tokenize(self):
        tokens = []
        self.advance()

        while self.current_char is not None:
            if self.current_char.isspace():
                if self.current_char == "\n":
                    self.line += 1
                    self.column = 0
                self.advance()
                continue

            if self.current_char == "#":
                comment = ""
                start_column = self.column
                while self.current_char is not None and self.current_char != "\n":
                    comment += self.current_char
                    self.advance()
                tokens.append(Token("COMMENT", comment, self.line, start_column))
                continue

            if self.current_char in ['"', "'"] and self.pos + 2 < len(self.text) and self.text[self.pos:self.pos+3] in ['"""', "'''"]:
                quote = self.text[self.pos:self.pos+3]
                comment = quote
                start_line = self.line
                start_column = self.column
                self.advance()
                self.advance()
                self.advance()
                while self.current_char is not None and self.text[self.pos:self.pos+3] != quote:
                    if self.current_char == "\n":
                        self.line += 1
                        self.column = 0
                    comment += self.current_char
                    self.advance()
                if self.current_char is not None:
                    comment += self.text[self.pos:self.pos+3]
                    self.advance()
                    self.advance()
                    self.advance()
                tokens.append(Token("COMMENT", comment, start_line, start_column))
                continue

            if self.current_char in self.operators:
                op = self.current_char
                start_column = self.column
                self.advance()
                if self.current_char is not None and op + self.current_char in self.operators:
                    op += self.current_char
                    self.advance()
                tokens.append(Token("OPERATOR", op, self.line, start_column))
                continue

            if self.current_char.isalpha() or self.current_char == "_":
                identifier = ""
                start_column = self.column
                while self.current_char is not None and (self.current_char.isalnum() or self.current_char == "_"):
                    identifier += self.current_char
                    self.advance()
                if identifier in self.literals:
                    token_type = "LITERAL"
                elif identifier in self.keywords:
                    token_type = "KEYWORD"
                else:
                    token_type = "IDENTIFIER"
                tokens.append(Token(token_type, identifier, self.line, start_column))
                continue

            if self.current_char.isdigit():
                number = ""
                start_column = self.column
                is_float = False
                while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
                    if self.current_char == ".":
                        if is_float:
                            tokens.append(Token("ERROR", number, self.line, start_column))
                            break
                        is_float = True
                    number += self.current_char
                    self.advance()
                tokens.append(Token("NUMBER", number, self.line, start_column))
                continue

            if self.current_char in ['"', "'"]:
                tokens.extend(self.tokenize_string())
                continue

            # Hatalı karakter
            tokens.append(Token("ERROR", self.current_char, self.line, self.column))
            self.advance()

        return tokens

    def tokenize_string(self):
        quote = self.current_char
        string = ""
        start_line = self.line
        start_column = self.column
        is_f_string = self.pos > 0 and self.text[self.pos - 1].lower() == 'f'
        string += quote
        self.advance()
        tokens = []
        while self.current_char is not None:
            if self.current_char == quote and self.text[self.pos:self.pos+2] != quote * 2:
                string += self.current_char
                self.advance()
                tokens.append(Token("FSTRING" if is_f_string else "STRING", string, start_line, start_column))
                return tokens
            if is_f_string and self.current_char == "{":
                if string:
                    tokens.append(Token("FSTRING", string, start_line, start_column))
                    string = ""
                    start_line = self.line
                    start_column = self.column
                self.advance()
                expr = ""
                brace_count = 1
                while self.current_char is not None and brace_count > 0:
                    if self.current_char == "\n":
                        self.line += 1
                        self.column = 0
                    if self.current_char == "{":
                        brace_count += 1
                    elif self.current_char == "}":
                        brace_count -= 1
                    expr += self.current_char
                    self.advance()
                if brace_count == 0 and self.current_char is not None:
                    tokens.append(Token("FSTRING_EXPR", "{" + expr, start_line, start_column))
                else:
                    tokens.append(Token("ERROR", "{" + expr, start_line, start_column))
                continue
            if self.current_char == "\n":
                self.line += 1
                self.column = 0
            string += self.current_char
            self.advance()
        # Kapanmamış dize için hata token'ı
        tokens.append(Token("ERROR", string, start_line, start_column))
        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None
        self.max_iterations = 10000  # Sonsuz döngü önleme

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def peek(self):
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

    def expect(self, token_type, value=None):
        if self.current_token and self.current_token.type == token_type and (value is None or self.current_token.value == value):
            self.advance()
        else:
            self.advance()  # Hata toleransı için devam et

    def parse(self):
        statements = []
        iteration_count = 0
        while self.current_token is not None and iteration_count < self.max_iterations:
            statements.append(self.parse_statement())
            iteration_count += 1
        if iteration_count >= self.max_iterations:
            print("Parser: Maksimum iterasyon sınırına ulaşıldı.")
        return statements

    def parse_statement(self):
        if self.current_token and self.current_token.type == "KEYWORD":
            if self.current_token.value == "def":
                return self.parse_function_def()
            elif self.current_token.value == "async":
                return self.parse_async_stmt()
            elif self.current_token.value == "if":
                return self.parse_if_stmt()
            elif self.current_token.value == "for":
                return self.parse_for_stmt()
            elif self.current_token.value == "while":
                return self.parse_while_stmt()
            elif self.current_token.value == "try":
                return self.parse_try_stmt()
            elif self.current_token.value == "class":
                return self.parse_class_def()
            elif self.current_token.value == "import":
                return self.parse_import_stmt()
            elif self.current_token.value == "from":
                return self.parse_from_stmt()
            elif self.current_token.value == "with":
                return self.parse_with_stmt()
            elif self.current_token.value == "match":
                return self.parse_match_stmt()
            elif self.current_token.value in ["break", "continue", "pass", "return", "raise", "yield"]:
                return self.parse_control_stmt()
            elif self.current_token.value == "global":
                return self.parse_global_stmt()
            elif self.current_token.value == "nonlocal":
                return self.parse_nonlocal_stmt()
            elif self.current_token.value == "assert":
                return self.parse_assert_stmt()
            elif self.current_token.value == "del":
                return self.parse_del_stmt()
        elif self.current_token and self.current_token.type == "IDENTIFIER":
            return self.parse_assignment()
        elif self.current_token and self.current_token.type == "COMMENT":
            comment = self.current_token.value
            self.advance()
            return ("COMMENT", comment)
        elif self.current_token and self.current_token.type == "ERROR":
            error = self.current_token.value
            self.advance()
            return ("ERROR", error)
        else:
            return self.parse_expression_stmt()

    def parse_function_def(self):
        decorators = []
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "@":
            decorators.append(self.parse_decorator())
        is_async = False
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "async":
            self.expect("KEYWORD", "async")
            is_async = True
        self.expect("KEYWORD", "def")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        self.expect("OPERATOR", "(")
        params = self.parse_param_list()
        self.expect("OPERATOR", ")")
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        return ("FUNCTION_DEF", identifier, params, suite, decorators, is_async)

    def parse_decorator(self):
        self.expect("OPERATOR", "@")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        return ("DECORATOR", identifier)

    def parse_param_list(self):
        params = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "IDENTIFIER" and iteration_count < self.max_iterations:
            params.append(self.current_token.value)
            self.expect("IDENTIFIER")
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return params

    def parse_suite(self):
        statements = []
        self.expect("OPERATOR", ":")
        iteration_count = 0 
        while self.current_token and iteration_count < self.max_iterations:
            if self.current_token.type == "KEYWORD" and self.current_token.value in ["elif", "else", "except", "finally"]:
                break  # Suite'i sonlandır
            statements.append(self.parse_statement())
            iteration_count += 1
        return statements

    def parse_async_stmt(self):
        self.expect("KEYWORD", "async")
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "def":
            return self.parse_function_def()
        elif self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "with":
            return self.parse_with_stmt()
        elif self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "for":
            return self.parse_for_stmt()
        else:
            return ("ASYNC_STMT", None)

    def parse_if_stmt(self):
        self.expect("KEYWORD", "if")
        expression = self.parse_expression()
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        elif_stmts = []
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "elif":
            self.expect("KEYWORD", "elif")
            elif_expr = self.parse_expression()
            self.expect("OPERATOR", ":")
            elif_suite = self.parse_suite()
            elif_stmts.append(("ELIF", elif_expr, elif_suite))
        else_suite = None
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "else":
            self.expect("KEYWORD", "else")
            self.expect("OPERATOR", ":")
            else_suite = self.parse_suite()
        return ("IF_STMT", expression, suite, elif_stmts, else_suite)

    def parse_for_stmt(self):
        is_async = False
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "async":
            self.expect("KEYWORD", "async")
            is_async = True
        self.expect("KEYWORD", "for")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        self.expect("KEYWORD", "in")
        expression = self.parse_expression()
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        return ("FOR_STMT", identifier, expression, suite, is_async)

    def parse_while_stmt(self):
        self.expect("KEYWORD", "while")
        expression = self.parse_expression()
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        return ("WHILE_STMT", expression, suite)

    def parse_try_stmt(self):
        self.expect("KEYWORD", "try")
        self.expect("OPERATOR", ":")
        try_suite = self.parse_suite()
        except_stmts = []
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "except":
            self.expect("KEYWORD", "except")
            self.expect("OPERATOR", ":")
            except_suite = self.parse_suite()
            except_stmts.append(("EXCEPT", except_suite))
        finally_suite = None
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "finally":
            self.expect("KEYWORD", "finally")
            self.expect("OPERATOR", ":")
            finally_suite = self.parse_suite()
        return ("TRY_STMT", try_suite, except_stmts, finally_suite)

    def parse_class_def(self):
        self.expect("KEYWORD", "class")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        bases = []
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "(":
            self.expect("OPERATOR", "(")
            if self.current_token and self.current_token.type == "IDENTIFIER":
                bases.append(self.current_token.value)
                self.expect("IDENTIFIER")
                while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                    self.expect("OPERATOR", ",")
                    if self.current_token and self.current_token.type == "IDENTIFIER":
                        bases.append(self.current_token.value)
                        self.expect("IDENTIFIER")
            self.expect("OPERATOR", ")")
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        return ("CLASS_DEF", identifier, bases, suite)

    def parse_import_stmt(self):
        self.expect("KEYWORD", "import")
        identifiers = []
        if self.current_token and self.current_token.type == "IDENTIFIER":
            identifiers.append(self.current_token.value)
            self.expect("IDENTIFIER")
            while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
                if self.current_token and self.current_token.type == "IDENTIFIER":
                    identifiers.append(self.current_token.value)
                    self.expect("IDENTIFIER")
        return ("IMPORT_STMT", identifiers)

    def parse_from_stmt(self):
        self.expect("KEYWORD", "from")
        module = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        self.expect("KEYWORD", "import")
        identifiers = []
        if self.current_token and self.current_token.type == "IDENTIFIER":
            identifiers.append(self.current_token.value)
            self.expect("IDENTIFIER")
            while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
                if self.current_token and self.current_token.type == "IDENTIFIER":
                    identifiers.append(self.current_token.value)
                    self.expect("IDENTIFIER")
        return ("FROM_IMPORT_STMT", module, identifiers)

    def parse_with_stmt(self):
        is_async = False
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "async":
            self.expect("KEYWORD", "async")
            is_async = True
        self.expect("KEYWORD", "with")
        expression = self.parse_expression()
        identifier = None
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "as":
            self.expect("KEYWORD", "as")
            identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
            self.expect("IDENTIFIER")
        self.expect("OPERATOR", ":")
        suite = self.parse_suite()
        return ("WITH_STMT", expression, identifier, suite, is_async)

    def parse_match_stmt(self):
        self.expect("KEYWORD", "match")
        expression = self.parse_expression()
        self.expect("OPERATOR", ":")
        cases = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "case" and iteration_count < self.max_iterations:
            self.expect("KEYWORD", "case")
            pattern = self.parse_pattern()
            self.expect("OPERATOR", ":")
            suite = self.parse_suite()
            cases.append(("CASE", pattern, suite))
            iteration_count += 1
        return ("MATCH_STMT", expression, cases)

    def parse_pattern(self):
        if self.current_token and self.current_token.type in ["NUMBER", "STRING", "FSTRING"]:
            value = self.current_token.value
            self.advance()
            return ("LITERAL", value)
        elif self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value in ["True", "False", "None"]:
            value = self.current_token.value
            self.advance()
            return ("LITERAL", value)
        elif self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "[":
            self.expect("OPERATOR", "[")
            patterns = self.parse_pattern_list()
            self.expect("OPERATOR", "]")
            return ("LIST_PATTERN", patterns)
        elif self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "{":
            self.expect("OPERATOR", "{")
            items = self.parse_dict_pattern_list()
            self.expect("OPERATOR", "}")
            return ("DICT_PATTERN", items)
        elif self.current_token and self.current_token.type == "IDENTIFIER":
            value = self.current_token.value
            self.expect("IDENTIFIER")
            return ("IDENTIFIER", value)
        else:
            return ("PATTERN", None)

    def parse_pattern_list(self):
        patterns = []
        iteration_count = 0
        while self.current_token and (self.current_token.type not in ["OPERATOR"] or self.current_token.value != "]") and iteration_count < self.max_iterations:
            patterns.append(self.parse_pattern())
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return patterns

    def parse_dict_pattern_list(self):
        items = []
        iteration_count = 0
        while self.current_token and (self.current_token.type not in ["OPERATOR"] or self.current_token.value != "}") and iteration_count < self.max_iterations:
            key = self.parse_pattern()
            self.expect("OPERATOR", ":")
            value = self.parse_pattern()
            items.append((key, value))
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return items

    def parse_control_stmt(self):
        control_type = self.current_token.value
        self.expect("KEYWORD", control_type)
        if control_type in ["return", "yield"]:
            expr = self.parse_expression() if self.current_token and self.current_token.type != "OPERATOR" else None
            return (control_type.upper() + "_STMT", expr)
        elif control_type == "raise":
            expr = self.parse_expression()
            return ("RAISE_STMT", expr)
        else:  # break, continue, pass
            return (control_type.upper() + "_STMT", None)

    def parse_global_stmt(self):
        self.expect("KEYWORD", "global")
        identifiers = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "IDENTIFIER" and iteration_count < self.max_iterations:
            identifiers.append(self.current_token.value)
            self.expect("IDENTIFIER")
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return ("GLOBAL_STMT", identifiers)

    def parse_nonlocal_stmt(self):
        self.expect("KEYWORD", "nonlocal")
        identifiers = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "IDENTIFIER" and iteration_count < self.max_iterations:
            identifiers.append(self.current_token.value)
            self.expect("IDENTIFIER")
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return ("NONLOCAL_STMT", identifiers)

    def parse_assert_stmt(self):
        self.expect("KEYWORD", "assert")
        expr = self.parse_expression()
        msg = None
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
            self.expect("OPERATOR", ",")
            msg = self.parse_expression()
        return ("ASSERT_STMT", expr, msg)

    def parse_del_stmt(self):
        self.expect("KEYWORD", "del")
        targets = self.parse_target_list()
        return ("DEL_STMT", targets)

    def parse_assignment(self):
        targets = self.parse_target_list()
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["=", ":="]:
            op = self.current_token.value
            self.expect("OPERATOR", op)
            expressions = self.parse_expression_list()
            return ("ASSIGNMENT", targets, op, expressions)
        else:
            return ("ASSIGNMENT", targets, None, [])

    def parse_target_list(self):
        targets = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "IDENTIFIER" and iteration_count < self.max_iterations:
            targets.append(self.current_token.value)
            self.expect("IDENTIFIER")
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["(", "["]:
            delim = self.current_token.value
            self.expect("OPERATOR", delim)
            targets = self.parse_target_list()
            self.expect("OPERATOR", "]" if delim == "[" else ")")
        return targets

    def parse_fstring_expr(self):
        if self.current_token and self.current_token.type == "FSTRING_EXPR":
            expr_value = self.current_token.value[1:-1]
            self.advance()
            temp_lexer = Lexer()
            temp_lexer.set_text(expr_value)
            temp_tokens = temp_lexer.tokenize()
            temp_parser = Parser(temp_tokens)
            expr = temp_parser.parse_expression()
            return ("FSTRING_EXPR", expr)
        return None

    def parse_expression(self):
        expr = self.parse_if_expr()
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ".":
            self.expect("OPERATOR", ".")
            if self.current_token and self.current_token.type == "IDENTIFIER":
                attr = self.current_token.value
                self.expect("IDENTIFIER")
                expr = ("ATTRIBUTE", expr, attr)
            else:
                break
        return expr

    def parse_if_expr(self):
        expr = self.parse_logical_or_expr()
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "if":
            self.expect("KEYWORD", "if")
            cond = self.parse_logical_or_expr()
            if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "else":
                self.expect("KEYWORD", "else")
                else_expr = self.parse_if_expr()
                return ("IF_EXPR", expr, cond, else_expr)
        return expr

    def parse_logical_or_expr(self):
        expr = self.parse_logical_and_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "or" and iteration_count < self.max_iterations:
            self.expect("KEYWORD", "or")
            right = self.parse_logical_and_expr()
            expr = ("LOGICAL_OR", expr, right)
            iteration_count += 1
        return expr

    def parse_logical_and_expr(self):
        expr = self.parse_not_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "and" and iteration_count < self.max_iterations:
            self.expect("KEYWORD", "and")
            right = self.parse_not_expr()
            expr = ("LOGICAL_AND", expr, right)
            iteration_count += 1
        return expr

    def parse_not_expr(self):
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "not":
            self.expect("KEYWORD", "not")
            expr = self.parse_not_expr()
            return ("NOT", expr)
        return self.parse_comparison()

    def parse_comparison(self):
        expr = self.parse_bitwise_or_expr()
        iteration_count = 0
        while self.current_token and (
            (self.current_token.type == "KEYWORD" and self.current_token.value in ["in", "is"]) or
            (self.current_token.type == "OPERATOR" and self.current_token.value in ["<", ">", "==", ">=", "<=", "!="])
        ) and iteration_count < self.max_iterations:
            if self.current_token.type == "KEYWORD" and self.current_token.value == "in":
                peek_token = self.peek()
                if peek_token and peek_token.type == "KEYWORD" and peek_token.value == "not":
                    self.expect("KEYWORD", "in")
                    self.expect("KEYWORD", "not")
                    right = self.parse_bitwise_or_expr()
                    expr = ("NOT_IN", expr, right)
                else:
                    self.expect("KEYWORD", "in")
                    right = self.parse_bitwise_or_expr()
                    expr = ("IN", expr, right)
            elif self.current_token.type == "KEYWORD" and self.current_token.value == "is":
                peek_token = self.peek()
                if peek_token and peek_token.type == "KEYWORD" and peek_token.value == "not":
                    self.expect("KEYWORD", "is")
                    self.expect("KEYWORD", "not")
                    right = self.parse_bitwise_or_expr()
                    expr = ("IS_NOT", expr, right)
                else:
                    self.expect("KEYWORD", "is")
                    right = self.parse_bitwise_or_expr()
                    expr = ("IS", expr, right)
            else:
                op = self.current_token.value
                self.advance()
                right = self.parse_bitwise_or_expr()
                expr = ("COMPARISON", expr, op, right)
            iteration_count += 1
        return expr

    def parse_bitwise_or_expr(self):
        expr = self.parse_bitwise_xor_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "|" and iteration_count < self.max_iterations:
            self.expect("OPERATOR", "|")
            right = self.parse_bitwise_xor_expr()
            expr = ("BITWISE_OR", expr, right)
            iteration_count += 1
        return expr

    def parse_bitwise_xor_expr(self):
        expr = self.parse_bitwise_and_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "^" and iteration_count < self.max_iterations:
            self.expect("OPERATOR", "^")
            right = self.parse_bitwise_and_expr()
            expr = ("BITWISE_XOR", expr, right)
            iteration_count += 1
        return expr

    def parse_bitwise_and_expr(self):
        expr = self.parse_shift_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "&" and iteration_count < self.max_iterations:
            self.expect("OPERATOR", "&")
            right = self.parse_shift_expr()
            expr = ("BITWISE_AND", expr, right)
            iteration_count += 1
        return expr

    def parse_shift_expr(self):
        expr = self.parse_arith_expr()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["<<", ">>"] and iteration_count < self.max_iterations:
            op = self.current_token.value
            self.expect("OPERATOR", op)
            right = self.parse_arith_expr()
            expr = ("SHIFT", expr, op, right)
            iteration_count += 1
        return expr

    def parse_arith_expr(self):
        expr = self.parse_term()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["+", "-"] and iteration_count < self.max_iterations:
            op = self.current_token.value
            self.expect("OPERATOR", op)
            right = self.parse_term()
            expr = ("ARITH", expr, op, right)
            iteration_count += 1
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        iteration_count = 0
        while self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["*", "/", "//", "%"] and iteration_count < self.max_iterations:
            op = self.current_token.value
            self.expect("OPERATOR", op)
            right = self.parse_factor()
            expr = ("TERM", expr, op, right)
            iteration_count += 1
        return expr

    def parse_factor(self):
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value in ["+", "-", "~"]:
            op = self.current_token.value
            self.expect("OPERATOR", op)
            expr = self.parse_factor()
            return ("UNARY", op, expr)
        return self.parse_power()

    def parse_power(self):
        expr = self.parse_primary()
        if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "**":
            self.expect("OPERATOR", "**")
            right = self.parse_factor()
            expr = ("POWER", expr, right)
        return expr

    def parse_primary(self):
        if self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "lambda":
            return self.parse_lambda_expr()
        elif self.current_token and self.current_token.type in ["NUMBER", "STRING", "FSTRING"]:
            value = self.current_token.value
            self.advance()
            return ("LITERAL", value)
        elif self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value in ["True", "False", "None"]:
            value = self.current_token.value
            self.advance()
            return ("LITERAL", value)
        elif self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "[":
            self.expect("OPERATOR", "[")
            peek_token = self.peek()
            if peek_token and peek_token.type == "KEYWORD" and peek_token.value == "for":
                comp = self.parse_comprehension()
                self.expect("OPERATOR", "]")
                return ("LIST_COMP", comp)
            exprs = self.parse_expression_list()
            self.expect("OPERATOR", "]")
            return ("LIST", exprs)
        elif self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "{":
            self.expect("OPERATOR", "{")
            peek_token = self.peek()
            if peek_token and peek_token.type == "OPERATOR" and peek_token.value == ":":
                items = self.parse_dict_item_list()
                self.expect("OPERATOR", "}")
                return ("DICT", items)
            elif peek_token and peek_token.type == "KEYWORD" and peek_token.value == "for":
                comp = self.parse_dict_comprehension()
                self.expect("OPERATOR", "}")
                return ("DICT_COMP", comp)
            else:
                exprs = self.parse_expression_list()
                self.expect("OPERATOR", "}")
                return ("SET", exprs)
        elif self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "(":
            self.expect("OPERATOR", "(")
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ")":
                self.expect("OPERATOR", ")")
                return ("TUPLE", [])
            expr = self.parse_expression()
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
                exprs = [expr] + self.parse_expression_list()
                self.expect("OPERATOR", ")")
                return ("TUPLE", exprs)
            self.expect("OPERATOR", ")")
            return expr
        elif self.current_token and self.current_token.type == "IDENTIFIER":
            identifier = self.current_token.value
            self.advance()
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == "(":
                self.expect("OPERATOR", "(")
                args = self.parse_expression_list()
                self.expect("OPERATOR", ")")
                return ("CALL", identifier, args)
            return ("IDENTIFIER", identifier)
        elif self.current_token and self.current_token.type == "ERROR":
            value = self.current_token.value
            self.advance()
            return ("ERROR", value)
        else:
            return ("EXPRESSION", None)

    def parse_lambda_expr(self):
        self.expect("KEYWORD", "lambda")
        params = self.parse_param_list()
        self.expect("OPERATOR", ":")
        expr = self.parse_expression()
        return ("LAMBDA", params, expr)

    def parse_comprehension(self):
        expr = self.parse_expression()
        self.expect("KEYWORD", "for")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        self.expect("KEYWORD", "in")
        iterable = self.parse_expression()
        conds = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "if" and iteration_count < self.max_iterations:
            self.expect("KEYWORD", "if")
            conds.append(self.parse_expression())
            iteration_count += 1
        return ("COMP", expr, identifier, iterable, conds)

    def parse_dict_comprehension(self):
        key = self.parse_expression()
        self.expect("OPERATOR", ":")
        value = self.parse_expression()
        self.expect("KEYWORD", "for")
        identifier = self.current_token.value if self.current_token and self.current_token.type == "IDENTIFIER" else ""
        self.expect("IDENTIFIER")
        self.expect("KEYWORD", "in")
        iterable = self.parse_expression()
        conds = []
        iteration_count = 0
        while self.current_token and self.current_token.type == "KEYWORD" and self.current_token.value == "if" and iteration_count < self.max_iterations:
            self.expect("KEYWORD", "if")
            conds.append(self.parse_expression())
            iteration_count += 1
        return ("DICT_COMP", key, value, identifier, iterable, conds)

    def parse_expression_list(self):
        exprs = []
        iteration_count = 0
        while self.current_token and (
            self.current_token.type not in ["OPERATOR"] or
            self.current_token.value not in ["]", ")", "}", ":"]
        ) and iteration_count < self.max_iterations:
            exprs.append(self.parse_expression())
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return exprs

    def parse_dict_item_list(self):
        items = []
        iteration_count = 0
        while self.current_token and (self.current_token.type not in ["OPERATOR"] or self.current_token.value != "}") and iteration_count < self.max_iterations:
            key = self.parse_expression()
            self.expect("OPERATOR", ":")
            value = self.parse_expression()
            items.append((key, value))
            if self.current_token and self.current_token.type == "OPERATOR" and self.current_token.value == ",":
                self.expect("OPERATOR", ",")
            else:
                break
            iteration_count += 1
        return items

    def parse_expression_stmt(self):
        expr = self.parse_expression()
        return ("EXPR_STMT", expr)

class SyntaxHighlighterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PySyntaxHighlight")
        self.lexer = Lexer()
        self.parser = None
        self.is_dark_mode = False
        self.current_file = None
        self.last_text = ""  # Performans için son metni sakla
        self.last_changed_line = 0  # Son değişen satır

        # Tema renkleri 
        self.light_theme = {
            "bg": "#FFFFFF",  # Beyaz zemin
            "fg": "#000000",  # Siyah yazı
            "keyword": "#0033A0",        # Koyu mavi
            "operator": "#000000",       # Siyah
            "number": "#D32F2F",         # Canlı kırmızı
            "string": "#388E3C",         # Koyu yeşil
            "fstring": "#388E3C",
            "fstring_expr": "#00796B",   # Teal
            "comment": "#9E9E9E",        # Gri
            "identifier": "#000000",     # Siyah
            "constant": "#6A1B9A",       # Mor
            "error": "#C62828",          # Kırmızı
            "decorator": "#EF6C00",      # Turuncu
            "function_def": "#00695C",   # Camgöbeği
            "class_def": "#1E88E5",      # Parlak mavi
            "call": "#1565C0",           # Mavi ton
            "lambda": "#00838F",         # Camgöbeği
            "loop_var": "#512DA8",       # Mor
            "conditional": "#3949AB",    # Koyu mavi
            "parameter": "#5D4037",      # Kahverengi
            "attribute": "#F57C00",      # Turuncu
            "line_numbers_bg": "#F0F0F0",
            "line_numbers_fg": "#888888"
        }

        self.dark_theme = {
            "bg": "#1E1E1E",
            "fg": "#D4D4D4",
            "keyword": "#569CD6",        # Mavi
            "operator": "#D4D4D4",       # Açık gri
            "number": "#B5CEA8",         # Açık yeşil
            "string": "#CE9178",         # Somon
            "fstring": "#CE9178",
            "fstring_expr": "#4EC9B0",   # Turkuaz
            "comment": "#6A9955",        # Yumuşak yeşil
            "identifier": "#D4D4D4",
            "constant": "#C586C0",       # Mor
            "error": "#F44747",          # Parlak kırmızı
            "decorator": "#DCDCAA",      # Sarımsı
            "function_def": "#DCDCAA",
            "class_def": "#4EC9B0",      # Camgöbeği
            "call": "#9CDCFE",           # Açık mavi
            "lambda": "#569CD6",
            "loop_var": "#C586C0",
            "conditional": "#569CD6",
            "parameter": "#9CDCFE",
            "attribute": "#D7BA7D",      # Sarımsı
            "line_numbers_bg": "#2D2D2D",
            "line_numbers_fg": "#858585"
        }

        self.current_theme = self.light_theme

        # Ana çerçeve
        self.main_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Menü çubuğu
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Dosya", menu=self.file_menu)
        self.file_menu.add_command(label="Aç", command=self.open_file)
        self.file_menu.add_command(label="Kaydet", command=self.save_file)
        self.file_menu.add_command(label="Farklı Kaydet", command=self.save_file_as)
        self.menubar.add_command(label="Tema Değiştir", command=self.toggle_theme)

        # Satır numaraları için metin alanı
        self.line_numbers = tk.Text(self.main_frame, width=4, padx=3, takefocus=0, border=0,
                                   background=self.current_theme["line_numbers_bg"],
                                   foreground=self.current_theme["line_numbers_fg"],
                                   state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Metin alanı ve kaydırma çubuğu
        self.text_area = tk.Text(self.main_frame, height=20, width=80, bg=self.current_theme["bg"],
                                 fg=self.current_theme["fg"], insertbackground=self.current_theme["fg"],
                                 wrap=tk.NONE)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Metin alanı ve satır numaralarını kaydırma çubuğuyla bağla
        self.text_area.config(yscrollcommand=self.sync_scroll)
        self.line_numbers.config(yscrollcommand=self.line_numbers.yview)
        self.scrollbar.config(command=self.on_scrollbar)

        # Renk ayarları
        self.update_tag_configurations()

        # Olay bağlamaları
        self.highlight_timer = None
        self.text_area.bind("<KeyRelease>", self.schedule_highlight)
        self.text_area.bind("<Return>", self.handle_return)
        self.text_area.bind("<MouseWheel>", self.update_line_numbers)
        self.text_area.bind("<Button-4>", self.update_line_numbers)  # Linux için
        self.text_area.bind("<Button-5>", self.update_line_numbers)  # Linux için

        # Başlangıçta satır numaralarını güncelle
        self.update_line_numbers()

    def update_tag_configurations(self):
        """Metin alanı için tema renklerini günceller."""
        token_types = [
            "KEYWORD", "OPERATOR", "NUMBER", "STRING", "FSTRING", "FSTRING_EXPR",
            "COMMENT", "IDENTIFIER", "CONSTANT", "ERROR", "DECORATOR",
            "FUNCTION_DEF", "CLASS_DEF", "CALL", "LAMBDA", "LOOP_VAR",
            "CONDITIONAL", "PARAMETER", "ATTRIBUTE"
        ]
        for token_type in token_types:
            self.text_area.tag_configure(token_type, foreground=self.current_theme[token_type.lower()])
        self.text_area.config(bg=self.current_theme["bg"], fg=self.current_theme["fg"],
                            insertbackground=self.current_theme["fg"])
        self.line_numbers.config(background=self.current_theme["line_numbers_bg"],
                                foreground=self.current_theme["line_numbers_fg"])
        self.main_frame.config(bg=self.current_theme["bg"])
        
    def toggle_theme(self):
        """Açık ve koyu tema arasında geçiş yapar."""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = self.dark_theme if self.is_dark_mode else self.light_theme
        self.update_tag_configurations()
        self.highlight_syntax()
        self.update_line_numbers()

    def sync_scroll(self, *args):
        """Metin alanı ve satır numaralarını senkronize eder."""
        self.scrollbar.set(*args)

    def on_scrollbar(self, *args):
        """Kaydırma çubuğu hareket ettiğinde her iki widget'ı kaydırır."""
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete("1.0", tk.END)
        start_index = self.text_area.index("@0,0")
        end_index = self.text_area.index(f"@0,{self.text_area.winfo_height()}")
        start_line = int(start_index.split('.')[0])
        end_line = int(end_index.split('.')[0])
        total_lines = int(self.text_area.index("end-1c").split('.')[0])
        end_line = min(end_line, total_lines)
        line_numbers = "\n".join(str(i) for i in range(start_line, end_line + 1))
        self.line_numbers.insert("1.0", line_numbers)
        self.line_numbers.config(state='disabled')

    def handle_return(self, event):
        self.text_area.insert("insert", "\n")
        self.text_area.see("insert")
        self.root.after(10, self.update_line_numbers)
        self.last_changed_line = int(self.text_area.index("insert").split('.')[0])
        return "break"

    def open_file(self):
        """Dosya açma işlemi."""
        file_path = filedialog.askopenfilename(filetypes=[("Python Dosyaları", "*.py"), ("Tüm Dosyalar", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert("1.0", content)
                    self.current_file = file_path
                    self.root.title(f"Python Sözdizimi Vurgulayıcı - {os.path.basename(file_path)}")
                    self.last_text = ""  # Vurgulamayı zorla tetiklemek için sıfırla
                    self.highlight_syntax()  # Vurgulamayı hemen uygula
                    self.update_line_numbers()
            except Exception as e:
                    messagebox.showerror("Hata", f"Dosya açılamadı: {str(e)}")

    def save_file(self):
        """Dosya kaydetme işlemi."""
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get("1.0", tk.END).rstrip("\n"))
                messagebox.showinfo("Başarılı", "Dosya kaydedildi.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya kaydedilemedi: {str(e)}")
        else:
            self.save_file_as()

    def save_file_as(self):
        """Farklı kaydet işlemi."""
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                 filetypes=[("Python Dosyaları", "*.py"), ("Tüm Dosyalar", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get("1.0", tk.END).rstrip("\n"))
                self.current_file = file_path
                self.root.title(f"Python Sözdizimi Vurgulayıcı - {os.path.basename(file_path)}")
                messagebox.showinfo("Başarılı", "Dosya kaydedildi.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya kaydedilemedi: {str(e)}")

    def schedule_highlight(self, event=None):
        """Vurgulamayı gecikmeli planlar."""
        if self.highlight_timer:
            self.root.after_cancel(self.highlight_timer)
        self.highlight_timer = self.root.after(300, self.highlight_syntax)

    def highlight_syntax(self, event=None):
        """Sözdizimi vurgulama işlemini gerçekleştirir."""
        self.highlight_timer = None
        text = self.text_area.get("1.0", tk.END).rstrip("\n")
        if text == self.last_text:
            return  # Metin değişmediyse tekrar vurgulama
        self.last_text = text

        # Tüm metni tokenlaştır
        self.lexer.set_text(text)
        tokens = self.lexer.tokenize()
        self.parser = Parser(tokens)
        statements = self.parser.parse()

        # Önceki vurgulama etiketlerini kaldır
        for tag in self.text_area.tag_names():
            self.text_area.tag_remove(tag, "1.0", tk.END)

        # Lexer token’larını vurgulama
        for token in tokens:
            start_pos = f"{token.line}.{token.column - 1}"
            end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
            try:
                tag = "CONSTANT" if token.type == "LITERAL" else token.type
                self.text_area.tag_add(tag, start_pos, end_pos)
            except tk.TclError:
                continue  # Geçersiz pozisyonları atla

        # Ayrıştırıcı çıktılarını kullanarak ek yapıları vurgulama
        for stmt in statements:
            if stmt[0] == "FUNCTION_DEF":
                identifier, params, suite, decorators, is_async = stmt[1], stmt[2], stmt[3], stmt[4], stmt[5]
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == identifier:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("FUNCTION_DEF", start_pos, end_pos)
                        except tk.TclError:
                            continue
                    # Parametreleri renklendirme
                    for param in params:
                        if token.type == "IDENTIFIER" and token.value == param:
                            start_pos = f"{token.line}.{token.column - 1}"
                            end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                            try:
                                self.text_area.tag_add("PARAMETER", start_pos, end_pos)
                            except tk.TclError:
                                continue
            elif stmt[0] == "CLASS_DEF":
                identifier, bases, suite = stmt[1], stmt[2], stmt[3]
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == identifier:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("CLASS_DEF", start_pos, end_pos)
                        except tk.TclError:
                            continue
            elif stmt[0] == "DECORATOR":
                identifier = stmt[1]
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == identifier:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("DECORATOR", start_pos, end_pos)
                        except tk.TclError:
                            continue
            elif stmt[0] == "CALL":
                identifier, args = stmt[1], stmt[2]
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == identifier:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("CALL", start_pos, end_pos)
                        except tk.TclError:
                            continue
            elif stmt[0] == "LAMBDA":
                params, expr = stmt[1], stmt[2]
                for token in tokens:
                    if token.type == "KEYWORD" and token.value == "lambda":
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("LAMBDA", start_pos, end_pos)
                        except tk.TclError:
                            continue
                    # Lambda parametrelerini renklendirme
                    for param in params:
                        if token.type == "IDENTIFIER" and token.value == param:
                            start_pos = f"{token.line}.{token.column - 1}"
                            end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                            try:
                                self.text_area.tag_add("PARAMETER", start_pos, end_pos)
                            except tk.TclError:
                                continue
            elif stmt[0] == "FOR_STMT":
                identifier, expr, suite, is_async = stmt[1], stmt[2], stmt[3], stmt[4]
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == identifier:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("LOOP_VAR", start_pos, end_pos)
                        except tk.TclError:
                            continue
            elif stmt[0] == "IF_STMT":
                expr, suite, elif_stmts, else_suite = stmt[1], stmt[2], stmt[3], stmt[4]
                def highlight_expr(expr, tag="CONDITIONAL"):
                    if isinstance(expr, tuple):
                        for sub_expr in expr[1:]:
                            highlight_expr(sub_expr, tag)
                    elif isinstance(expr, str):
                        for token in tokens:
                            if token.type in ["IDENTIFIER", "NUMBER", "STRING", "CONSTANT"] and token.value == expr:
                                start_pos = f"{token.line}.{token.column - 1}"
                                end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                                try:
                                    self.text_area.tag_add(tag, start_pos, end_pos)
                                except tk.TclError:
                                    continue
                highlight_expr(expr)
                for elif_stmt in elif_stmts:
                    highlight_expr(elif_stmt[1])  # ELIF ifadeleri için
            elif stmt[0] == "EXPRESSION" and isinstance(stmt[1], tuple) and stmt[1][0] == "ATTRIBUTE":
                attr = stmt[1][2]  # Nitelik adı
                for token in tokens:
                    if token.type == "IDENTIFIER" and token.value == attr:
                        start_pos = f"{token.line}.{token.column - 1}"
                        end_pos = f"{token.line}.{token.column - 1 + len(token.value)}"
                        try:
                            self.text_area.tag_add("ATTRIBUTE", start_pos, end_pos)
                        except tk.TclError:
                            continue

if __name__ == "__main__":
    root = tk.Tk()
    app = SyntaxHighlighterGUI(root)
    root.mainloop()