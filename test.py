import click
import random
import sys
import logging
import string
import pandas
from tabulate import tabulate
from alive_progress import alive_bar
from helpers import generate_problem, run_problems, solve_problem, SYMBOLS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

logger.addHandler(handler)


@click.command()
@click.option("--maxdepth", default=5, help="Maximum depth of the generated problems")
@click.option("--seed", default="notquitehaskell", help="Seed to generate the problems")
@click.option("--tests", default=None, help="CSV containing test cases")
@click.option("--plfile", default="resolution.pl", help="File containing your source")
@click.option("--count", default=30, help="How many tests to run")
@click.option("--symbols", default=5, help="How many symbols to include in the problem")
@click.option("--quiet", default=False, is_flag=True, help="Avoids outputting until the end")
@click.option("--errors", default=False, is_flag=True,
              help="Avoids outputting randomly generated tests which passed")
@click.option("--truths", default=False, is_flag=True, help="Only outputs tautologies")
@click.option("--csvout", default=False, is_flag=True, help="Output in CSV format")
@click.option("--concurrent", default=1, help="Runs many tests at once")
def main(maxdepth, seed, tests, plfile, count, symbols, quiet, errors, truths, csvout, concurrent):
    """ Entry point of the test script """
    if tests is not None:
        try:
            data = pandas.read_csv(tests, header=None)
        except:
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
        if csvout:
            quiet = True

        random.seed(seed)
        problem_symbols = SYMBOLS[:symbols]
        try:
            problems = [generate_problem(
                maxdepth, problem_symbols) for _ in range(int(count))]

            if quiet:
                with alive_bar(int(count)) as bar:
                    run_result = run_generated(problems, quiet, errors, plfile, concurrent, bar)
            else:
                run_result = run_generated(problems, quiet, errors, plfile, concurrent)

            probs, solutions, actual_results, same = run_result

            if not csvout:
                logger.info("Summary:")
                res = list(zip(probs, solutions, actual_results, same))
                if truths:
                    res = list(filter(lambda x: x[1] == "YES", res))
                if len(res) > 0:
                    logger.info(tabulate(res, headers=[
                        "Problem", "Expected", "Actual", "Result"]))

                if all(map(lambda x: x == "PASS", same)):
                    logger.info("ALL PASSED")
            else:
                res = list(zip(probs, solutions))
                if truths:
                    res = list(filter(lambda x: x[1] == "YES", res))
                print("\n".join(map(lambda x: ",".join(x), res)))

        except AssertionError:
            logger.error("Prolog program produced unexpected output. Expecting YES or NO")
        except ValueError:
            logger.error("Tests needs to be a number")


def run_generated(problems, quiet, errors, plfile, concurrent=1, func=lambda: ""):
    probs = []
    solutions = []
    actual_results = []
    same = []

    if concurrent > 1:
        for i in range(0, len(problems), concurrent):
            problemsi = problems[i:i+concurrent]

            actual_reses = run_problems(map(lambda x: x[0], problemsi), plfile)
            sols = [solve_problem(clause) for _, clause in problemsi]

            for j in range(len(problemsi)):
                infix, clause = problemsi[j]
                actual_res = actual_reses[j]
                solution = sols[j]

                append = not errors or actual_res != solution

                res = "PASS" if actual_res == solution else "FAIL"

                if append:
                    probs.append(infix)
                    solutions.append(solution)
                    actual_results.append(actual_res)
                    same.append(res)

                func()
    else:
        for infix, clause in problems:
            if not quiet:
                logger.info(f"Running test on {infix}")

            actual_res = run_problems([infix], plfile)[0]
            solution = solve_problem(clause)

            append = not errors or actual_res != solution

            res = "PASS" if actual_res == solution else "FAIL"

            if append:
                probs.append(infix)
                solutions.append(solution)
                actual_results.append(actual_res)
                same.append(res)

            if not quiet:
                logger.info(res)

            func()

    return probs, solutions, actual_results, same


if __name__ == "__main__":
    main()
