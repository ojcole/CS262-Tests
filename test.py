import click
import subprocess
import logging
import random
import string
import sys
import pandas
from os import remove
from tabulate import tabulate
import sympy
from sympy.logic.boolalg import Nand, Not, Nor, Xor, Equivalent, Implies, And, Or
from sympy.logic.inference import satisfiable

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

logger.addHandler(handler)

SYMBOLS = list(string.ascii_lowercase)
sympsymbs = sympy.symbols(SYMBOLS)

BINARY_OPERATORS = [("and", "And"), ("uparrow", "Nand"), ("or", "Or"), ("downarrow", "Nor"),
                    ("imp", "Implies"), ("notimp", "s"), ("revimp", "s"), ("notrevimp", "s"),
                    ("equiv", "Equivalent"), ("notequiv", "Xor")]


@click.command()
@click.option("--maxdepth", default=5, help="Maximum depth of the generated problems")
@click.option("--seed", default="notquitehaskell", help="Seed to generate the problems")
@click.option("--tests", default=None,
              help="CSV containing test cases **Must be in the test folder**")
@click.option("--plfile", default="resolution.pl", help="File containing your source")
@click.option("--count", default=30, help="How many tests to run")
@click.option("--symbols", default=5, help="How many symbols to include in the problem")
@click.option("--quiet", default=False, is_flag=True, help="Avoids outputting until the end")
def main(maxdepth, seed, tests, plfile, count, symbols, quiet, errors):
    """ Entry point of the test script """
    if tests is not None:
        data = pandas.read_csv(f"tests/{tests}", header=None)

        problems = list(data[0])
        solutions = list(data[1])

        actual_results = run_problems(problems, plfile)

        same = ["PASS" if solutions[i] == actual_results[i]
                else "FAIL" for i in range(len(solutions))]

        res = list(zip(problems, solutions, actual_results, same))

        logger.info(tabulate(res, headers=[
                    "Problem", "Expected", "Actual", "Result"]))

    else:
        random.seed(seed)
        problem_symbols = SYMBOLS[:symbols]
        try:
            problems = [generate_problem(
                maxdepth, problem_symbols) for _ in range(int(count))]
            solutions = []
            actual_results = []
            same = []
            for infix, clause in problems:
                if not quiet:
                    logger.info(f"Running test on {infix}")

                actual_res = run_problems([infix], plfile)[0]
                solution = solve_problem(clause)

                solutions.append(solution)
                actual_results.append(actual_res)

                res = "PASS" if actual_res == solution else "FAIL"

                if not quiet:
                    logger.info(res)

                same.append(res)

            logger.info("Summary:")

            res = list(zip(map(lambda x: x[0], problems), solutions, actual_results, same))

            logger.info(tabulate(res, headers=[
                "Problem", "Expected", "Actual", "Result"]))

            if all(map(lambda x: x == "PASS", same)):
                logger.info("ALL PASSED")

        except AssertionError:
            logger.error("Prolog program produced unexpected output. Expecting YES or NO")
        except ValueError:
            logger.error("Tests needs to be a number")


def generate_problem(maxdepth: int, symbs: list) -> (str, str):
    if maxdepth <= 0:
        rand = random.randint(0, len(symbs) - 1)
        infix = symbs[rand]
        clause = f"sympsymbs[{rand}]"
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

    problem_string = ",".join(map(lambda x: f"test({x}),writeln(\"\")", problems))

    tmp.write(contents + f"\n\nrun :- {problem_string}.")

    p = subprocess.Popen(["swipl", "--quiet", "-l", "temp.pl", "-t",
                          f"run"], stdout=subprocess.PIPE)

    p.wait()
    result, _ = p.communicate()
    stringres = bytes(result).decode("utf-8").strip()

    tmp.close()
    resolution.close()

    remove("temp.pl")

    return stringres.split("\n")


def solve_problem(problem: str) -> str:
    return "NO" if isinstance(eval(f"satisfiable(Not({problem}))"), dict) else "YES"


if __name__ == "__main__":
    main()
