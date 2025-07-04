from Utilities import GlobalBuffer, _sub_414FE6, sub_42164D
from Fake_Stack import execute_vm_code
from NormalOpcodeTable import NormalOpcodeDisassembler
from typing import Optional
from enum import IntEnum

class SysCallOpcodes(IntEnum):
    """VM Opcode constants for better readability."""
    BASIC_OPERATION = 0x00
    PLAY_WAV = 0x04
    AUDIO_OP = 0x05
    SIMPLE_JUMP = 0x08
    SWITCH_CASE = 0x09
    SCENARIO_LOAD = 0x0A
    CALL_OPERATION = 0x0B
    CONDITIONAL_JUMP = 0x0C
    RETURN = 0x0D
    SCENARIO_CALL = 0x10
    END_PROCESSING = 0x11
    CONDITIONAL_SKIP = 0x12

class SysCallOpcodeDisassemblerError(Exception):
    """Custom exception for SysCallOpcodeDisassembler errors."""
    pass

class SysCallOpcodeDisassembler:
    def __init__(self):
        self.normal_opcode_disassembler = NormalOpcodeDisassembler()
        self.debug = True  # Add debug flag for controlling output
    
    def process_sys_calls(self) -> None:
        """Process all VM commands in the data - fixed byte consumption logic."""
        try:
            while GlobalBuffer.command_data_offset < len(GlobalBuffer.command_data):
                current_offset = GlobalBuffer.command_data_offset
                
                opcode = self._get_next_byte()
                if opcode is None:
                    break
                
                if self.debug:
                    print(f"At offset {current_offset}: Processing opcode {opcode} (0x{opcode:02X})")
                
                self._process_opcode(opcode, current_offset)
                
        except SysCallOpcodeDisassemblerError as e:
            print(f"VM Error: {e}")
        except Exception as e:
            print(f"Unexpected error in process_sys_calls: {e}")
    
    def _process_opcode(self, opcode: int, current_offset: int) -> None:
        """Process a single opcode."""
        if opcode > 0x0B:  # Extended opcodes
            self._process_extended_opcode(opcode, current_offset)
        else:
            self._process_basic_opcode(opcode, current_offset)
    
    def _process_extended_opcode(self, opcode: int, current_offset: int) -> None:
        """Process extended opcodes (> 0x0B)."""
        adjusted_opcode = opcode - 12
        
        opcode_handlers = {
            0: self._handle_conditional_jump,      # Case 12 (0x0C)
            1: self._handle_return,                # Case 13 (0x0D)
            4: self._handle_scenario_call,         # Case 16 (0x10)
            5: self._handle_end_processing,        # Case 17 (0x11)
            6: self._handle_conditional_skip,      # Case 18 (0x12)
        }
        
        handler = opcode_handlers.get(adjusted_opcode)
        if handler:
            handler(current_offset)
        else:
            print(f"Unknown adjusted opcode {adjusted_opcode} for base opcode {opcode}")
    
    def _process_basic_opcode(self, opcode: int, current_offset: int) -> None:
        """Process basic opcodes (<= 0x0B)."""
        opcode_handlers = {
            SysCallOpcodes.BASIC_OPERATION: self._handle_basic_operation,
            SysCallOpcodes.PLAY_WAV: self._handle_play_wav_opcode,
            SysCallOpcodes.AUDIO_OP: self._handle_audio_operation,
            SysCallOpcodes.SIMPLE_JUMP: self._handle_simple_jump,
            SysCallOpcodes.SWITCH_CASE: self._handle_switch_case,
            SysCallOpcodes.SCENARIO_LOAD: self._handle_scenario_load_opcode,
            SysCallOpcodes.CALL_OPERATION: self._handle_call_operation_opcode,
        }
        
        handler = opcode_handlers.get(opcode)
        if handler:
            handler(current_offset)
        else:
            print(f"Unhandled opcode 0x{opcode:02X} at offset {current_offset}")

    def _get_next_byte(self) -> Optional[int]:
        """Get next byte from command data."""
        if GlobalBuffer.command_data_offset >= len(GlobalBuffer.command_data):
            return None
        
        byte_val = GlobalBuffer.command_data[GlobalBuffer.command_data_offset]
        GlobalBuffer.command_data_offset += 1
        return byte_val

    def _get_next_word(self) -> Optional[int]:
        """Get next 16-bit word from command data."""
        if GlobalBuffer.command_data_offset + 1 >= len(GlobalBuffer.command_data):
            return None
        
        # Read little-endian 16-bit word
        low_byte = GlobalBuffer.command_data[GlobalBuffer.command_data_offset]
        high_byte = GlobalBuffer.command_data[GlobalBuffer.command_data_offset + 1]
        GlobalBuffer.command_data_offset += 2
        
        return low_byte | (high_byte << 8)

    def _safe_get_next_byte(self) -> int:
        """Get next byte with error checking."""
        byte_val = self._get_next_byte()
        if byte_val is None:
            raise SysCallOpcodeDisassemblerError("Unexpected end of data while reading byte")
        return byte_val

    def _safe_get_next_word(self) -> int:
        """Get next word with error checking."""
        word_val = self._get_next_word()
        if word_val is None:
            raise SysCallOpcodeDisassemblerError("Unexpected end of data while reading word")
        return word_val

    def _evaluate_expression(self) -> int:
        """Evaluate expression - this consumes variable number of bytes."""
        return execute_vm_code()

    def _jump_to_offset(self, offset: int) -> None:
        """Jump to specific offset in command data."""
        if 0 <= offset < len(GlobalBuffer.command_data):
            # GlobalBuffer.command_data_offset = offset
            if self.debug:
                print(f"Jumping to offset {offset}")

    def _main_interpreter(self) -> int:
        """Main opcode interpreter that may consume bytes internally."""
        return self.normal_opcode_disassembler.process_single_command()

    # Opcode handlers
    def _handle_conditional_jump(self, current_offset: int) -> None:
        """Handle conditional jump operation."""
        condition = self._evaluate_expression()
        jump_target = sub_42164D(condition)
        if self.debug:
            print(f"Conditional jump at offset {current_offset}, condition: {condition}, target: {jump_target}")

    def _handle_return(self, current_offset: int) -> None:
        """Handle return operation."""
        if self.debug:
            print(f"Return operation at offset {current_offset}")

    def _handle_scenario_call(self, current_offset: int) -> None:
        """Handle scenario call operation."""
        scenario_id = self._evaluate_expression()
        return_point = self._evaluate_expression()
        extra_param = self._evaluate_expression()
        if self.debug:
            print(f"Scenario call at offset {current_offset}: {scenario_id}, return: {return_point}, param: {extra_param}")

    def _handle_end_processing(self, current_offset: int) -> None:
        """Handle end processing operation."""
        if self.debug:
            print(f"End processing at offset {current_offset}")
        return

    def _handle_conditional_skip(self, current_offset: int) -> None:
        """Handle conditional skip operation."""
        condition = self._evaluate_expression()
        if not condition:
            jump_target = self._safe_get_next_word()
            if self.debug:
                print(f"Conditional skip at offset {current_offset}, jumping to {jump_target}")

    def _handle_basic_operation(self, current_offset: int) -> None:
        """Handle basic operation."""
        if self.debug:
            print(f"[Sys Call] Executing main Interpreter at offset {current_offset}")
        self._main_interpreter()

    def _handle_play_wav_opcode(self, current_offset: int) -> None:
        """Handle play WAV opcode."""
        wav_param = self._safe_get_next_byte()
        wav_id = self._safe_get_next_word()
        expression_result = self._evaluate_expression()
        self._handle_play_wav(wav_param, wav_id, expression_result)

    def _handle_audio_operation(self, current_offset: int) -> None:
        """Handle audio operation."""
        if self.debug:
            print(f"Audio operation at offset {current_offset}")
        audio_param = self._safe_get_next_byte()
        audio_id = self._safe_get_next_word()
        jump_result = self._main_interpreter()
        if self.debug:
            print(f"Jump result: {jump_result}")
        self._handle_audio_op(audio_param, audio_id, jump_result)

    def _handle_simple_jump(self, current_offset: int) -> None:
        """Handle simple jump operation."""
        jump_target = self._safe_get_next_word()
        if self.debug:
            print(f"Simple jump at offset {current_offset} to {jump_target}")

    def _handle_switch_case(self, current_offset: int) -> None:
        """Handle switch/case operation."""
        if self.debug:
            print(f"Switch operation at offset {current_offset}")
        
        switch_param_raw = self._safe_get_next_byte()
        switch_value = self._safe_get_next_word()
        default_target = self._safe_get_next_word()
        case_count = self._safe_get_next_byte()
        
        if self.debug:
            print(f"Raw switch param: {switch_param_raw}, switch value: {switch_value}")
        
        processed_switch_param = _sub_414FE6(switch_param_raw, switch_value)
        if self.debug:
            print(f"Processed switch param: {processed_switch_param}")
            print(f"Switch operation: comparing {processed_switch_param} against {case_count} cases, default target {default_target}")
        
        found_match = False
        for i in range(case_count):
            case_value = self._safe_get_next_byte()
            case_target = self._safe_get_next_word()
            
            if self.debug:
                print(f"Case {i}: value={case_value}, target={case_target}")
            
            if case_value == 255 or processed_switch_param == case_value:
                if self.debug:
                    print(f"Match found! Processed param {processed_switch_param} matches case value {case_value}")
                    print(f"Target would be {case_target}")
                found_match = True
        
        if not found_match and self.debug:
            print(f"No match found for processed param {processed_switch_param}, would use default target {default_target}")

    def _handle_scenario_load_opcode(self, current_offset: int) -> None:
        """Handle scenario load opcode."""
        scenario_id = self._evaluate_expression()
        self._handle_scenario_load(scenario_id)
        
        # Skip zero padding bytes
        next_byte = self._get_next_byte()
        while next_byte == 0 and next_byte is not None:
            next_byte = self._get_next_byte()
            if next_byte is None:
                break

    def _handle_call_operation_opcode(self, current_offset: int) -> None:
        """Handle call operation opcode."""
        target_offset = self._evaluate_expression()
        return_address = self._evaluate_expression()
        self._handle_call_operation(target_offset, return_address)

    # Helper methods for actual operations
    def _handle_call_operation(self, target: int, return_addr: int) -> bool:
        """Handle call operation."""
        if self.debug:
            print(f"Call to {target}, return to {return_addr}")
        return True

    def _handle_play_wav(self, param: int, wav_id: int, expression: int) -> None:
        """Handle play WAV operation."""
        if self.debug:
            print(f"Play WAV: param={param}, id={wav_id}, expr={expression}")

    def _handle_audio_op(self, param: int, audio_id: int, jump_result: int) -> None:
        """Handle audio operation."""
        if self.debug:
            print(f"Audio op: param={param}, id={audio_id}, jump={jump_result}")

    def _handle_scenario_load(self, scenario_id: int) -> None:
        """Handle scenario load."""
        if self.debug:
            print(f"Load scenario: {scenario_id}")