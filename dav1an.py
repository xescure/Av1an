#!/bin/python3

import argparse
import subprocess
import os
import sys
from typing import List, Or



def resolve_path(path):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)

    # if not os.path.isabs(path) and relative_directory:
    #     path = os.path.join(relative_directory, path)
    # path = os.path.normpath(path)

    return path


class Mounter:
    arg: str
    file: os.PathLike

    def __init__(
        self,
        arg: str,
        file: Or[os.PathLike, str]
    ) -> None:
        self.arg = arg
        self.file = resolve_path(file)

    @property
    def container_location(self) -> str:
        return f'/{self.arg}'

    @property
    def new_arg(self) -> List[str]:
        return [
            f"{'-' if len(self.arg) == 1 else '--'}{self.arg}",
            f"{self.container_location}/{os.path.basename(self.file)}",
        ]

    @property
    def dockerv(self) -> List[str]:
        return [
            "-v",
            f"{os.path.dirname(self.file)}:{self.container_location}",
        ]


class Dav1an:
    DOCKER_INPUT_DIR = "/input"
    DOCKER_OUTPUT_DIR = "/output"

    input_dir: str = None
    input_file: str = None

    output_dir: str = None
    output_file: str = None

    encoder: str = None
    encoder_branch: str = None

    @staticmethod
    def resolve_path(path):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.abspath(path)

        # if not os.path.isabs(path) and relative_directory:
        #     path = os.path.join(relative_directory, path)

        # path = os.path.normpath(path)

        return path

    def parse_arguments(self, args=None):
        if args is None:
            args = self.captured_args

        if args.encoder:
            parsed_encoder = args.encoder.split("_", 1)
            self.encoder = parsed_encoder[0]
            if len(parsed_encoder) == 2:
                self.encoder_branch = parsed_encoder[1]

        if args.i:
            self.input_path = self.resolve_path(args.i)
            self.input_dir, self.input_file = os.path.split(self.input_path)

        if args.o:
            self.output_path = self.resolve_path(args.o)
            self.output_dir, self.output_file = os.path.split(self.output_path)

    def get_docker_image(self):
        tag = self.encoder
        if self.encoder_branch:
            tag += f"_{self.encoder_branch}"

        return f"xescure/av1an:{tag}"

    def get_docker_command(self, remaining_args=None):
        if remaining_args is None:
            remaining_args = self.remaining_args

        command = [
            "docker",
            "run",
            "--rm",
            "--privileged",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
        ]

        if self.input_path and self.output_path:
            command.extend(
                [
                    "-v",
                    f"{self.input_dir}:{self.DOCKER_INPUT_DIR}",
                    "-v",
                    f"{self.output_dir}:{self.DOCKER_OUTPUT_DIR}",
                ]
            )

        command.append(self.get_docker_image())

        if self.input_path and self.output_path:
            command.extend(
                [
                    "-i",
                    f"{self.DOCKER_INPUT_DIR}/{self.input_file}",
                    "-o",
                    f"{self.DOCKER_OUTPUT_DIR}/{self.output_file}",
                    "-e",
                    self.encoder,
                ]
            )

        if remaining_args:
            command.extend(remaining_args)

        return command

    def run_docker(self, extra_args=None):
        command = self.get_docker_command()
        subprocess.run(command)

    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog="dav1an",
            description="A wrapper for av1an docker containers",
            add_help=False,
            allow_abbrev=False,
            usage="",
        )

        parser.add_argument("-e", "--encoder")  # capture version number from encoder
        parser.add_argument("-i")  # input file
        parser.add_argument("-o")  # output file

        self.captured_args, self.remaining_args = parser.parse_known_args()

        self.parse_arguments()


if __name__ == "__main__":
    dav1an = Dav1an()
    print(dav1an.get_docker_command())
    # dav1an.run_docker()
    print(sys.argv)
