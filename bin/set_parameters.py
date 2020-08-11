import PySimpleGUI as sg
import yaml
import numpy as np
import os

# set layout for GUI
sg.theme('LightGrey1')
appFont = ("Arial", 12)
sg.set_options(font=appFont)

layout = [[sg.Text('Foldername', font='bold')],
          [sg.Input(key='folder_name'), sg.FolderBrowse()],
          [sg.Text('')],
          [sg.Text('')],
          [sg.Text('Input Files', font='bold')],
          [sg.Text('Phase')],
          [sg.Input(key='inp_1'), sg.FileBrowse()],
          [sg.Checkbox('Phase', key='phase', default=True), sg.Checkbox('PH', key='ph', default=False)],
          [sg.Text('')],
          [sg.Text('Additional channel 1', font='bold')],
          [sg.Input(key='inp_2'), sg.FileBrowse()],
          [sg.Text('Channel type 1')],
          [sg.Checkbox('GFP', key='gfp_1'), sg.Checkbox('mCherry', key='cherry_1'), sg.Checkbox('TXRED', key='txred_1')],
          [sg.Text('Cell type 1')],      
          [sg.Checkbox('13B01', key='cell_type_11'), sg.Checkbox('ZF270g', key='cell_type_12'), sg.Checkbox('FS144', key='cell_type_13')],
          [sg.Checkbox('A3M17', key='cell_type_14'), sg.Checkbox('1F187', key='cell_type_15')], 
          [sg.Text('')],
          [sg.Text('Additional channel 2', font='bold')],
          [sg.Input(key='inp_3'), sg.FileBrowse()],
          [sg.Text('Channel type 2')],
          [sg.Checkbox('GFP', key='gfp_2'), sg.Checkbox('mCherry', key='cherry_2'), sg.Checkbox('TXRED', key='txred_2')],
          [sg.Text('Cell type 2')],      
          [sg.Checkbox('13B01', key='cell_type_21'), sg.Checkbox('ZF270g', key='cell_type_22'), sg.Checkbox('FS144', key='cell_type_23')],
          [sg.Checkbox('A3M17', key='cell_type_24'), sg.Checkbox('1F187', key='cell_type_25')], 
	      [sg.Text('')],
          [sg.OK(), sg.Cancel()]] 

window = sg.Window('Parameters', layout)

event, values = window.read()
window.close()

# extract results from GUI
sel_inputs = []
for i in range(3):
    if len(values['inp_' + str(i + 1)]) > 0:
        sel_inputs.append(values['inp_' + str(i + 1)])

channel_types = ['Phase', 'PH', 'GFP', 'mCherry', 'TXRED', 'GFP', 'mCherry', 'TXRED']
channel_type_vals = [values['phase'], values['ph'], values['gfp_1'], values['cherry_1'], values['txred_1'], values['gfp_2'], values['cherry_2'], values['txred_2']]
ix_channels = np.where(channel_type_vals)[0]
sel_channel_types = [channel_types[i] for i in ix_channels]

cell_types = ['13B01', 'Zf270g', 'FS144', 'A3M17', '1F187', '13B01', 'Zf270g', 'FS144', 'A3M17', '1F187']
cell_type_vals = [values['cell_type_11'], values['cell_type_12'], values['cell_type_13'], values['cell_type_14'], values['cell_type_15'],\
                  values['cell_type_21'], values['cell_type_22'], values['cell_type_23'], values['cell_type_24'], values['cell_type_25']]
ix_cells = np.where(cell_type_vals)[0]
sel_cell_types = [cell_types[i] for i in ix_cells]

dict_file = [{'FOLDERNAME' : values['folder_name']},
{'CHANNELS' : sel_channel_types}, {'CELL_TYPES': sel_cell_types}]

# save parameters to config file
with open(r'config.yaml', 'w') as file:
    documents = yaml.dump(dict_file, file)

file_settings = open("settings.sh","w") 
file_settings.write("PATH_FOLDER=" + values['folder_name'] + "/ \n") 

file_settings.write("INPUTS=" + str(sel_inputs) + "\n")

for i, s in enumerate(sel_inputs):
    file_settings.write("INP_" + str(i + 1) + "=" + os.path.basename(s) + "\n")
file_settings.write("NUM_INP=" + str(len(sel_inputs)) + "\n")

for i, s in enumerate(sel_cell_types):
	file_settings.write("CELL_TYPE_" + str(i + 1) + "=" + s + "\n")
file_settings.write("NUM_CELL_TYPES=" + str(len(sel_cell_types)) + "\n")

for i, s in enumerate(sel_channel_types):
        file_settings.write("CHANNEL_" + str(i + 1) + "=" + s + "\n")
file_settings.write("NUM_CHANNEL_TYPES=" + str(len(sel_channel_types)) + "\n")
file_settings.close()
