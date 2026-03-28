import argparse

from services.pragmatic import Pragmatic
from services.fambet import Fambet


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        choices=["pragmatic", "fambet"]
    )
    args: argparse.Namespace = parser.parse_args()

    modules: dict = {
        "pragmatic": Pragmatic,
        "fambet": Fambet
    }

    module_class = modules[args.module]
    module_instance = module_class()
    module_instance.run()

if __name__ == "__main__":
    main()
