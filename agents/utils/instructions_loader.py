"""Utility for loading agent instructions from text files."""

import os
from pathlib import Path


def load_instruction_from_file(filename: str, relative_to_caller: bool = True) -> str:
    """
    Load instruction text from a file.
    
    Args:
        filename: Name of the instruction file (e.g., "Main_Agent_Instructions.txt")
        relative_to_caller: If True, looks for the file in the same directory as the calling module.
                           If False, looks in the project root instructions directory.
    
    Returns:
        The content of the instruction file as a string.
    
    Raises:
        FileNotFoundError: If the instruction file doesn't exist.
        IOError: If there's an error reading the file.
    """
    if relative_to_caller:
        # Get the caller's file location from the call stack
        import inspect
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        caller_dir = Path(caller_file).parent
        file_path = caller_dir / filename
    else:
        # Look in project root instructions directory
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