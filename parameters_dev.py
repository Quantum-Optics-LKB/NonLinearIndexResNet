#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: Louis Rossignol

import gc
import numpy as np
from engine.finder import launch_training, prep_training
from engine.use import get_parameters
import cupy as cp
from engine.generate_augment import data_creation, data_augmentation, generate_labels

saving_path="/home/louis/LEON/DATA/Atoms/2024/PINNS2/CNN"
input_alpha_path="/home/louis/LEON/DATA/Atoms/2024/PINNS2/CNN/exp_data/alpha.npy"
exp_image_path="/home/louis/LEON/DATA/Atoms/2024/PINNS2/CNN/exp/experiment.npy"

device = 1
resolution_in = 2048
window_in = 50e-3
smallest_out_res = 3008
out_pixel_size = 3.76e-6
window_out = out_pixel_size * smallest_out_res
resolution_training = 256

number_of_n2 = 10
number_of_isat = 10
n2 = -5*np.logspace(-11, -9, number_of_n2) #m/W^2
isat = np.logspace(4, 5, number_of_isat) #W/m^2

delta_z=1e-4
length=20e-2

in_power = 1.05 #W
alpha = 22 #m^-1
waist = 2.3e-3 #m
nl_length = 0

expansion=False
generate=False
training=True
learning_rate=0.01
batch_size=33
accumulator=3
num_epochs=100

use=True
plot_generate_compare=True

cameras = resolution_in, window_in, window_out, resolution_training
nlse_settings = n2, in_power, alpha, isat, waist, nl_length, delta_z, length

if expansion or generate or training:
    if generate:
        with cp.cuda.Device(device):
            E = data_creation(nlse_settings, cameras ,saving_path)
    else:
        if expansion:
            file = f'{saving_path}/Es_w{resolution_training}_n2{number_of_n2}_isat{number_of_isat}_power{in_power:.2f}.npy'
            E = np.load(file)
        else:
            E = np.zeros((number_of_n2*number_of_isat, 3, resolution_training, resolution_training), dtype=np.float16)

    labels = generate_labels(n2, isat)
    E, labels = data_augmentation(E, in_power, expansion, saving_path, labels)

    if training:
        print("---- TRAINING ----")
        trainloader, validationloader, testloader, model_settings, new_path = prep_training(nlse_settings, labels, E, saving_path, learning_rate, batch_size, num_epochs, accumulator, device)
        del E
        gc.collect()
        launch_training(trainloader, validationloader, testloader, model_settings, nlse_settings, new_path, resolution_training, labels)

if use:
    print("---- COMPUTING PARAMETERS ----\n")
    get_parameters(exp_image_path, saving_path, resolution_training, nlse_settings, device, cameras, plot_generate_compare)