#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: Louis Rossignol

import numpy as np
from engine.field_dataset import FieldDataset
from torch.utils.data import DataLoader

def data_split(
        E: np.ndarray, 
        n2_labels: np.ndarray,
        isat_labels: np.ndarray,
        train_ratio: float = 0.8, 
        validation_ratio: float = 0.1, 
        test_ratio: float = 0.1
        ) -> tuple:
    # Ensure the ratios sum to 1
    assert train_ratio + validation_ratio + test_ratio == 1
    
    np.random.seed(0)
    indices = np.arange(E.shape[0])
    np.random.shuffle(indices)
    
    train_index = int(len(indices) * train_ratio)
    validation_index = int(len(indices) * (train_ratio + validation_ratio))

    training_indices = indices[:train_index]
    validation_indices = indices[train_index:validation_index]
    test_indices = indices[validation_index:]

    train = E[training_indices,:,:,:].copy()
    validation = E[validation_indices,:,:,:].copy()
    test = E[test_indices,:,:,:].copy()

    train_n2 = n2_labels[training_indices].copy()
    validation_n2 = n2_labels[validation_indices].copy()
    test_n2 = n2_labels[test_indices].copy()

    train_isat = isat_labels[training_indices].copy()
    validation_isat = isat_labels[validation_indices].copy()
    test_isat = isat_labels[test_indices].copy()

    return (train, train_n2, train_isat), (validation, validation_n2, validation_isat), (test, test_n2, test_isat)

def data_treatment(
        sets: np.ndarray, 
        batch_size: int, 
        training: bool):
    
    set, n2label, isatlabel = sets 
    fieldset = FieldDataset(set, n2label, isatlabel, training)
    fieldloader = DataLoader(fieldset, batch_size=batch_size, shuffle=True)

    return fieldloader