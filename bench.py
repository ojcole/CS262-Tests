import click
import random
from helpers import SYMBOLS, generate_problem, run_problem
from alive_progress import alive_bar


@click.command()
@click.option("--maxdepth", default=5, help="Maximum depth of the generated problems")
@click.option("--seed", default="notquitehaskell", help="Seed to generate the problems")
@click.option("--plfile", default="resolution.pl", help="File containing your source")
@click.option("--count", default=30, help="How many tests to run")
@click.option("--symbols", default=5, help="How many symbols to include in the problem")
def main(maxdepth, seed, plfile, count, symbols):
    random.seed(seed)
    problem_symbols = SYMBOLS[:symbols]
    problems = [generate_problem(
        maxdepth, problem_symbols) for _ in range(int(count))]
    problems = list(map(lambda x: x[0], problems))

    resolution = open(plfile, "r+")

    contents = resolution.read()

    with alive_bar(int(count)) as bar:
        for problem in problems:
            run_problem(problem, contents)
            bar()


if __name__ == "__main__":
    main()
