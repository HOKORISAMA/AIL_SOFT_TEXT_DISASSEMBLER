import struct
from typing import Union, BinaryIO, Optional
from dataclasses import dataclass

Buffer = Union[bytearray, bytes]
Stream = BinaryIO

@dataclass
class GlobalBuffer:
    command_data: bytearray
    text_data: bytearray
    command_data_offset: int = 0
    text_data_offset: int = 0

@dataclass
class FileHeader:
    """Represents the file header structure."""
    reserved1: int
    command_block_size: int
    command_block_for_text_size: int
    string_table_size: int
    reserved2: int
    
    def __str__(self) -> str:
        return (f"Header Information:\n"
                f"Reserved1: {self.reserved1}\n"
                f"Command Block Size: {self.command_block_size}\n"
                f"Command Block for Text Size: {self.command_block_for_text_size}\n"
                f"String Table Size: {self.string_table_size}\n"
                f"Reserved2: {self.reserved2}")


def read_next_opcode() -> Optional[int]:
    """Read the next opcode from command data."""
    return get_next_byte()

def sub_42164D(a1):
    """
    Lookup table function - searches for a1 in a table and returns corresponding value
    Based on the C code pattern
    """
    result = 0
    v2 = 0
    
    # dword_53AAE4 is the table size (0xee = 238 bytes)
    table_size = 0xee  # 238 bytes
    table_base = 0  # You'll need to set this appropriately
    data = [0]*table_size  # Pre-allocate memory for the table
    
    if table_size - 1 > 0:
        # Search through the table in pairs
        while v2 < table_size - 1:
            # Each entry is 4 bytes (2 words): search_value, result_value
            # Read directly from the table memory location
            search_value = int.from_bytes(data[table_base + v2:table_base + v2 + 2], 'little')
            if search_value == a1:
                # Found match, return the corresponding result value
                result = int.from_bytes(data[table_base + v2 + 2:table_base + v2 + 4], 'little')
                break
            v2 += 4  # Move to next pair (each pair is 4 bytes)
    
    word_53A590 = a1  # Store the search value
    return result

def _sub_414FE6(a1, a2):
    """
    Bit manipulation function equivalent to C sub_414FE6
    Extracts a bit field from word_498710[a1] based on mask pattern in a2
    """
    if a2 == 0:
        return a2
    
    # Find position of first set bit (shift count)
    i = 0
    temp_a2 = a2 & 0xFFFF  # Keep as 16-bit
    while (temp_a2 & 1) == 0:
        i += 1
        temp_a2 = temp_a2 >> 1
    
    # Count consecutive set bits (bit field width)
    v4 = 0
    while (temp_a2 & 1) != 0:
        v4 += 1
        temp_a2 = temp_a2 >> 1
    
    # Create mask: sub_4151AA(v4) = (1 << v4) - 1
    mask = (1 << v4) - 1
    
    # Since word_498710 is all zeros, this will always return 0
    # # But implementing the full logic for completeness
    # if hasattr(self, 'word_498710') and a1 < len(self.word_498710):
    #     value = self.word_498710[a1] & 0xFFFF
    # else:
    #     value = 0  # Array is all zeros as you mentioned
    value = 0  # Assuming word_498710 is all zeros as per your context
    
    # Extract bit field: shift right by i positions, then mask
    result = (value >> i) & mask
    return result

def get_next_byte() -> int:    
    """Reads the next byte from the command data buffer."""

    # Check bounds
    if GlobalBuffer.command_data_offset >= len(GlobalBuffer.command_data):
        return None
    
    # Read byte and update the global offset (mimics int_op_16 += 1 in C)
    byte_value = GlobalBuffer.command_data[GlobalBuffer.command_data_offset]
    GlobalBuffer.command_data_offset += 1
    
    return byte_value


def get_next_word() -> int:
    """Mimics the C function get_next_text_offset() / sub_426C5B"""    
    # Check bounds
    if GlobalBuffer.command_data_offset + 1 >= len(GlobalBuffer.command_data):
        return None
    
    # Read 16-bit value from command data (little-endian)
    word = read_uint16(GlobalBuffer.command_data[GlobalBuffer.command_data_offset:GlobalBuffer.command_data_offset+2])

    # Update the global offset (mimics int_op_16 += 2 in C)
    GlobalBuffer.command_data_offset += 2

    return word

def read_C_string(data: bytes, txt_offset: int) -> tuple[int, str]:
    """
    Read a null-terminated string from data starting at txt_offset.
    Handles both single null (0x00) and double null (0x00 0x00) terminators.
    
    Args:
        data: The byte data to read from
        txt_offset: The starting offset for this string
    
    Returns:
        tuple: (bytes_read, decoded_string)
    """
    
    # Start reading from the given offset
    result = bytearray()
    current_offset = txt_offset
    null_terminator_found = False
    
    # Read byte by byte until we find null terminator(s)
    while current_offset < len(data):
        current_byte = data[current_offset]
        
        # Check for null terminator
        if current_byte == 0:
            # Check if this is a double null terminator (0x00 0x00)
            if (current_offset + 1 < len(data) and 
                data[current_offset + 1] == 0):
                # Double null terminator - move past both bytes
                current_offset += 2
                null_terminator_found = True
                break
            else:
                # Single null terminator - move past one byte
                current_offset += 1
                null_terminator_found = True
                break
        
        # Regular byte - add to result
        result.append(current_byte)
        current_offset += 1
        
        # Safety check - don't read more than 5000 bytes
        if len(result) > 5000:
            break
    
    # Decode the string
    try:
        decoded_string = result.decode('shift_jis').strip('\x00')
    except UnicodeDecodeError:
        print("UnicodeDecodeError: Unable to decode string, using fallback.")
        decoded_string = result.decode('cp932').strip('\x00')
    
    # Calculate total bytes read (including null terminator)
    bytes_read = current_offset - txt_offset
    
    return bytes_read, decoded_string

# ---------- READ FUNCTIONS ----------

def read_uint16(data: Union[Buffer, Stream], offset: int = 0) -> int:
    return _read_struct('<H', data, offset)

def read_uint32(data: Union[Buffer, Stream], offset: int = 0) -> int:
    return _read_struct('<I', data, offset)

def read_int16(data: Union[Buffer, Stream], offset: int = 0) -> int:
    return _read_struct('<h', data, offset)

def read_int32(data: Union[Buffer, Stream], offset: int = 0) -> int:
    return _read_struct('<i', data, offset)


# ---------- WRITE FUNCTIONS ----------

def write_uint16(value: int) -> bytes:
    return struct.pack('<H', value)

def write_uint32(value: int) -> bytes:
    return struct.pack('<I', value)

def write_int16(value: int) -> bytes:
    return struct.pack('<h', value)

def write_int32(value: int) -> bytes:
    return struct.pack('<i', value)


# ---------- INTERNAL ----------

def _read_struct(fmt: str, data: Union[Buffer, Stream], offset: int) -> int:
    size = struct.calcsize(fmt)
    if isinstance(data, (bytes, bytearray)):
        return struct.unpack_from(fmt, data, offset)[0]
    elif hasattr(data, 'read'):
        data.seek(offset)
        return struct.unpack(fmt, data.read(size))[0]
    else:
        raise TypeError("Expected bytes-like object or file-like stream.")
