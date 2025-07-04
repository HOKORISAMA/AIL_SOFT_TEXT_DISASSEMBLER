import mmap
import os
from Utilities import read_uint16, read_uint32, FileHeader, GlobalBuffer
from SysCallTable import SysCallOpcodeDisassembler

class DisassemblerError(Exception):
    """Custom exception for disassembler errors."""
    pass

class Disassembler:
    def __init__(self, debug: bool = False):
        self.sys_call_executer = SysCallOpcodeDisassembler()
        self.debug = debug
    
    def _read_file_mmap(self, file_path: str) -> bytes:
        """Read file using memory mapping for better performance with large files."""
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DisassemblerError("File is empty")
        
        with open(file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                return mmapped_file.read()
    
    def _read_file_traditional(self, file_path: str) -> bytes:
        """Traditional file reading for smaller files."""
        with open(file_path, 'rb') as f:
            return f.read()
    
    def _read_file(self, file_path: str) -> bytes:
        """Read the binary file with optimal method based on size."""
        try:
            file_size = os.path.getsize(file_path)
            # Use mmap for files larger than 1MB
            if file_size > 1024 * 1024:
                return self._read_file_mmap(file_path)
            else:
                return self._read_file_traditional(file_path)
        except OSError as e:
            raise DisassemblerError(f"Cannot read file '{file_path}': {e}")
    
    def _parse_header(self, data: bytes) -> FileHeader:
        """Parse the file header with optimized unpacking."""
        if len(data) < 12:
            raise DisassemblerError("File too small to contain valid header")
        
        # Use slice assignment for better performance
        header_data = data[:12]
        return FileHeader(
            reserved1=read_uint32(header_data[:4]),
            command_block_size=read_uint16(header_data[4:6]),
            command_block_for_text_size=read_uint16(header_data[6:8]),
            string_table_size=read_uint16(header_data[8:10]),
            reserved2=read_uint16(header_data[10:12])
        )
    
    def _setup_global_buffers(self, data: bytes, header: FileHeader) -> None:
        """Setup global buffer data from file with bounds checking."""
        offset = 12
        
        # Validate file size before processing
        required_size = (12 + header.command_block_size + 
                        header.command_block_for_text_size + 
                        header.string_table_size)
        
        if len(data) < required_size:
            raise DisassemblerError(f"File size {len(data)} is smaller than required {required_size}")
        
        # Skip command block
        offset += header.command_block_size
        
        # Extract command data
        command_end = offset + header.command_block_for_text_size
        GlobalBuffer.command_data = data[offset:command_end]
        offset = command_end
        
        # Extract text data
        text_end = offset + header.string_table_size
        GlobalBuffer.text_data = data[offset:text_end]
        GlobalBuffer.command_data_offset = 0
 
    def disassemble(self, file_path: str) -> None:
        """Main disassembly function with comprehensive error handling."""
        try:
            # Read and parse file
            data = self._read_file(file_path)
            header = self._parse_header(data)
            
            if self.debug:
                print(f"Header: {header}")
                print()
            
            # Setup global buffers
            self._setup_global_buffers(data, header)
            
            # Process system calls
            self.sys_call_executer.process_sys_calls()
            
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
        except DisassemblerError as e:
            print(f"Disassembly error: {e}")
        except Exception as e:
            print(f"Unexpected error during disassembly: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()

    