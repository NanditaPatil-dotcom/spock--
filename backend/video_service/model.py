import torch
import torch.nn as nn
import torchvision.models as models
from pathlib import Path

class DeepfakeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = models.resnet18(weights=None)
        self.target_layer = self.backbone.layer4[-1]
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, 1)

    def forward(self, x):
        return self.backbone(x)

def load_model():
    model = DeepfakeModel()  
    weights_path = Path(__file__).resolve().parent.parent / "weights" / "model.pth"

    try:
        ckpt = torch.load(weights_path, map_location="cpu", weights_only=False)
    except TypeError:
        ckpt = torch.load(weights_path, map_location="cpu")
    except Exception:
        try:
            import torch.serialization as ts
            import numpy as _np
            ts.add_safe_globals([_np._core.multiarray.scalar])
            ckpt = torch.load(weights_path, map_location="cpu", weights_only=False)
        except Exception:
            ckpt = torch.load(weights_path, map_location="cpu")
    state_dict = ckpt.get("model_state", ckpt.get("state_dict", ckpt)) if isinstance(ckpt, dict) else ckpt
    threshold = ckpt.get("threshold", 0.7) if isinstance(ckpt, dict) else 0.7
    threshold = float(threshold)

    if isinstance(state_dict, dict) and not any(k.startswith("backbone.") for k in state_dict.keys()):
        new_state = {}
        for k, v in state_dict.items():
            if k.startswith(("conv1", "bn1", "layer", "fc", "target_layer")):
                new_state[f"backbone.{k}"] = v
            else:
                new_state[k] = v
        state_dict = new_state

    model.load_state_dict(state_dict, strict=False)
    return model, threshold
