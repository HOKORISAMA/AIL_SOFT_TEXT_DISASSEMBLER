import sys
from Disassemble import Disassembler
from Utilities import GlobalBuffer

def disassemble(file_path: str) -> None:
    """Public interface for disassembly."""
    disassembler = Disassembler()
    disassembler.disassemble(file_path)
    print(f"[DEBUG] Shared disassembler id: {id(disassembler)}")



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python disassemble.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    disassemble(file_path)