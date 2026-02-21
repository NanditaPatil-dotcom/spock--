import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from audio_model import CRNN
from audio_dataset import AudioDataset
import os

torch.set_num_threads(2)
DEVICE = torch.device("cpu")

model = CRNN().to(DEVICE)

criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)



DATASET_ROOT = "audio_dataset"  

REAL_DIR = os.path.join(DATASET_ROOT, "real")
FAKE_DIR = os.path.join(DATASET_ROOT, "fake")

real_files = [os.path.join(REAL_DIR, f)
              for f in os.listdir(REAL_DIR)
              if f.endswith(".flac")]

fake_files = [os.path.join(FAKE_DIR, f)
              for f in os.listdir(FAKE_DIR)
              if f.endswith(".flac")]

print("Real files:", len(real_files))
print("Fake files:", len(fake_files))

files = real_files + fake_files
labels = [0]*len(real_files) + [1]*len(fake_files)

dataset = AudioDataset(files, labels)
loader = DataLoader(dataset, batch_size=8, shuffle=True)

EPOCHS = 8

for epoch in range(EPOCHS):
    total_loss = 0

    for mel, label in loader:
        mel = mel.to(DEVICE)
        label = label.to(DEVICE).unsqueeze(1)

        output = model(mel)

        loss = criterion(output, label)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}, Loss: {total_loss/len(loader)}")



model.eval()

#test
real_scores = []
fake_scores = []

with torch.no_grad():
    for mel, label in loader:
        mel = mel.to(DEVICE)
        output = model(mel).cpu().numpy().flatten()
        
        for o, l in zip(output, label):
            if l.item() == 0:
                real_scores.append(float(o))
            else:
                fake_scores.append(float(o))

import numpy as np

print("Real mean:", np.mean(real_scores))
print("Fake mean:", np.mean(fake_scores))
#test


import numpy as np

mean_real = np.mean(real_scores)
mean_fake = np.mean(fake_scores)

threshold = mean_real + 0.6 * (mean_fake - mean_real)

print("Chosen threshold:", threshold)

torch.save({
    "model_state": model.state_dict(),
    "threshold": threshold
}, "weights/audio_model.pth")