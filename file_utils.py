import os


def get_file(file_name: str) -> str:
    if os.path.exists(file_name):
        with open(file_name, "r") as fd:
            content = fd.read()
        return content
    else:
        raise FileNotFoundError(f"Requested file: {file_name} does no exist")


def write_file(file_name: str, content: str, should_over_ride: bool):
    if should_over_ride or not os.path.exists(file_name):
        with open(file_name, "w") as fd:
            fd.write(content)
    else:
        raise FileExistsError(f"should over ride: {should_over_ride} but the file {file_name} already exists")
