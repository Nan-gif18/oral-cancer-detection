import os
import random
import numpy as np
from glob import glob
import json
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets
import timm

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# ==================== CONFIGURATION ====================
# Update these paths according to your setup
CONFIG = {
    "oscc_dir": r"C:\Users\HP\OneDrive\Desktop\oralcancer\oralcancer\Second Set\400x OSCC Histopathological Images",
    "normal_dir": r"C:\Users\HP\OneDrive\Desktop\oralcancer\oralcancer\Second Set\400x Normal Oral Cavity Histopathological Images",
    "output_base_dir": r"C:\Users\HP\OneDrive\Desktop\oralcancer\oralcancer\output",
    "img_size": 224,
    "batch_size": 16,
    "epochs": 30,
    "lr": 0.0001,
    "val_split": 0.2,
    "num_workers": 4,
    "seed": 42,
    "freeze_backbone_epochs": 3,
    "early_stopping_patience": 5,
    "use_amp": True
}


def seed_everything(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class GrayscaleToRGB(object):
    """Convert grayscale PIL image to 3-channel RGB."""
    def __call__(self, img):
        return img.convert("RGB")


def build_dataloaders(oscc_dir, normal_dir, img_size, batch_size, val_split, num_workers):
    root_dir = "/tmp/oral_cancer_dataset"
    if not os.path.exists(root_dir):
        os.makedirs(root_dir, exist_ok=True)
        os.makedirs(os.path.join(root_dir, "OSCC"), exist_ok=True)
        os.makedirs(os.path.join(root_dir, "Normal"), exist_ok=True)

        for f in glob(os.path.join(oscc_dir, "*")):
            if os.path.isfile(f):
                try:
                    os.symlink(f, os.path.join(root_dir, "OSCC", os.path.basename(f)))
                except FileExistsError:
                    pass
        for f in glob(os.path.join(normal_dir, "*")):
            if os.path.isfile(f):
                try:
                    os.symlink(f, os.path.join(root_dir, "Normal", os.path.basename(f)))
                except FileExistsError:
                    pass

    train_tfms = transforms.Compose([
        GrayscaleToRGB(),
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])

    val_tfms = transforms.Compose([
        GrayscaleToRGB(),
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])

    full_dataset = datasets.ImageFolder(root=root_dir)
    val_len = int(len(full_dataset) * val_split)
    train_len = len(full_dataset) - val_len

    train_dataset, val_dataset = random_split(full_dataset, [train_len, val_len])
    
    train_dataset.dataset.transform = train_tfms
    val_dataset.dataset.transform = val_tfms

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, full_dataset.classes


def build_model(model_name, num_classes):
    """Build model using timm library"""
    if model_name == "InceptionResNetV2":
        model = timm.create_model('inception_resnet_v2', pretrained=True, num_classes=num_classes)
    elif model_name == "XceptionNet":
        model = timm.create_model('xception', pretrained=True, num_classes=num_classes)
    elif model_name == "EfficientNetB3":
        model = timm.create_model('efficientnet_b3', pretrained=True, num_classes=num_classes)
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    return model


def get_classifier_params(model, model_name):
    """Get classifier parameters for different model architectures"""
    classifier_params = []
    
    if model_name == "InceptionResNetV2":
        # InceptionResNetV2 uses 'classif' as the final layer
        if hasattr(model, 'classif'):
            classifier_params = list(model.classif.parameters())
    elif model_name == "XceptionNet":
        # Xception uses 'fc' as the final layer
        if hasattr(model, 'fc'):
            classifier_params = list(model.fc.parameters())
    elif model_name == "EfficientNetB3":
        # EfficientNet uses 'classifier' as the final layer
        if hasattr(model, 'classifier'):
            classifier_params = list(model.classifier.parameters())
    
    # Fallback: try common names
    if not classifier_params:
        for name in ['classifier', 'fc', 'head', 'classif']:
            if hasattr(model, name):
                classifier_params = list(getattr(model, name).parameters())
                break
    
    return classifier_params


def train_model(model, train_loader, val_loader, device, config, output_dir, model_name):
    """Train model"""
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'])
    
    # Use appropriate AMP based on device
    use_amp = config['use_amp'] and device.type == 'cuda'
    if use_amp:
        scaler = torch.amp.GradScaler('cuda')
    else:
        scaler = None
        if config['use_amp'] and device.type == 'cpu':
            print("Note: AMP is disabled on CPU\n")

    best_acc = 0.0
    patience_counter = 0
    
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []

    os.makedirs(output_dir, exist_ok=True)

    for epoch in range(config['epochs']):
        # Freeze/unfreeze backbone
        if epoch < config['freeze_backbone_epochs']:
            # Get classifier parameters
            classifier_params = get_classifier_params(model, model_name)
            
            if classifier_params:
                # Freeze all parameters first
                for param in model.parameters():
                    param.requires_grad = False
                
                # Unfreeze only classifier parameters
                for param in classifier_params:
                    param.requires_grad = True
                
                # Recreate optimizer with only trainable parameters
                optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=config['lr'])
            else:
                # If no classifier found, train all parameters
                print(f"Warning: Could not identify classifier layer for {model_name}. Training all parameters.")
                for param in model.parameters():
                    param.requires_grad = True
                optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'])
        else:
            # Unfreeze all parameters
            for param in model.parameters():
                param.requires_grad = True
            # Recreate optimizer with all parameters
            optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'])

        # Training
        model.train()
        running_loss, running_corrects = 0.0, 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            
            if use_amp:
                with torch.amp.autocast('cuda'):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

            _, preds = torch.max(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_acc = running_corrects.double() / len(train_loader.dataset)
        train_losses.append(epoch_loss)
        train_accs.append(epoch_acc.item())

        # Validation
        model.eval()
        val_running_loss, val_running_corrects = 0.0, 0
        y_true, y_pred = [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                
                if use_amp:
                    with torch.amp.autocast('cuda'):
                        outputs = model(inputs)
                        loss = criterion(outputs, labels)
                else:
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    
                _, preds = torch.max(outputs, 1)
                val_running_loss += loss.item() * inputs.size(0)
                val_running_corrects += torch.sum(preds == labels.data)
                y_true.extend(labels.cpu().numpy())
                y_pred.extend(preds.cpu().numpy())

        val_loss = val_running_loss / len(val_loader.dataset)
        val_acc = val_running_corrects.double() / len(val_loader.dataset)
        val_losses.append(val_loss)
        val_accs.append(val_acc.item())

        print(f"Epoch {epoch+1}/{config['epochs']} | "
              f"Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), os.path.join(output_dir, "best_model.pth"))
            best_y_true, best_y_pred = y_true, y_pred
            print(">> Model saved.")
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= config['early_stopping_patience']:
                print(">> Early stopping triggered.")
                break

    # Save training plots
    plot_training_history(train_losses, train_accs, val_losses, val_accs, output_dir)
    
    # Save metrics
    save_metrics(best_y_true, best_y_pred, best_acc.item(), output_dir)
    
    return model


def plot_training_history(train_losses, train_accs, val_losses, val_accs, output_dir):
    """Plot and save training history"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    axes[0].plot(train_losses, label='Train Loss', marker='o')
    axes[0].plot(val_losses, label='Val Loss', marker='s')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)
    
    axes[1].plot(train_accs, label='Train Accuracy', marker='o')
    axes[1].plot(val_accs, label='Val Accuracy', marker='s')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'training_history.png'), dpi=150, bbox_inches='tight')
    plt.close()


def save_metrics(y_true, y_pred, best_acc, output_dir):
    """Save all metrics to text file"""
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
    
    cm = confusion_matrix(y_true, y_pred)
    
    # Save confusion matrix plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Normal', 'OSCC'], yticklabels=['Normal', 'OSCC'])
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Confusion Matrix')
    plt.savefig(os.path.join(output_dir, 'confusion_matrix.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save metrics to text file
    with open(os.path.join(output_dir, 'metrics.txt'), 'w') as f:
        f.write("="*50 + "\n")
        f.write("MODEL EVALUATION METRICS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Best Validation Accuracy: {best_acc:.4f}\n")
        f.write(f"Accuracy: {accuracy:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"F1-Score: {f1:.4f}\n\n")
        f.write("="*50 + "\n")
        f.write("CLASSIFICATION REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(classification_report(y_true, y_pred, target_names=['Normal', 'OSCC']))
        f.write("\n" + "="*50 + "\n")
        f.write("CONFUSION MATRIX\n")
        f.write("="*50 + "\n\n")
        f.write(str(cm))


def main():
    print("="*70)
    print("ORAL CANCER CLASSIFICATION TRAINING")
    print("="*70)
    print("\nSelect training option:")
    print("1. InceptionResNetV2")
    print("2. XceptionNet")
    print("3. EfficientNetB3")
    print("="*70)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    options = {
        '1': 'InceptionResNetV2',
        '2': 'XceptionNet',
        '3': 'EfficientNetB3',
    }
    
    if choice not in options:
        print("Invalid choice! Exiting...")
        return
    
    model_name = options[choice]
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(CONFIG['output_base_dir'], f"{model_name}_{timestamp}")
    
    print(f"\n{'='*70}")
    print(f"Training Configuration:")
    print(f"Model: {model_name}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*70}\n")
    
    seed_everything(CONFIG['seed'])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}\n")
    
    # Build dataloaders
    print("Loading datasets...")
    train_loader, val_loader, classes = build_dataloaders(
        CONFIG['oscc_dir'], CONFIG['normal_dir'],
        CONFIG['img_size'], CONFIG['batch_size'], 
        CONFIG['val_split'], CONFIG['num_workers']
    )
    print(f"Classes: {classes}")
    print(f"Train samples: {len(train_loader.dataset)}")
    print(f"Val samples: {len(val_loader.dataset)}\n")
    
    # Build model
    print(f"Building {model_name} model...")
    model = build_model(model_name, num_classes=len(classes))
    model = model.to(device)
    print("Model loaded successfully!\n")
    
    # Train model
    print("Starting training...\n")
    train_model(
        model, train_loader, val_loader, device,
        CONFIG, output_dir, model_name
    )
    
    print(f"\n{'='*70}")
    print(f"Training completed!")
    print(f"All results saved to: {output_dir}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

    




