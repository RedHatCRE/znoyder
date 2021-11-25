#!/usr/bin/env python3

import os

from argparse import ArgumentParser
from shutil import rmtree
from subprocess import check_call, CalledProcessError
from sys import exit

URL_BASE_PROJECT = "https://opendev.org/openstack/{project_name}.git"


def process_arguments() -> tuple:
    """ Return the branch, destination folder and project name of the processed arguments"""
    parser = ArgumentParser()
    parser.add_argument(
        '-p', '--projectname',
        dest='project_name',
        help="Insert the project name",
        metavar="PROJECT_NAME",
        required=True
    )
    parser.add_argument(
        '-b', '--branchname',
        dest='branch_name',
        help="Select branch to work",
        metavar="BRANCH_NAME",
        required=True
    )
    parser.add_argument(
        '-d', '--destinationfolder',
        dest='destination_folder',
        help="Insert the destination folder",
        metavar="DESTINATION_FOLDER",
        required=True
    )
    arguments = parser.parse_args()
    return arguments


def clone_project(url: str, branch: str, destination_folder: str) -> None:
    command = ['git', 'clone', '--depth', '1', url, '--branch', branch, destination_folder]
    execute_command(command)


def execute_command(command: list) -> None:
    try:
        check_call(command)
    except CalledProcessError as e:
        print("Error. Details: ", e)
        exit(e.returncode)


def delete_not_specified_files_in_folder(destination_folder: str, files: list = []) -> None:
    for file in os.listdir(destination_folder):
        file_path = os.path.join(destination_folder, file)
        if file in files:
            continue
        rmtree(file_path) if (os.path.isdir(file_path)) else os.remove(file_path)


def main() -> None:
    arguments = process_arguments()
    clone_project(
        URL_BASE_PROJECT.format(project_name=arguments.project_name),
        arguments.branch_name,
        arguments.destination_folder
    )
    delete_not_specified_files_in_folder(arguments.destination_folder, ['.zuul.yaml', 'zuul.d', 'zuul.yaml'])


if __name__ == "__main__":
    main()
