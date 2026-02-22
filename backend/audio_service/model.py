import torch
import torch.nn as nn
from pathlib import Path

class CRNN(nn.Module):
    def __init__(self):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d((2,2)),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d((2,2)),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d((2,2))
        )

        self.rnn = nn.LSTM(
            input_size=128,
            hidden_size=128,
            num_layers=2,
            batch_first=True
        )

        self.fc = nn.Linear(128, 1)

    def forward(self, x):
        x = self.cnn(x)

        # shape: (B, C, F, T)
        x = torch.mean(x, dim=2)  # global average over freq

        x = x.permute(0, 2, 1)  # (B, T, C)

        x, _ = self.rnn(x)

        x = x[:, -1, :]
        x = self.fc(x)

        return torch.sigmoid(x)
    

def load_audio_model():
    model = CRNN()
    weights_dir = Path(__file__).resolve().parent.parent / "weights"
    candidate_paths = [weights_dir / "audio_model.pth"]
    weights_path = next((p for p in candidate_paths if p.exists()), None)
    if weights_path is None:
        checked = ", ".join(str(p) for p in candidate_paths)
        raise FileNotFoundError(f"Audio model weights not found. Checked: {checked}")

    checkpoint = torch.load(
        weights_path,
        map_location="cpu",
        weights_only=False
    )

    model.load_state_dict(checkpoint["model_state"])

    threshold = checkpoint["threshold"]

    return model, threshold
