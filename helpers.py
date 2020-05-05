import string
import sympy
from sympy.logic.boolalg import Nand, Not, Nor, Xor, Equivalent, Implies, And, Or, true, false
from sympy.logic.inference import satisfiable
import random
import subprocess
from os import remove

SYMBOLS = list(string.ascii_lowercase)
sympsymbs = sympy.symbols(SYMBOLS)

BINARY_OPERATORS = [("and", "And"), ("uparrow", "Nand"), ("or", "Or"), ("downarrow", "Nor"),
                    ("imp", "Implies"), ("notimp", "s"), ("revimp", "s"), ("notrevimp", "s"),
                    ("equiv", "Equivalent"), ("notequiv", "Xor")]


def generate_problem(maxdepth: int, symbs: list) -> (str, str):
    if maxdepth <= 0:
        rand = random.randint(0, len(symbs) + 1)

        if rand >= len(symbs):
            clause = ["true", "false"][rand - len(symbs)]
            infix = clause
        else:
            clause = f"sympsymbs[{rand}]"
            infix = symbs[rand]
    else:
        rand1 = random.randint(0, len(BINARY_OPERATORS) - 1)
        rand2 = maxdepth - random.randint(1, 5)
        rand3 = maxdepth - random.randint(1, 5)

        operator, sympop = BINARY_OPERATORS[rand1]
        infix1, sympclause1 = generate_problem(rand2, symbs)
        infix2, sympclause2 = generate_problem(rand3, symbs)
        infix = f"({infix1})" if rand2 > 0 else infix1
        infix += f" {operator} "
        infix += f"({infix2})" if rand3 > 0 else infix2

        if sympop == "s":
            if "rev" in operator:
                tmp = sympclause1
                sympclause1 = sympclause2
                sympclause2 = tmp
                operator = operator.replace("rev", "")

            if operator == "imp":
                sympop = "Implies"

            if operator == "notimp":
                clause = f"Not(Implies({sympclause1}, {sympclause2}))"

        if sympop != "s":
            clause = f"{sympop}({sympclause1}, {sympclause2})"

    negs = random.randint(0, 5)

    if negs >= 3:
        if maxdepth > 0:
            infix = f"({infix})"
        for i in range(negs - 3):
            infix = f"neg {infix}"
            clause = f"Not({clause})"

    return infix, clause


def run_problems(problems: [str], resfile: str) -> [bool]:

    tmp = open("temp.pl", "w+")
    resolution = open(resfile, "r+")

    contents = resolution.read()

    problem_string = ",".join(map(lambda x: f"test({x}),nl", problems))

    tmp.write(
        contents + f"\n\nrun :- {problem_string}.")

    tmp.close()
    resolution.close()

    p = subprocess.Popen(["swipl", "--quiet", "--stack_limit=4G", "-l", "temp.pl", "-t",
                          f"run"], stdout=subprocess.PIPE)

    p.wait()
    result, _ = p.communicate()
    stringres = bytes(result).decode("utf-8").strip()

    while "\n\n" in stringres:
        stringres = stringres.replace("\n\n", "\n")

    remove("temp.pl")

    return stringres.split("\n")


def run_problem(problem: str, contents: str):
    tmp = open("temp.pl", "w+")
    tmp.write(contents + f"\n\nrun :- test({problem}).")
    tmp.close()

    p = subprocess.Popen(["swipl", "--quiet", "--stack_limit=4G", "-l", "temp.pl", "-t",
                          f"run"], stdout=subprocess.DEVNULL)

    p.wait()


def solve_problem(problem: str) -> str:
    return "NO" if isinstance(eval(f"satisfiable(Not({problem}))"), dict) else "YES"
