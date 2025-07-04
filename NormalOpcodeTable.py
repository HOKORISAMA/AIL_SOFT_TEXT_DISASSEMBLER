from Utilities import GlobalBuffer, read_C_string, read_next_opcode, get_next_word
import Fake_Stack as vm
from typing import Optional, Dict, Callable
from enum import IntEnum


class Opcode(IntEnum):
    """Enumeration of all opcodes for better maintainability."""
    STRING_TYPE_0 = 0x00
    STRING_TYPE_1 = 0x01
    UNK_0x02 = 0x02
    NEWLINE = 0x04
    UNK_0x05 = 0x05
    UNK_0x09 = 0x09
    UNK_0x0A = 0x0A
    UNK_0x0B = 0x0B
    UNK_0x10 = 0x10
    UNK_0x12 = 0x12
    UNK_0x13 = 0x13
    SHOW_IMAGES = 0x15
    UNK_0x17 = 0x17
    UNK_0x18 = 0x18
    SHOW_STANDSTILLS = 0x1E
    UNK_0x1F = 0x1F
    UNK_0x28 = 0x28
    UNK_0x30 = 0x30
    UNK_0x32 = 0x32
    UNK_0x33 = 0x33
    UNK_0x34 = 0x34
    UNK_0x35 = 0x35
    UNK_0x38 = 0x38
    UNK_0x3A = 0x3A
    UNK_0x3D = 0x3D
    UNK_0x61 = 0x61
    UNK_0x41 = 0x41
    UNK_0x4F = 0x4F
    UNK_0x71 = 0x71
    UNK_0x72 = 0x72
    UNK_0x79 = 0x79
    UNK_0xA2 = 0xA2
    UNK_0xAD = 0xAD
    UNK_0xA6 = 0xA6
    UNK_0xB3 = 0xB3
    UNK_0xE3 = 0xE3
    UNK_0xEE = 0xEE
    UNK_0xF2 = 0xF2
    UNK_0xF6 = 0xF6
    UNK_0xF7 = 0xF7
    UNK_0xF8 = 0xF8
    PLAY_WAV = 0x44
    UNK_0x45 = 0x45
    UNK_0x46 = 0x46
    UNK_0x47 = 0x47
    PLAY_VOICELINES = 0x48
    UNK_0x4E = 0x4E
    UNK_0x58 = 0x58
    UNK_0x5B = 0x5B
    UNK_0x5D = 0x5D
    UNK_0x5E = 0x5E
    UNK_0x60 = 0x60
    UNK_0x66 = 0x66
    UNK_0x6C = 0x6C
    SCENARIO_VM = 0x6E
    UNK_0x76 = 0x76
    UNK_0x7A = 0x7A
    SET_DELAY = 0x78
    UNK_0x82 = 0x82
    PLAY_MPG_VIDEO = 0x8A
    UNK_0x8B = 0x8B
    UNK_0x8C = 0x8C
    UNK_0x8D = 0x8D
    UNK_0x8E = 0x8E
    UNK_0x93 = 0x93
    UNK_0x95 = 0x95
    UNK_0x96 = 0x96
    UNK_0x98 = 0x98
    UNK_0xA8 = 0xA8
    UNK_0xA9 = 0xA9
    UNK_0xAC = 0xAC
    UNK_0xB4 = 0xB4
    UNK_0xC6 = 0xC6
    UNK_0xCA = 0xCA
    UNK_0xD6 = 0xD6
    GET_CHOICE_HINTS = 0xD7
    UNK_0xD8 = 0xD8
    UNK_0xE2 = 0xE2
    UNK_0xF0 = 0xF0
    UNK_0xF1 = 0xF1
    UNK_0xFC = 0xFC
    UNK_0xFF = 0xFF


class NormalOpcodeDisassemblerException(Exception):
    """Custom exception for disassembler errors."""
    pass


class NameCache:
    """Manages name caching with better encapsulation."""

    def __init__(self, debug: bool = True):
        self.cache: Dict[int, str] = {}
        self.last_saved_name = ""
        self.last_saved_name_offset: Optional[int] = None
        self.debug = debug
    
    def get_name(self, offset: int) -> Optional[str]:
        """Get cached name by offset."""
        return self.cache.get(offset)
    
    def cache_name(self, offset: int, name: str) -> None:
        """Cache a name at given offset."""
        if self._is_japanese_name_bracket(name):
            self.cache[offset] = name
            self.last_saved_name = name
            self.last_saved_name_offset = offset
            if self.debug:
                print(f"  -> CACHED NAME: '{name}' at START offset {offset}")
    
    def get_last_saved_name(self) -> tuple[str, Optional[int]]:
        """Get the last saved name and its offset."""
        return self.last_saved_name, self.last_saved_name_offset
    
    @staticmethod
    def _is_japanese_name_bracket(text: str) -> bool:
        """Check if text is enclosed in Japanese brackets 【】"""
        return text.startswith('【') and text.endswith('】')


class VMExecutor:
    """Handles VM execution with consistent patterns."""
    
    @staticmethod
    def execute_single() -> int:
        """Execute VM code once and return result."""
        return vm.execute_vm_code()
    
    @staticmethod
    def execute_multiple(count: int) -> list[int]:
        """Execute VM code multiple times and return all results."""
        return [vm.execute_vm_code() for _ in range(count)]


class NormalOpcodeDisassembler:
    """Fixed NormalOpcodeDisassembler that processes one opcode at a time."""
    
    def __init__(self, debug: bool = True):
        """Initialize the disassembler."""
        self.debug = debug  # Fixed: Added missing debug attribute
        self.name_cache = NameCache(debug)
        
        # Build opcode handler mapping for O(1) lookup
        self.opcode_handlers: Dict[int, Callable[[int], None]] = self._build_opcode_handlers()
    
    def _build_opcode_handlers(self) -> Dict[int, Callable[[int], None]]:
        """Build mapping of opcodes to their handler functions."""
        handlers = {
            Opcode.STRING_TYPE_0: self._handle_string_opcode,
            Opcode.STRING_TYPE_1: self._handle_string_opcode,
            Opcode.NEWLINE: self._handle_newline,
            Opcode.UNK_0x02: lambda offset: self._handle_simple_vm_execution(offset, "0x02"),
            Opcode.UNK_0x05: lambda offset: self._handle_simple_execution(offset, "0x05"),
            Opcode.UNK_0x09: self._handle_unk_0x09,
            Opcode.UNK_0x0A: lambda offset: self._handle_double_vm_execution(offset, "0x0A"),
            Opcode.UNK_0x0B: lambda offset: self._handle_simple_execution(offset, "0x0B"),
            Opcode.UNK_0x10: lambda offset: self._handle_simple_vm_execution(offset, "0x10"),
            Opcode.UNK_0x12: lambda offset: self._handle_simple_vm_execution(offset, "0x12"),
            Opcode.UNK_0x13: lambda offset: self._handle_simple_execution(offset, "0x13"),
            Opcode.SHOW_IMAGES: self._handle_show_images,
            Opcode.UNK_0x17: lambda offset: self._handle_simple_vm_execution(offset, "0x17"),
            Opcode.UNK_0x18: lambda offset: self._handle_simple_vm_execution(offset, "0x18"),
            Opcode.SHOW_STANDSTILLS: self._handle_show_standstills,
            Opcode.UNK_0x1F: lambda offset: self._handle_double_vm_execution(offset, "0x1F"),
            Opcode.UNK_0x28: lambda offset: self._handle_double_vm_execution(offset, "0x28"),
            Opcode.UNK_0x30: lambda offset: self._handle_double_vm_execution(offset, "0x30"),
            Opcode.UNK_0x32: lambda offset: self._handle_simple_vm_execution(offset, "0x32"),
            Opcode.UNK_0x33: lambda offset: self._handle_simple_vm_execution(offset, "0x33"),
            Opcode.UNK_0x34: lambda offset: self._handle_simple_vm_execution(offset, "0x34"),
            Opcode.UNK_0x35: lambda offset: self._handle_simple_vm_execution(offset, "0x35"),
            Opcode.UNK_0x38: lambda offset: self._handle_double_vm_execution(offset, "0x38"),
            Opcode.UNK_0x3A: lambda offset: self._handle_double_vm_execution(offset, "0x3A"),
            Opcode.UNK_0x3D: lambda offset: self._handle_simple_vm_execution(offset, "0x3D"),
            Opcode.UNK_0x61: lambda offset: self._handle_simple_vm_execution(offset, "0x61"),
            Opcode.UNK_0x41: lambda offset: self._handle_simple_vm_execution(offset, "0x41"),
            Opcode.UNK_0x4F: lambda offset: self._handle_simple_vm_execution(offset, "0x4F"),
            Opcode.UNK_0x71: lambda offset: self._handle_simple_vm_execution(offset, "0x71"),
            Opcode.UNK_0x72: lambda offset: self._handle_simple_vm_execution(offset, "0x72"),
            Opcode.UNK_0x79: lambda offset: self._handle_simple_vm_execution(offset, "0x79"),
            Opcode.UNK_0xA2: lambda offset: self._handle_simple_vm_execution(offset, "0xA2"),
            Opcode.UNK_0xA6: self._handle_unk_0xA6,
            Opcode.UNK_0xA8: lambda offset: self._handle_simple_execution(offset, "0xA8"),
            Opcode.UNK_0xAD: lambda offset: self._handle_simple_vm_execution(offset, "0xAD"),
            Opcode.UNK_0xB3: lambda offset: self._handle_simple_vm_execution(offset, "0xB3"),
            Opcode.UNK_0xB4: self._handle_unk_0xB4,
            Opcode.UNK_0xE3: lambda offset: self._handle_simple_vm_execution(offset, "0xE3"),
            Opcode.UNK_0xEE: lambda offset: self._handle_simple_vm_execution(offset, "0xEE"),
            Opcode.UNK_0xF2: lambda offset: self._handle_simple_vm_execution(offset, "0xF2"),
            Opcode.UNK_0xF6: lambda offset: self._handle_simple_vm_execution(offset, "0xF6"),
            Opcode.UNK_0xF7: lambda offset: self._handle_simple_vm_execution(offset, "0xF7"),
            Opcode.UNK_0xF8: lambda offset: self._handle_simple_vm_execution(offset, "0xF8"),
            Opcode.PLAY_WAV: lambda offset: self._handle_double_vm_execution(offset, "PLAY_WAV"),
            Opcode.UNK_0x45: lambda offset: self._handle_simple_vm_execution(offset, "0x45"),
            Opcode.UNK_0x46: self._handle_unk_0x46,
            Opcode.UNK_0x47: lambda offset: self._handle_simple_vm_execution(offset, "0x47"),
            Opcode.PLAY_VOICELINES: lambda offset: self._handle_double_vm_execution(offset, "PLAY_VOICELINES"),
            Opcode.UNK_0x4E: lambda offset: self._handle_simple_vm_execution(offset, "0x4E"),
            Opcode.UNK_0x58: lambda offset: self._handle_simple_vm_execution(offset, "0x58"),
            Opcode.UNK_0x5B: lambda offset: self._handle_simple_vm_execution(offset, "0x5B"),
            Opcode.UNK_0x5D: lambda offset: self._handle_simple_vm_execution(offset, "0x5D"),
            Opcode.UNK_0x5E: lambda offset: self._handle_simple_vm_execution(offset, "0x5E"),
            Opcode.UNK_0x60: lambda offset: self._handle_double_vm_execution(offset, "0x60"),
            Opcode.UNK_0x66: lambda offset: self._handle_double_vm_execution(offset, "0x66"),
            Opcode.UNK_0x6C: self._handle_unk_0x6C,
            Opcode.SCENARIO_VM: self._handle_scenario_vm,
            Opcode.UNK_0x76: lambda offset: self._handle_simple_execution(offset, "0x76"),
            Opcode.UNK_0x7A: lambda offset: self._handle_double_vm_execution(offset, "0x7A"),
            Opcode.SET_DELAY: lambda offset: self._handle_simple_vm_execution(offset, "SET_DELAY"),
            Opcode.UNK_0x82: lambda offset: self._handle_simple_vm_execution(offset, "0x82"),
            Opcode.PLAY_MPG_VIDEO: self._handle_play_mpg_video,
            Opcode.UNK_0x8B: lambda offset: self._handle_simple_vm_execution(offset, "0x8B"),  # Fixed: Added missing opcode
            Opcode.UNK_0x8C: lambda offset: self._handle_simple_vm_execution(offset, "0x8C"),  # Fixed: Added missing opcode
            Opcode.UNK_0x8D: lambda offset: self._handle_simple_vm_execution(offset, "0x8D"),
            Opcode.UNK_0x8E: lambda offset: self._handle_simple_vm_execution(offset, "0x8E"),  # Fixed: Added missing opcode
            Opcode.UNK_0x93: lambda offset: self._handle_simple_execution(offset, "0x93"),
            Opcode.UNK_0x95: lambda offset: self._handle_double_vm_execution(offset, "0x95"),
            Opcode.UNK_0x96: lambda offset: self._handle_simple_vm_execution(offset, "0x96"),
            Opcode.UNK_0x98: lambda offset: self._handle_double_vm_execution(offset, "0x98"),
            Opcode.UNK_0xA9: lambda offset: self._handle_simple_vm_execution(offset, "0xA9"),
            Opcode.UNK_0xAC: self._handle_unk_0xAC,
            Opcode.UNK_0xB3: lambda offset: self._handle_simple_execution(offset, "0xB3"),
            Opcode.UNK_0xC6: lambda offset: self._handle_double_vm_execution(offset, "0xC6"),
            Opcode.UNK_0xCA: lambda offset: self._handle_simple_execution(offset, "0xCA"),
            Opcode.UNK_0xD6: lambda offset: self._handle_simple_vm_execution(offset, "0xD6"),
            Opcode.GET_CHOICE_HINTS: self._handle_get_choice_hints,
            Opcode.UNK_0xD8: lambda offset: self._handle_simple_execution(offset, "0xD8"),
            Opcode.UNK_0xE2: lambda offset: self._handle_simple_execution(offset, "0xE2"),
            Opcode.UNK_0xF0: lambda offset: self._handle_simple_vm_execution(offset, "0xF0"),
            Opcode.UNK_0xF1: self._handle_unk_0xF1,
            Opcode.UNK_0xFC: lambda offset: self._handle_simple_vm_execution(offset, "0xFC"),
            Opcode.UNK_0xFF: lambda offset: self._handle_simple_execution(offset, "0xFF"),
        }
        return handlers
    
    def process_single_command(self) -> int:
        """Process a single command and return status code. Fixed: New method for single command processing."""
        try:
            if GlobalBuffer.command_data_offset >= len(GlobalBuffer.command_data):
                return -1  # End of data
            
            current_offset = GlobalBuffer.command_data_offset
            
            opcode = read_next_opcode()
            if opcode is None:
                if self.debug:
                    print("[ERROR] Tried to dispatch a None opcode")
                return -1
            
            if self.debug:
                print(f"[Normal] At offset {current_offset}: Opcode {opcode} (0x{opcode:02X})")
            
            # Use handler mapping for O(1) lookup
            handler = self.opcode_handlers.get(opcode)
            if handler:
                handler(current_offset)
                return 0  # Success
            else:
                self._handle_unknown_opcode(opcode, current_offset)
                return -1  # Error
                
        except Exception as e:
            if self.debug:
                print(f"Error processing single command: {e}")
            return -1
    
    def process_all_commands(self) -> None:
        """Process all VM commands in the data. Fixed: Renamed from _process_commands for clarity."""
        try:
            while GlobalBuffer.command_data_offset < len(GlobalBuffer.command_data):
                result = self.process_single_command()
                if result == -1:
                    break
                    
        except Exception as e:
            if self.debug:
                print(f"Error processing all commands: {e}")
            raise NormalOpcodeDisassemblerException(f"Error processing commands: {e}")
    
    # Optimized handler methods - grouped by similar behavior
    def _handle_simple_execution(self, current_offset: int, opcode_name: str) -> None:
        """Handle opcodes that only need conditional increment."""
        if self.debug:
            print(f"[Normal] Executing opcode {opcode_name} at offset {current_offset}")
    
    def _handle_simple_vm_execution(self, current_offset: int, opcode_name: str) -> None:
        """Handle opcodes that execute VM once then increment."""
        result = VMExecutor.execute_single()
        if self.debug:
            print(f"[Normal] Executing opcode {opcode_name} at offset {current_offset}")
            print(f"VM Execution Result: {result}")

    def _handle_double_vm_execution(self, current_offset: int, opcode_name: str) -> None:
        """Handle opcodes that execute VM twice then increment."""
        results = VMExecutor.execute_multiple(2)
        if self.debug:
            print(f"[Normal] Executing opcode {opcode_name} at offset {current_offset}")
            print(f"VM Execution Results: {results}")
    
    def _handle_string_opcode(self, current_offset: int) -> None:
        """Handle string opcodes (0 and 1) - optimized version."""
        opcode = GlobalBuffer.command_data[current_offset]
        v252 = 1 if opcode == Opcode.STRING_TYPE_0 else 0
        text_offset = get_next_word()
        get_string_flag = 1 if v252 == 0 else 0
        
        #This is not actually an error but it's due to the fact there is some unused command data at the end so we use this as a safe guard for now.
        if text_offset is None:
            print(f"[ERROR] Unexpected EOF while reading string offset at {current_offset}, max Offset = {len(GlobalBuffer.command_data)}")
            return 
        
        if text_offset < len(GlobalBuffer.text_data):
            length, string = read_C_string(GlobalBuffer.text_data, text_offset)
            
            if length == 0 and get_string_flag == 1:
                # Try to get cached name
                cached_name = self.name_cache.get_name(text_offset)
                if cached_name:
                    actual_string = cached_name
                    cache_info = f"CACHED FROM OFFSET {text_offset}: '{actual_string}'"
                else:
                    last_name, last_offset = self.name_cache.get_last_saved_name()
                    if last_name:
                        actual_string = last_name
                        cache_info = f"CACHED LAST: '{actual_string}' from offset {last_offset}"
                    else:
                        actual_string = ""
                        cache_info = "NO CACHE AVAILABLE"
                
                if self.debug:
                    print(f"  -> Text Offset: {text_offset}, v252: {v252}, "
                          f"get_string_flag: {get_string_flag}, Length: {length}, "
                          f"String = '' [{cache_info}]")
            else:
                actual_string = string
                if self.debug:
                    print(f"  -> Text Offset: {text_offset}, v252: {v252}, "
                          f"get_string_flag: {get_string_flag}, Length: {length}, String = '{string}'")
                
                # Cache if Japanese name bracket
                self.name_cache.cache_name(text_offset, string)
        else:
            if self.debug:
                print(f"  -> Invalid text offset {text_offset} (max: {len(GlobalBuffer.text_data)})")
    
    def _handle_newline(self, current_offset: int) -> None:
        """Handle newline opcode."""
        if self.debug:
            print(f"  -> Newline encountered at offset {current_offset}")
    
    def _handle_play_mpg_video(self, current_offset: int) -> None:
        """Handle Play MPG video execution."""
        video_name_string_offset = get_next_word()
        video_name_length, video_name_string = read_C_string(GlobalBuffer.text_data, video_name_string_offset)
        if self.debug:
            print(f"Playing MPG video: '{video_name_string}.mpg' at offset {current_offset}")
    
    def _handle_scenario_vm(self, current_offset: int) -> None:
        """Handle scenario String."""
        scenario_txt_start_offset = get_next_word()
        length, scenario_string = read_C_string(GlobalBuffer.text_data, scenario_txt_start_offset)
        
        if length == 0:
            if self.debug:
                print(f"  -> Scenario string at offset {current_offset} with empty string")
        else:
            if self.debug:
                print(f"  -> Scenario string at offset {current_offset} with string: '{scenario_string}'")
        
        result = VMExecutor.execute_single()
        if self.debug:
            print(f"VM Execution Result: {result}")
            print(f"Scenario Text Start Offset: {scenario_txt_start_offset}")
    
    def _handle_get_choice_hints(self, current_offset: int) -> None:
        """Handle get choice hints opcode."""
        text_offset = get_next_word()
        length, hint_string = read_C_string(GlobalBuffer.text_data, text_offset)
        if self.debug:
            print(f"[Normal] Executing OPCODE_GET_CHOICE_HINTS at offset {current_offset}")
            print(f"Hint string: '{hint_string}'")
    
    # Specialized handlers for complex opcodes
    def _handle_unk_0x09(self, current_offset: int) -> None:
        """Handle unknown opcode 0x09 - 4 VM executions + text offset."""
        results = VMExecutor.execute_multiple(4)
        scn_txt_offset = get_next_word()
        length, string = read_C_string(GlobalBuffer.text_data, scn_txt_offset)
        if self.debug:
            print(f"[Normal] Executing opcode 0x09 at offset {current_offset}")
            print(f"VM Execution Results: {results}")
            print(f"Scenario Text Length: {length}, Text: '{string}'")
    
    def _handle_show_images(self, current_offset: int) -> None:
        """Handle unknown opcode 0x15 - image related."""
        image_no = VMExecutor.execute_single()
        if self.debug:
            print(f"[Normal] Executing show image at offset {current_offset}")
            print(f"Image No: {image_no}")
    
    def _handle_show_standstills(self, current_offset: int) -> None:
        """Handle show standstills opcode."""
        results = VMExecutor.execute_multiple(3)
        if self.debug:
            print(f"[Normal] Executing OPCODE_SHOW_STANDSTILLS 0x1E at offset {current_offset}")
            print(f"VM Execution Results: {results}")
    
    def _handle_unk_0x46(self, current_offset: int) -> None:
        """Handle unknown opcode 0x46 - triple VM execution."""
        results = VMExecutor.execute_multiple(3)
        if self.debug:
            print(f"[Normal] Executing opcode 0x46 at offset {current_offset}")
            print(f"VM Execution Results: {results}")
    
    def _handle_unk_0xAC(self, current_offset: int) -> None:
        """Handle unknown opcode 0xAC - quadruple VM execution."""
        results = VMExecutor.execute_multiple(4)
        if self.debug:
            print(f"[Normal] Executing opcode 0xAC at offset {current_offset}")
            print(f"VM Execution Results: {results}")

    def _handle_unk_0xA6(self, current_offset: int) -> None:
        """Handle unknown opcode 0xA6."""
        if self.debug:
            print(f"[Normal] Executing opcode 0xA6 at offset {current_offset}")

    def _handle_unk_0xB4(self, current_offset: int) -> None:
        """Handle unknown opcode 0xB4 - 3 VM executions."""
        results = VMExecutor.execute_multiple(9)
        if self.debug:
            print(f"[Normal] Executing opcode 0xB4 at offset {current_offset}")
            print(f"VM Execution Results: {results}")

    def _handle_unk_0x6C(self, current_offset: int) -> None:
        """Handle unknown opcode 0x6C - 5 VM executions."""
        results = VMExecutor.execute_multiple(4)
        string_offset = get_next_word()
        length, string = read_C_string(GlobalBuffer.text_data, string_offset)
        if self.debug:
            print(f"[Normal] Executing opcode 0x6C at offset {current_offset}")
            print(f"VM Execution Results: {results}")
            print(f"String: '{string}'")
    
    def _handle_unk_0xF1(self, current_offset: int) -> None:
        """Handle unknown opcode 0xF1 - 10 VM executions."""
        results = VMExecutor.execute_multiple(10)
        if self.debug:
            print(f"[Normal] Executing opcode 0xF1 at offset {current_offset}")
            print(f"VM Execution Results: {results}")
    
    def _handle_unknown_opcode(self, opcode: int, current_offset: int) -> None:
        """Handle unknown opcodes."""
        if self.debug:
            print(f"Unknown opcode: {opcode} (0x{opcode:02X}) at offset {current_offset}")
        # Don't exit - let caller handle the error
        raise NormalOpcodeDisassemblerException(f"Unknown opcode: {opcode} (0x{opcode:02X}) at offset {current_offset}")
