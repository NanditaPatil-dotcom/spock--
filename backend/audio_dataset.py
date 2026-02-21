import os
import librosa
import numpy as np
import torch
from torch.utils.data import Dataset

class AudioDataset(Dataset):
    def __init__(self, file_paths, labels):
        self.file_paths = file_paths
        self.labels = labels

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        path = self.file_paths[idx]
        label = self.labels[idx]

        audio, sr = librosa.load(path, sr=16000)

        mel = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_mels=128,
            n_fft=1024,
            hop_length=512
        )

        mel = librosa.power_to_db(mel, ref=np.max)
        mel = np.nan_to_num(mel)

        MAX_LEN = 300  # choose fixed time dimension

        mel = torch.tensor(mel).float()

        # Pad or trim time dimension
        if mel.shape[1] < MAX_LEN:
            pad_size = MAX_LEN - mel.shape[1]
            mel = torch.nn.functional.pad(mel, (0, pad_size))
        else:
            mel = mel[:, :MAX_LEN]

        mel = mel.unsqueeze(0)  # (1, 128, 300)

        return mel, torch.tensor(label).float()
