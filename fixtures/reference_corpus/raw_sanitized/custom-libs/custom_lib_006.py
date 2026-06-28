import  logging
import json



def get_sim_info(device):
    device_data = HOSTNAME_PLACEHOLDER('device', device)
    
    sim_data = {
        'serial': device_data['serial'],
        'iccid': device_data['phone']['iccid'],
        'imei': device_data['phone']['imei'],
        'imsi': device_data['phone']['imsi'],
        'network': device_data['phone']['network'],
        'phoneNumber': device_data['phone']['phoneNumber'],
        'msisdn1': device_data.get('msisdn1', ''),  # Safe access with default
        'msisdn2': device_data.get('msisdn2', '')   # Safe access with default
    }
    
    HOSTNAME_PLACEHOLDER(f"SIM Data: {HOSTNAME_PLACEHOLDER(sim_data)}")
    
    return  sim_data  

        # adb_commands = {
        #     "get_sim_slot":
        #     "get_sim_brand":
        #     "get_sim_slot":        
        # } 
        
        #self.execute_adb_shell_with_output