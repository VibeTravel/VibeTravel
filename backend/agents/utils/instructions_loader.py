# agents/utils/instructions_loader.py

import inspect
from pathlib import Path

def load_instruction_from_file(filename: str, relative_to_caller: bool = True) -> str:
    """
    Load instruction text from a file.
    """
    if relative_to_caller:
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        caller_dir = Path(caller_file).parent
        file_path = caller_dir / filename
    else:
        project_root = Path(__file__).parent.parent
        file_path = project_root / "instructions" / filename

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            instructions = f.read().strip()

        if not instructions:
            raise ValueError(f"Instruction file '{filename}' is empty.")

        return instructions

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Instruction file not found: {file_path}\n"
            f"Please ensure the file exists in the same directory as the agent definition."
        )
    except IOError as e:
        raise IOError(f"Error reading instruction file '{filename}': {str(e)}")
