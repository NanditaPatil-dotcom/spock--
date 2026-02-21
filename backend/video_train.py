import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader



DEVICE = torch.device("cpu")
BATCH_SIZE = 16
EPOCHS = 5
LR = 1e-3

DATA_DIR = "dataset"
WEIGHTS_PATH = "weights/model.pth"


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)



model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False

# Replace classifier
model.fc = nn.Linear(model.fc.in_features, 1)

model.to(DEVICE)

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=LR)



print("Starting training...")

for epoch in range(EPOCHS):
    total_loss = 0

    for images, labels in loader:
        images = images.to(DEVICE)
        labels = labels.float().unsqueeze(1).to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch [{epoch+1}/{EPOCHS}] Loss: {total_loss/len(loader):.4f}")

print("Training complete.")

model.eval()

real_scores = []
fake_scores = []

with torch.no_grad():
    for images, labels in loader:
        images = images.to(DEVICE)
        outputs = model(images)
        probs = torch.sigmoid(outputs).cpu().numpy()

        for p, l in zip(probs, labels):
            score = float(p[0])
            if l.item() == 0:
                real_scores.append(score)
            else:
                fake_scores.append(score)

import numpy as np

all_scores = real_scores + fake_scores
best_threshold = 0
best_accuracy = 0

for t in np.linspace(0, 1, 200):
    correct = 0

    for s in real_scores:
        if s < t:
            correct += 1

    for s in fake_scores:
        if s >= t:
            correct += 1

    acc = correct / len(all_scores)

    if acc > best_accuracy:
        best_accuracy = acc
        best_threshold = t

print("Best threshold:", best_threshold)
print("Training accuracy:", best_accuracy)

# Save weights
os.makedirs("weights", exist_ok=True)
torch.save({
    "model_state": model.state_dict(),
    "threshold": best_threshold
}, "weights/model.pth")

print("Model saved.")
