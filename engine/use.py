#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: Louis Rossignol
import torch
import numpy as np
from scipy.ndimage import zoom
from engine.nlse_generator import normalize_data
from engine.model import Inception_ResNetv2
from skimage.restoration import unwrap_phase
import torch.nn as nn


def reshape_resize(E, resolution_out):
    if E.shape[2] != E.shape[3]:
        cut = (E.shape[3] - E.shape[2])//2
        E_reshape = E[:,0,:,cut:E.shape[3] - cut]
    else:
        E_reshape = E
    
    if resolution_out != E_reshape.shape[1]:
        E_resized = zoom(E_reshape, (1, resolution_out/E_reshape.shape[1],resolution_out/E_reshape.shape[2]), order=3)
    else:
        E_resized = E_reshape
    
    return E_resized

def formatting(E_resized, resolution_out, number_of_power):
    E_formatted = np.zeros((1, 2*number_of_power, resolution_out, resolution_out))

    even_indices = np.arange(0, number_of_power*2, 2)
    data_even = np.abs(E_resized)**2

    odd_indices = np.arange(1, number_of_power*2, 2)
    data_odd = unwrap_phase(np.angle(E_resized))
    
    E_formatted[0, even_indices, :, :] = data_even

    E_formatted[0, odd_indices, :, :] = data_odd

    E_formatted = normalize_data(E_formatted)
    return E_formatted

def get_parameters(exp_path, saving_path, resolution_out, numbers, device_number):
    number_of_n2, power_alpha, number_of_isat = numbers
    power_values, alpha_values = power_alpha
    number_of_power = len(power_values)

    n2 = np.linspace(-1e-11, -1e-9, number_of_n2)
    isat = np.linspace(1e4, 1e6, number_of_isat)

    device = torch.device(f"cuda:{device_number}")
    
    E_experiment = np.load(exp_path)
    E_resized = reshape_resize(E_experiment, resolution_out)
    E = formatting(E_resized, resolution_out, number_of_power)

    cnn = Inception_ResNetv2(in_channels=E.shape[1], class_n2=number_of_n2, class_isat=number_of_isat)
    cnn = nn.DataParallel(cnn, device_ids=[0, 1])
    cnn.load_state_dict(torch.load(f'{saving_path}/training_n2{number_of_n2}_isat{number_of_isat}_power{number_of_power}/n2_net_w{resolution_out}_n2{number_of_n2}_isat{number_of_isat}_power{number_of_power}.pth'))

    with torch.no_grad():
        images = torch.from_numpy(E).float().to(device)
        outputs_n2, outputs_isat = cnn(images)
        _, predicted_n2 = torch.max(outputs_n2, 1)
        _, predicted_isat = torch.max(outputs_isat, 1)

    print(f"n2 = {n2[predicted_n2]:.2e} m^2/W")
    print(f"Isat = {isat[predicted_isat]:.2e} W/m^2")