#!/usr/bin/env python3

import hashlib
import re
from dataclasses import dataclass, asdict
from typing import Sequence


BASE36_LOWERCASE_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def b36encode(b: bytes, alphabet: Sequence[str] = BASE36_LOWERCASE_ALPHABET) -> str:
    num = int.from_bytes(b, byteorder="big")

    base36 = ""

    while num:
        num, i = divmod(num, 36)
        base36 = alphabet[i] + base36

    return base36


# Reference in GitLab's codebase:
# https://gitlab.com/gitlab-org/gitlab-runner/-/blob/16102dd7edb4ef9602ade59afccae04337929f41/Makefile.build.mk#L64
#
# echo $(BRANCH)
# | cut -c -63
# | sed -E 's/[^a-z0-9-]+/-/g'
# | sed -E 's/^-*([a-z0-9-]+[a-z0-9])-*$$/\1/g'
def generate_commit_ref_slug(branch: str) -> str:
    return re.sub("[^a-z0-9-]+", "-", branch.lower()[:63]).strip("-")


# Reference in GitLab's codebase:
# https://gitlab.com/gitlab-org/gitlab/-/blob/e9b70ffa9204e57c1a89046d9e591aa16873e661/lib/gitlab/slug/environment.rb
def generate_environment_slug(environment_name: str) -> str:
    # Turn to lowercase and replace all non-alphanumeric chars
    # with a dash
    slug = re.sub("[^a-z0-9]", "-", environment_name.lower())

    # If the slug does not start with a letter, prepend env-
    if not re.match("[a-z]", slug):
        slug = "env-" + slug

    # Collapse multiple consecutive dashes
    slug = re.sub(r"\-+", "-", slug)

    # If the environment name was already a valid slug and it is shorter
    # than 24 characters, leave it as is
    if len(slug) <= 24 and slug == environment_name:
        return slug

    # Truncate the slug to 16 characters and make sure it ends
    # with a dash
    slug = slug[:16]
    if not slug.endswith("-"):
        slug += "-"

    # Generate the SHA256 hash of the environment name and convert it
    # to base36.
    hash = hashlib.sha256(environment_name.encode()).digest()
    base36_hash = b36encode(hash)

    # Concatenate the slug to the last 6 characters
    return slug + base36_hash[-6:]


def interpolate_env_variables(string: str, env_variables: dict[str, str]) -> str:
    # env_variables = {
    #     "CI_COMMIT_REF_NAME": branch_name,
    #     "CI_COMMIT_REF_SLUG": commit_ref_slug,
    # }

    for key, val in env_variables.items():
        string = string.replace(f"${key}", val).replace(f"${{{key}}}", val)

    return string


@dataclass
class PredefinedVariables:
    CI_COMMIT_REF_NAME: str
    CI_COMMIT_REF_SLUG: str
    CI_ENVIRONMENT_NAME: str
    CI_ENVIRONMENT_SLUG: str

    @staticmethod
    def generate(
        branch: str, environment_name: str, env_variables: dict[str, str] = {}
    ) -> "PredefinedVariables":
        commit_ref_slug = generate_commit_ref_slug(branch)

        environment_name = interpolate_env_variables(
            environment_name,
            env_variables={
                **env_variables,
                "CI_COMMIT_REF_NAME": branch,
                "CI_COMMIT_REF_SLUG": commit_ref_slug,
            },
        )

        environment_slug = generate_environment_slug(environment_name)

        return PredefinedVariables(
            CI_COMMIT_REF_NAME=branch,
            CI_COMMIT_REF_SLUG=commit_ref_slug,
            CI_ENVIRONMENT_NAME=environment_name,
            CI_ENVIRONMENT_SLUG=environment_slug,
        )


def _cli_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="gitlab-ci-env",
        description="""\
Generate the predefined GitLab CI environment variables for a given branch.

Example:
gitlab-ci-env --branch TEST-branch --environment-name 'deployment-$CI_COMMIT_REF_SLUG'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--branch",
        help="Upstream branch name of the merge request.",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--environment-name",
        help="Environment name of the CI step from the .gitlab-ci.yml configuration. References to the CI_COMMIT_REF_SLUG and CI_COMMIT_REF_NAME env variables will be resolved.",
        required=True,
        type=str,
    )

    return parser


if __name__ == "__main__":
    args = _cli_parser().parse_args()

    predefined_variables = PredefinedVariables.generate(
        branch=args.branch,
        environment_name=args.environment_name,
    )

    import json
    import sys

    json.dump(asdict(predefined_variables), sys.stdout, indent=2)
