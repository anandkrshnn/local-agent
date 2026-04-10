"""System-related tools: safe commands"""

import subprocess

class SystemTools:
    def __init__(self, agent):
        self.agent = agent
    
    def run_command_safe(self, command: str, token: str) -> str:
        """Run a whitelisted shell command"""
        if not self.agent.broker.validate_and_consume(token, "run_command", command.split()[0]):
            return "Permission denied"
        
        # Whitelist of safe commands
        safe_commands = ['ls', 'dir', 'echo', 'cat', 'type', 'pwd', 'whoami', 'date', 'time']
        base_cmd = command.split()[0].lower()
        
        if base_cmd not in safe_commands:
            return f"❌ Blocked: Command '{base_cmd}' is not in the whitelist of safe commands."
            
        try:
            # On Windows, 'ls' might fail, so we mapping it to 'dir'
            if os.name == 'nt' and base_cmd == 'ls':
                command = command.replace('ls', 'dir')
                
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            output = result.stdout if result.stdout else result.stderr
            
            # Store in memory
            self.agent.memory.store("run_command", {"command": command, "exit_code": result.returncode})
            
            return output[:2000]
        except Exception as e:
            return f"❌ Command failed: {e}"
