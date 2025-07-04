import Utilities as utils

# Global word table - equivalent to word_498710
word_table = [0] * 256

def read_next_byte():
    """Equivalent to get_next_byte() - reads from global buffer"""
    if utils.GlobalBuffer.command_data_offset >= len(utils.GlobalBuffer.command_data):
        return 0xFF  # End of data marker
    
    return utils.get_next_byte()


def read_processed_value(hwnd=None):
    """Equivalent to sub_426C34() - uses global buffer"""
    table_index = read_next_byte()  # v0 = get_next_byte()
    bit_pattern = utils.get_next_word()  # LOWORD(v2) = get_next_word(v1)
    
    if table_index != 0xFF:
        bit_pattern = extract_bit_field(table_index, bit_pattern)
    
    return bit_pattern & 0xFFFF

def create_mask(bit_count):
    """Equivalent to sub_4151AA(v4) - creates a mask with bit_count bits set"""
    if bit_count <= 0:
        return 0
    return (1 << bit_count) - 1

def extract_bit_field(table_index, bit_pattern):
    """Equivalent to sub_414FE6() - uses global word table"""
    if bit_pattern == 0:
        return bit_pattern
    
    # Count leading zeros (right shifts until we find a 1 bit)
    leading_zeros = 0
    temp_pattern = bit_pattern
    while temp_pattern & 1 == 0:
        leading_zeros += 1
        temp_pattern >>= 1
    
    # Count consecutive ones
    ones_count = 0
    while temp_pattern & 1 != 0:
        ones_count += 1
        temp_pattern >>= 1
    
    # Extract bits from global word table
    word_value = word_table[table_index] if table_index < len(word_table) else 0
    shifted_value = word_value >> leading_zeros
    mask = create_mask(ones_count)
    
    return shifted_value & mask

def execute_vm_code(hwnd=None):
    """
    Complete VM interpreter using global buffers
    
    Equivalent to evaluateExpression() / sub_4214B9() - main VM interpreter
    Uses global command_data and command_data_offset
    """
    value_stack = []  # Stack for values (equivalent to v23 array, v1 pointer)
    flag_stack = []   # Stack for flags (equivalent to v22 array, v2 pointer)
    
    # Main VM execution loop
    while True:
        # Phase 1: Data collection loop
        while True:
            next_byte = read_next_byte()
            
            # Check for termination
            if next_byte == 255:
                return value_stack[0] if value_stack else 0
            
            # If not zero, break to process as operation
            if next_byte != 0:
                break
            
            # Push data to stack (only when next_byte == 0)
            value = read_processed_value(hwnd)
            value_stack.append(value)
            flag_stack.append(0)  # Initialize corresponding flag
        
        # Phase 2: Operation processing
        # next_byte now contains the operation opcode
        operation = read_next_byte()
        
        if operation > 11:
            # Arithmetic and logical operations (12+)
            op_type = operation - 12
            
            if op_type == 0:  # Logical NOT (operation 12)
                # C code complex logic for flag handling
                if len(flag_stack) >= 1:
                    if flag_stack[-1] != 0:
                        flag_stack[-1] = 1
                    else:
                        if len(value_stack) >= 1 and value_stack[-1] != 0:
                            flag_stack[-1] = 1
                        else:
                            flag_stack[-1] = 0
                    # Pop one level from both stacks (v1 -= 2; --v2;)
                    if len(value_stack) >= 1:
                        value_stack.pop()
                    if len(flag_stack) >= 2:
                        flag_stack.pop()
            
            elif op_type == 8:  # Addition (operation 20)
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = (flag_stack[-1] + val) & 0xFFFFFFFF
                    flag_stack.pop()  # --v2
            
            elif op_type == 9:  # Subtraction (operation 21)
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = (flag_stack[-1] - val) & 0xFFFFFFFF
                    flag_stack.pop()
            
            elif op_type == 10:  # Multiplication (operation 22)
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = (flag_stack[-1] * val) & 0xFFFFFFFF
                    flag_stack.pop()
            
            elif op_type == 11:  # Division (operation 23)
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    divisor = value_stack.pop()
                    if divisor != 0:
                        flag_stack[-1] = flag_stack[-1] // divisor
                    else:
                        flag_stack[-1] = 0
                    flag_stack.pop()
            
            elif op_type == 12:  # Modulo (operation 24)
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    divisor = value_stack.pop()
                    if divisor != 0:
                        flag_stack[-1] = flag_stack[-1] % divisor
                    else:
                        # Error condition - equivalent to sub_412956(hWnd, 9, (int)&Class)
                        if hwnd:
                            pass  # Error handler call
                        flag_stack[-1] = 0
                    flag_stack.pop()
        
        else:
            # Comparison operations (0-11)
            if operation == 11:  # Logical NOT
                if len(flag_stack) >= 1:
                    flag_stack[-1] = 1 if flag_stack[-1] == 0 else 0
            
            elif operation == 0:  # Greater than
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if flag_stack[-1] > val else 0
                    flag_stack.pop()
            
            elif operation == 1:  # Less than or equal
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if flag_stack[-1] <= val else 0
                    flag_stack.pop()
            
            elif operation == 2:  # Not equal
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if flag_stack[-1] != val else 0
                    flag_stack.pop()
            
            elif operation == 3:  # Equal
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if val == flag_stack[-1] else 0
                    flag_stack.pop()
            
            elif operation == 4:  # Greater than or equal
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if flag_stack[-1] >= val else 0
                    flag_stack.pop()
            
            elif operation == 5:  # Less than
                if len(value_stack) >= 1 and len(flag_stack) >= 1:
                    val = value_stack.pop()
                    flag_stack[-1] = 1 if flag_stack[-1] < val else 0
                    flag_stack.pop()
            
            elif operation == 10:  # Special zero check operation
                if len(value_stack) >= 1:
                    value_stack[-1] = 1 if value_stack[-1] == 0 else 0
        
        # Loop continues until termination (255) is encountered