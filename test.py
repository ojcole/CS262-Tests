import click
import subprocess
import logging
import random
import string
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

logger.addHandler(handler)

SYMBOLS = list(string.ascii_lowercase)
BINARY_OPERATORS = ["and", "uparrow", "or", "downarrow", "imp",
                    "notimp", "revimp", "notrevimp", "equiv", "notequiv"]


@click.command()
@click.option("--maxdepth", default=5, help="Maximum depth of the generated problems")
@click.option("--seed", default="notquitehaskell", help="Seed to generate the problems")
@click.option("--file", default="resolution.pl", help="File containing your source")
@click.option("--tests", default=30, help="How many tests to run")
@click.option("--symbols", default=10, help="How many symbols to include in the problem")
def main(maxdepth, seed, file, tests, symbols):
    """ Entry point of the test script """
    random.seed(seed)
    problem_symbols = SYMBOLS[:symbols]
    try:
        for i in range(int(tests)):
            problem = generate_problem(maxdepth, problem_symbols)
            logger.info(f"Running test on {problem}")

            actual_res = solve_problem(problem)
            res = run_problem(problem)

            if res == actual_res:
                logger.info("Success")
    except AssertionError:
        logger.error("Prolog program produced unexpected output. Expecting YES or NO")
    except ValueError:
        logger.error("Tests needs to be a number")


def generate_problem(maxdepth: int, symbs: list) -> str:
    if maxdepth <= 0:
        clause = symbs[random.randint(0, len(symbs) - 1)]
    else:
        clause = generate_problem(maxdepth - random.randint(1, 5), symbs)
        clause += f",{generate_problem(maxdepth - random.randint(1, 5), symbs)}"
        clause = f"{BINARY_OPERATORS[random.randint(0, len(BINARY_OPERATORS) - 1)]}({clause})"

    negs = random.randint(0, 5)

    if negs >= 3:
        for i in range(negs - 3):
            clause = f"neg({clause})"

    return clause


def solve_problem(problem: str) -> bool:
    pass


def run_problem(problem: str) -> bool:
    result = subprocess.check_output(
        ["swipl", "--quiet", "-l", "resolution.pl", "-t", f"test({problem})"])

    logger.info(result)

    assert result == b'YES' or result == b'NO'

    return result == b'YES'


if __name__ == "__main__":
    main()
