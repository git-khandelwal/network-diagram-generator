def classify_device(device_name):
    device_name = device_name.lower()
    if 'server' in device_name:
        return 'server'
    elif ('r' in device_name and device_name[1:].isdigit()) or 'router' in device_name:  # R1, R2, etc.
        return 'router'
    elif ('sw' in device_name and device_name[2:].isdigit()) or 'switch' in device_name:  # SW1, SW2, etc.
        return 'switch'
    elif 'pc' in device_name:
        return 'pc'
    else:
        return 'other'
    

icons = {
    'server': r'icons\file-server.png',
    'router': r'icons\router.png',
    'pc': r'icons\pc.png',
    'switch': r'icons\switch.png',
    'other': r'icons\cloud.png'
}

