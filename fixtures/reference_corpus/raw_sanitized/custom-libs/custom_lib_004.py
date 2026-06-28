import paramiko
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import logging
from typing import List, Dict, Any, Optional
import os
import re
from typing import Union, List
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER



class SOURCE_NAME_PLACEHOLDER:
    def __init__(self,CMG_params: Dict[str, str]):
        
        
        required_parms =['CMG_SMF_IP', 'CMG_UPF_IP', 'PASSWORD', 'USERNAME', 'KEYPATH'] 
        
        for param in required_parms:
            if param not in CMG_params:
                raise ValueError (f"Missing required parameter:{param}")

        self.cmg_ips =[ip for cmgname , ip in CMG_params.items() if "IP" in cmgname]
        HOSTNAME_PLACEHOLDER = [HOSTNAME_PLACEHOLDER("_IP", "") for cmgame in CMG_params if "IP" in cmgame]
        self.cmg_password = VALUE_PLACEHOLDER 
        self.cmg_username = CMG_params['USERNAME'] 
        self.cmg_keypath = CMG_params['KEYPATH'] 
        self.is_connected = False
        
    def login_cmg(self, testcasedir, filter=None) -> bool:
        self.connected_cmgs = []  # Store all successful connections
        successful_connections = 0
        
        # Determine which CMGs to connect to
        if filter:
            if not self.cmg_ips or not HOSTNAME_PLACEHOLDER:
                HOSTNAME_PLACEHOLDER("No CMG IPs or names available")
                return False
            
            # Debug logging to see what names are available
            HOSTNAME_PLACEHOLDER(f"Filtering for: {filter}")
                
            filtered_data = [(ip, name) for ip, name in zip(self.cmg_ips, HOSTNAME_PLACEHOLDER)
                 if HOSTNAME_PLACEHOLDER() in HOSTNAME_PLACEHOLDER().split('_')]
            
            # Debug logging to see what was filtered
            HOSTNAME_PLACEHOLDER(f"Target CMG server : {filtered_data}")
            
            if not filtered_data:
                HOSTNAME_PLACEHOLDER(f"No CMGs with filter : {filter}  in name found")
                return False
            
            # Connect to ALL matching nodes, not just the first one
            cmg_pairs = filtered_data
        else:
            
              cmg_pairs = [ (self.cmg_ips[0], HOSTNAME_PLACEHOLDER[0]) ]
        
        # Try to connect to each selected CMG
        for ip, cmgname in cmg_pairs:
            try:   
                cmg_node = SOURCE_NAME_PLACEHOLDER(
                    "cmg", self.cmg_username, ip, testcasedir + "/HOSTNAME_PLACEHOLDER"
                )
                
                cmg_node.logintoNode_password(self.cmg_keypath, self.cmg_password)
                
                # Add successful connection to the list
                self.connected_cmgs.append({'node': cmg_node, 'name': cmgname, 'ip': ip})
                successful_connections += 1
                HOSTNAME_PLACEHOLDER(f"Successfully logged into CMG node: {cmgname} :{ip}")
                
            except ConnectionError:
                HOSTNAME_PLACEHOLDER(f"Failed to connect to CMG node {cmgname}: Connection Error")
                
            except TimeoutError:
                HOSTNAME_PLACEHOLDER(f"Connection to CMG node {cmgname} timed out")
                
            except OSError as e:
                HOSTNAME_PLACEHOLDER(f"Network error connecting to CMG node {cmgname}: {e}")
                
            except FileNotFoundError:
                HOSTNAME_PLACEHOLDER(f"Key file not found for CMG node {cmgname}: {self.cmg_keypath}")
                
            except PermissionError:
                HOSTNAME_PLACEHOLDER(f"Permission denied accessing key file for CMG node {cmgname}")
                
            except ValueError as e:
                HOSTNAME_PLACEHOLDER(f"Invalid configuration for CMG node {cmgname}: {e}")
                
            except AttributeError as e:
                HOSTNAME_PLACEHOLDER(f"Missing required attribute for CMG node {cmgname}: {e}")
                
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Unexpected error during CMG login to {cmgname}: {e}")
        
        # Set connection status based on results
        if successful_connections > 0:
            self.is_connected = True
            # Set primary CMG to the first successful connection for backward compatibility
            HOSTNAME_PLACEHOLDER = self.connected_cmgs[0]['node']
            HOSTNAME_PLACEHOLDER(f"Successfully connected to {successful_connections} CMG nodes")
            return True
        else:
            self.is_connected = False
            HOSTNAME_PLACEHOLDER("Failed to connect to any CMG node")
            return False
         
    def executeCommand(self, commands: List[str], testcasedir: str, filter= None ,  prompt: str = r"[AB]:.*?#\s*") -> str:
    
        results = {
            'total_commands': len(commands),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        # Login to all available CMG nodes
        self.connected_cmgs = []  # Clear old list
        if not self.login_cmg(testcasedir, filter):
            HOSTNAME_PLACEHOLDER("Failed to connect to any CMG nodes")
            return None  # Return None instead of False to match str return type
        
        # Execute each command on all connected nodes
        for command in commands:
            command_success = True
            
            for cmg_info in self.connected_cmgs:
                cmg_name = cmg_info['name']
                cmg_ip = cmg_info['ip']
                cmg_node = cmg_info['node']
                
                try:
                    # Use a more specific prompt pattern that matches the actual prompts
            
                    result = cmg_node.executeCommandsOnNodes(prompt, command)
                    HOSTNAME_PLACEHOLDER(f"Command: '{command}' executed successfully on {cmg_name} ({cmg_ip})")
                    
                    results['details'].append({    
                        'command': command,
                        'node': cmg_name,
                        'ip': cmg_ip,
                        'status': 'success',
                        'output': result
                    })
                    
                except ConnectionError:
                    HOSTNAME_PLACEHOLDER(f"Connection lost while executing command '{command}' on {cmg_name} ({cmg_ip})")
                    command_success = False
                    results['details'].append({
                        'command': command,
                        'node': cmg_name,
                        'ip': cmg_ip,
                        'status': 'failed',
                        'error': 'Connection lost'
                    })
                    
                except TimeoutError:
                    HOSTNAME_PLACEHOLDER(f"Command '{command}' timed out on {cmg_name} ({cmg_ip})")
                    command_success = False
                    results['details'].append({
                        'command': command,
                        'node': cmg_name,
                        'ip': cmg_ip,
                        'status': 'failed',
                        'error': 'Command timed out'
                    })
                    
                except PermissionError:
                    HOSTNAME_PLACEHOLDER(f"Permission denied executing command '{command}' on {cmg_name} ({cmg_ip})")
                    command_success = False
                    results['details'].append({
                        'command': command,
                        'node': cmg_name,
                        'ip': cmg_ip,
                        'status': 'failed',
                        'error': 'Permission denied'
                    })
                    
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"Failed to execute command '{command}' on {cmg_name} ({cmg_ip}): {str(e)}")
                    command_success = False
                    results['details'].append({
                        'command': command,
                        'node': cmg_name,
                        'ip': cmg_ip,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Update overall results for this command
            if command_success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                # Optionally return False here if you want to stop on any command failure
                # return False
        
        HOSTNAME_PLACEHOLDER(f"Command execution complete. Success: {results['successful']}, Failed: {results['failed']}")
        return testcasedir + "/HOSTNAME_PLACEHOLDER"
    
    def executeOneCommand(self, command: str, testcasedir: str, filter= None ,  prompt: str = r"[AB]:.*?#\s*") -> str:
    
        results = {
            'total_commands': len(command),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        # Login to all available CMG nodes
        self.connected_cmgs = []  # Clear old list
        if not self.login_cmg(testcasedir, filter):
            HOSTNAME_PLACEHOLDER("Failed to connect to any CMG nodes")
            return None  # Return None instead of False to match str return type
        
        # Execute each command on all connected nodes

        command_success = True
        
        for cmg_info in self.connected_cmgs:
            cmg_name = cmg_info['name']
            cmg_ip = cmg_info['ip']
            cmg_node = cmg_info['node']
            
            try:
                # Use a more specific prompt pattern that matches the actual prompts
                result = cmg_node.executeCommandsOnNodes(prompt, command)
                HOSTNAME_PLACEHOLDER(f"Command: '{command}' executed successfully on {cmg_name} ({cmg_ip})")
                
                results['details'].append({    
                    'command': command,
                    'node': cmg_name,
                    'ip': cmg_ip,
                    'status': 'success',
                    'output': result
                })
                
            except ConnectionError:
                HOSTNAME_PLACEHOLDER(f"Connection lost while executing command '{command}' on {cmg_name} ({cmg_ip})")
                command_success = False
                results['details'].append({
                    'command': command,
                    'node': cmg_name,
                    'ip': cmg_ip,
                    'status': 'failed',
                    'error': 'Connection lost'
                })
                
            except TimeoutError:
                HOSTNAME_PLACEHOLDER(f"Command '{command}' timed out on {cmg_name} ({cmg_ip})")
                command_success = False
                results['details'].append({
                    'command': command,
                    'node': cmg_name,
                    'ip': cmg_ip,
                    'status': 'failed',
                    'error': 'Command timed out'
                })
                
            except PermissionError:
                HOSTNAME_PLACEHOLDER(f"Permission denied executing command '{command}' on {cmg_name} ({cmg_ip})")
                command_success = False
                results['details'].append({
                    'command': command,
                    'node': cmg_name,
                    'ip': cmg_ip,
                    'status': 'failed',
                    'error': 'Permission denied'
                })
                
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Failed to execute command '{command}' on {cmg_name} ({cmg_ip}): {str(e)}")
                command_success = False
                results['details'].append({
                    'command': command,
                    'node': cmg_name,
                    'ip': cmg_ip,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Update overall results for this command
        if command_success:
            results['successful'] += 1
        else:
            results['failed'] += 1
            # Optionally return False here if you want to stop on any command failure
            # return False
        
        HOSTNAME_PLACEHOLDER(f"Command execution complete. Success: {results['successful']}, Failed: {results['failed']}")
        return testcasedir + "/HOSTNAME_PLACEHOLDER"

    def fetch_config_file(self, tc_dir: str, config_path_list: list, filter=None,
                          partial_success=False) -> dict:
        """
        Fetch configuration files from CMG servers via SFTP.

        Args:
            tc_dir: Local directory to store downloaded files
            config_path_list: List of remote file paths to download
            filter: Optional filter to select specific CMG servers
            partial_success: If True, consider partial downloads as success

        Returns:
            dict: Contains 'success' (bool), 'results' (dict), 'summary' (dict)
        """
        # Validate input parameters
        if not tc_dir:
            HOSTNAME_PLACEHOLDER("tc_dir cannot be empty")
            return {'success': False, 'error': 'Invalid tc_dir', 'results': {}}

        if not config_path_list or not isinstance(config_path_list, list):
            HOSTNAME_PLACEHOLDER("config_path_list must be a non-empty list")
            return {'success': False, 'error': 'Invalid config_path_list', 'results': {}}

        # Ensure tc_dir exists, create if it doesn't
        try:
            os.makedirs(tc_dir, exist_ok=True)
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to create directory {tc_dir}: {e}")
            return {'success': False, 'error': f'Directory creation failed: {e}', 'results': {}}

        # Determine target CMG servers
        if filter:
            if not self.cmg_ips or not HOSTNAME_PLACEHOLDER:
                HOSTNAME_PLACEHOLDER("No CMG IPs or names available")
                return {'success': False, 'error': 'No CMG data available', 'results': {}}

            HOSTNAME_PLACEHOLDER(f"Filtering for: {filter}")
            
            filtered_data = [(ip, name) for ip, name in zip(self.cmg_ips, HOSTNAME_PLACEHOLDER)
                 if HOSTNAME_PLACEHOLDER() in HOSTNAME_PLACEHOLDER().split('_')]
            
            HOSTNAME_PLACEHOLDER(f"Target CMG server : {filtered_data}")

            if not filtered_data:
                HOSTNAME_PLACEHOLDER(f"No CMGs with filter '{filter}' in name found")
                return {'success': False, 'error': f'No CMGs found with filter: {filter}', 'results': {}}

            cmg_pairs = filtered_data
        else:
            if not self.cmg_ips or not HOSTNAME_PLACEHOLDER:
                HOSTNAME_PLACEHOLDER("No CMG IPs or names available")
                return {'success': False, 'error': 'No CMG data available', 'results': {}}
            cmg_pairs = [(self.cmg_ips[0], HOSTNAME_PLACEHOLDER[0])]

        # Track results for each file
        results = {}
        ssh = None
        sftp = None

        try:
            ssh = HOSTNAME_PLACEHOLDER()
            ssh.set_missing_host_key_policy(HOSTNAME_PLACEHOLDER())

            # Connect to the first matching CMG
            target_ip, target_name = cmg_pairs[0]
            HOSTNAME_PLACEHOLDER(f"Connecting to {target_name} ({target_ip})")

            HOSTNAME_PLACEHOLDER(target_ip, username=self.cmg_username, password=self.cmg_password)
            sftp = ssh.open_sftp()

            # Process each config file
            for i, config_path in enumerate(config_path_list, 1):
                config_path = config_path.strip()
                HOSTNAME_PLACEHOLDER(f"Processing file {i}/{len(config_path_list)}: {config_path}")

                # Construct local file path
                local_filename = os.HOSTNAME_PLACEHOLDER(config_path)
                local_path = os.HOSTNAME_PLACEHOLDER(tc_dir, local_filename)

                # Log the exact paths being used
                HOSTNAME_PLACEHOLDER(f"Remote path: '{config_path}'")
                HOSTNAME_PLACEHOLDER(f"Local path: '{local_path}'")

                try:
                    # Check if remote file exists
                    try:
                        remote_stat = HOSTNAME_PLACEHOLDER(config_path)
                        HOSTNAME_PLACEHOLDER(f"Valid config path {config_path}")
                        HOSTNAME_PLACEHOLDER(f"Remote file size: {remote_stat.st_size} bytes")
                    except FileNotFoundError:
                        HOSTNAME_PLACEHOLDER(f"Remote file not found: {config_path}")
                        results[config_path] = {
                            'success': False,
                            'error': 'File not found on remote server',
                            'local_path': local_path
                        }
                        continue

                    # Perform the file transfer
                    HOSTNAME_PLACEHOLDER(config_path, local_path)

                    # Verify the file was downloaded successfully
                    if os.HOSTNAME_PLACEHOLDER(local_path):
                        file_size = os.HOSTNAME_PLACEHOLDER(local_path)
                        HOSTNAME_PLACEHOLDER(f"Config file fetched successfully (size: {file_size} bytes)")
                        results[config_path] = {
                            'success': True,
                            'local_path': local_path,
                            'size': file_size
                        }
                    else:
                        HOSTNAME_PLACEHOLDER(f"File transfer completed but local file not found: {local_path}")
                        results[config_path] = {
                            'success': False,
                            'error': 'Local file not found after transfer',
                            'local_path': local_path
                        }

                except PermissionError as e:
                    HOSTNAME_PLACEHOLDER(f"Permission denied when writing to {local_path}: {e}")
                    results[config_path] = {
                        'success': False,
                        'error': f'Permission denied: {e}',
                        'local_path': local_path
                    }
                except IOError as e:
                    HOSTNAME_PLACEHOLDER(f"I/O error during file transfer for {config_path}: {e}")
                    results[config_path] = {
                        'success': False,
                        'error': f'I/O error: {e}',
                        'local_path': local_path
                    }
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"Unexpected error processing {config_path}: {e}")
                    results[config_path] = {
                        'success': False,
                        'error': f'Unexpected error: {e}',
                        'local_path': local_path
                    }

            # Generate summary
            successful_files = [path for path, result in HOSTNAME_PLACEHOLDER() if result['success']]
            failed_files = [path for path, result in HOSTNAME_PLACEHOLDER() if not result['success']]

            summary = {
                'total_files': len(config_path_list),
                'successful': len(successful_files),
                'failed': len(failed_files),
                'successful_files': successful_files,
                'failed_files': failed_files
            }

            HOSTNAME_PLACEHOLDER(f"Transfer summary: {summary['successful']} successful, {summary['failed']} failed")
            if successful_files:
                HOSTNAME_PLACEHOLDER(f"Successful files: {successful_files}")
            if failed_files:
                HOSTNAME_PLACEHOLDER(f"Failed files: {failed_files}")

            # Determine overall success
            if partial_success:
                overall_success = summary['successful'] > 0
            else:
                overall_success = summary['failed'] == 0

            return {
                'success': overall_success,
                'results': results,
                'summary': summary,
                'target_server': f"{target_name} ({target_ip})"
            }

        except HOSTNAME_PLACEHOLDER:
            HOSTNAME_PLACEHOLDER("Authentication failed, please check username/password")
            return {'success': False, 'error': 'Authentication failed', 'results': results}
        except HOSTNAME_PLACEHOLDER as e:
            HOSTNAME_PLACEHOLDER(f"SSH connection error: {e}")
            return {'success': False, 'error': f'SSH connection error: {e}', 'results': results}
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Unexpected connection error: {e}")
            return {'success': False, 'error': f'Unexpected connection error: {e}', 'results': results}
        finally:
            # Ensure cleanup
            if sftp:
                try:
                    HOSTNAME_PLACEHOLDER()
                except:
                    pass
            if ssh:
                try:
                    HOSTNAME_PLACEHOLDER()
                except:
                    pass
    def fetch_VPRN_service_id(self, sshlogs: str)-> List:
        
        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False
        try: 
            HOSTNAME_PLACEHOLDER(f"Searching for VPRN Service IDs ")
            pattern = r"(\d+)\s+VPRN"  
            matches = re.findall(pattern, content, re.MULTILINE)
            
            service_ids = [int(m) for m in matches]
            HOSTNAME_PLACEHOLDER(f"Found VPRN Service IDs: {service_ids}")
            return service_ids
            
        except re.error as e:
            HOSTNAME_PLACEHOLDER(f"Regex pattern error: {e}")
            return []
            
        except ValueError as e:
            HOSTNAME_PLACEHOLDER(f"Error converting matches to integers: {e}")
            return []
            
        except NameError as e:
            HOSTNAME_PLACEHOLDER(f"Variable not defined: {e}")
            return []
            
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Unexpected error while searching for VPRN Service IDs: {e}")
            return []
            
    def build_dyn_command(self, base_command: str, args: Union[str, List]):
        
        try:
            full_commands_list = []
        
            if isinstance(args, str):
                args = [args]
            
            if not args:
                HOSTNAME_PLACEHOLDER("No arguments provided for command building")
                return []
            
            for arg in args:
                full_command = base_command.replace("<>", str(arg))
                full_commands_list.append(full_command)
                
            HOSTNAME_PLACEHOLDER(f"Built {len(full_commands_list)} dynamic commands")
            return full_commands_list
            
        except TypeError as e:
            HOSTNAME_PLACEHOLDER(f"Type error in Build_dyn_command: {e}")
            return []
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Unexpected error in Build_dyn_command: {e}")
            return []
        
    def check_cmg_active_alarms(self, ports: List[int], testcase_dir: str, 
               filter_criteria: str = None, prompt: str = r"A:.*?#\s*") -> bool:

        try:
            if not ports:
                raise ValueError("Ports list cannot be empty")
            
            if not all(isinstance(port, int) and port > 0 for port in ports):
                raise TypeError("All ports must be positive integers")
            
            # Construct port path from list of integers
            port_path = "/".join(map(str, ports))
            
            # Build network commands
            port_status_command = f"show port {port_path}"
            log_match_command = f'show log log-id 98 | match "{port_path}"'
            port_shutdown_command = f"configure port {port_path} shutdown"
            port_enable_command = f"configure port {port_path} no shutdown"
            
            network_commands = [
                port_status_command,
                port_shutdown_command,
                log_match_command,
                port_enable_command,
                port_status_command
            ]
            
            HOSTNAME_PLACEHOLDER(f"[CMD] Commands constructed for port {port_path}")
            for i, cmd in enumerate(network_commands, 1):
                HOSTNAME_PLACEHOLDER(f"  CMD[{i}]. {cmd}")
                        
        except ValueError as ve:
            HOSTNAME_PLACEHOLDER(f"Validation error in check_cmg_alarms: {ve}")
            return False
            
        except TypeError as te:
            HOSTNAME_PLACEHOLDER(f"Type error in check_cmg_alarms: {te}")
            return False
            
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Unexpected error in check_cmg_alarms: {e}")
            return False
        
        # Initialize final log file
        final_log_file = os.HOSTNAME_PLACEHOLDER(testcase_dir, "final_log.txt")
        
        # Helper function to copy log and clear source
        def copy_and_clear_log(source_log_file, dest_log_file, append_mode=True):
            try:
                mode = 'a' if append_mode else 'w'
                with open(source_log_file, 'r') as source_file:
                    with open(dest_log_file, mode) as dest_file:
                        if append_mode:
                            dest_file.write(f"\n--- Log Entry ---\n")
                        dest_file.write(source_file.read())
                
                # Clear the source log file
                with open(source_log_file, 'w') as log_file:
                    log_file.write('')
                
                HOSTNAME_PLACEHOLDER(f"Log copied from {source_log_file} to {dest_log_file}")
                return True
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Failed to copy log file: {e}")
                return False
        
        # Suppress info logs
        current_level = HOSTNAME_PLACEHOLDER().getEffectiveLevel()
        HOSTNAME_PLACEHOLDER().setLevel(HOSTNAME_PLACEHOLDER)
        
        # Test 1: Check initial port status (should be up)
        expected_dict = {"Admin State": "up", "Oper State": "up"}
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[0], testcase_dir, filter_criteria)
        result = SOURCE_NAME_PLACEHOLDER.validate_value_by_key(LogFile, expected_dict)
        if not result:
            HOSTNAME_PLACEHOLDER(f"Initial validation of active alarm status Failed")  
            return False
        
        if not copy_and_clear_log(LogFile, final_log_file, append_mode=False):  # First write, don't append
            return False
        
        # Test 2: Shutdown port
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[1], testcase_dir, filter_criteria)
        
        # Test 3: Check port status after shutdown (should be down)
        expected_dict = {"Admin State": "down", "Oper State": "down"}
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[0], testcase_dir, filter_criteria)
        result = SOURCE_NAME_PLACEHOLDER.validate_value_by_key(LogFile, expected_dict)
        if not result:
            HOSTNAME_PLACEHOLDER(f"Validation of port down status Failed")  
            return False
            
        if not copy_and_clear_log(LogFile, final_log_file):
            return False
        
        # Test 4: Check log for alarm entries
        expected_dict = {"administrative state": "outOfService", "operational state": "outOfService"}
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[2], testcase_dir, filter_criteria)  # Use log command
        result = SOURCE_NAME_PLACEHOLDER.validate_value_by_key(LogFile, expected_dict)
        if not result:
            HOSTNAME_PLACEHOLDER(f"Validation of alarm log status Failed")  
            return False
            
        if not copy_and_clear_log(LogFile, final_log_file):
            return False
        
        # Test 5: Re-enable port
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[3], testcase_dir, filter_criteria)
        
        # Test 6: Final check - port should be up again
        expected_dict = {"Admin State": "up", "Oper State": "up"}
        LogFile = HOSTNAME_PLACEHOLDER(network_commands[0], testcase_dir, filter_criteria)
        result = SOURCE_NAME_PLACEHOLDER.validate_value_by_key(LogFile, expected_dict)
        if not result:
            HOSTNAME_PLACEHOLDER(f"Final validation of port up status Failed")  
            return False
            
        if not copy_and_clear_log(LogFile, final_log_file):
            return False
        
        # Restore original log level
        HOSTNAME_PLACEHOLDER().setLevel(current_level)
        
        HOSTNAME_PLACEHOLDER(f"[1] Port status OK - {port_path}")
        HOSTNAME_PLACEHOLDER(f"[2] Port shutdown executed - {port_path} confirmed DOWN")
        HOSTNAME_PLACEHOLDER("[3] Alarm validation OK - Expected 'outOfService' states found")
        HOSTNAME_PLACEHOLDER("[4] Port status restored")
        HOSTNAME_PLACEHOLDER(f"[5] Final status OK - Port {port_path} is UP")
        HOSTNAME_PLACEHOLDER(f"[DONE] All CMG alarm tests passed. Log: {final_log_file}")

        return True