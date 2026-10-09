import os
import numpy as np
from glob import glob
import json
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
import timm

import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# ==================== CONFIGURATION ====================
# Update these paths according to your setup
CONFIG = {
    "models_base_dir": r"C:\oralcancer\output",
    "output_dir": r"C:\oralcancer\detection_results",
    "img_size": 224,
    "class_names": ["Normal", "OSCC"]
}

# Model paths mapping - Only 3 basic models needed
MODEL_PATHS = {
    "InceptionResNetV2": "InceptionResNetV2_20251108_103240/best_model.pth",
    "XceptionNet": "XceptionNet_20251105_141151/best_model.pth",
    "EfficientNetB3": "EfficientNetB3_20251105_124019/best_model.pth",
}


class GrayscaleToRGB(object):
    """Convert grayscale PIL image to 3-channel RGB."""

    def __call__(self, img):
        return img.convert("RGB")


def get_transforms(img_size):
    """Get image preprocessing transforms"""
    return transforms.Compose([
        GrayscaleToRGB(),
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.5] * 3, [0.5] * 3)
    ])


def build_model(model_name, num_classes=2):
    """Build model architecture"""
    if model_name == "InceptionResNetV2":
        model = timm.create_model('inception_resnet_v2', pretrained=False, num_classes=num_classes)
    elif model_name == "XceptionNet":
        model = timm.create_model('xception', pretrained=False, num_classes=num_classes)
    elif model_name == "EfficientNetB3":
        model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=num_classes)
    else:
        raise ValueError(f"Unknown model: {model_name}")
    return model


def load_model(model_path, model_name, device):
    """Load trained model"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = build_model(model_name)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


class GradCAM:
    """Grad-CAM implementation"""

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_full_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output.detach()

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_cam(self, input_tensor, target_class=None):
        self.model.eval()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1)

        self.model.zero_grad()
        output[0, target_class].backward()

        gradients = self.gradients[0]
        activations = self.activations[0]

        weights = gradients.mean(dim=(1, 2), keepdim=True)
        cam = (weights * activations).sum(dim=0)
        cam = F.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)

        return cam.cpu().numpy()


def get_target_layer(model, model_name):
    """Get the target layer for Grad-CAM"""
    if model_name == "InceptionResNetV2":
        return model.conv2d_7b
    elif model_name == "XceptionNet":
        return model.conv4
    elif model_name == "EfficientNetB3":
        return model.conv_head
    else:
        raise ValueError(f"Unknown model: {model_name}")


def occlusion_sensitivity(model, image, target_class, patch_size=20, stride=10):
    """Generate occlusion sensitivity map"""
    model.eval()
    h, w = image.shape[2:]
    sensitivity_map = np.zeros((h, w))

    with torch.no_grad():
        baseline_output = model(image)
        baseline_prob = F.softmax(baseline_output, dim=1)[0, target_class].item()

    total_steps = ((h - patch_size) // stride) * ((w - patch_size) // stride)
    current_step = 0

    for y in range(0, h - patch_size, stride):
        for x in range(0, w - patch_size, stride):
            occluded_image = image.clone()
            occluded_image[:, :, y:y + patch_size, x:x + patch_size] = 0

            with torch.no_grad():
                output = model(occluded_image)
                prob = F.softmax(output, dim=1)[0, target_class].item()

            sensitivity_map[y:y + patch_size, x:x + patch_size] = baseline_prob - prob
            current_step += 1

            if current_step % 10 == 0:
                print(f"  Processing occlusion: {current_step}/{total_steps}", end='\r')

    print()
    return sensitivity_map


def visualize_and_save(original_img, heatmap, save_path, title, pred_class, confidence, class_names):
    """Visualize and save detection results with heatmap"""
    fig = plt.figure(figsize=(16, 5))

    # Original Image
    plt.subplot(1, 4, 1)
    plt.imshow(original_img)
    plt.title('Original Image', fontsize=12, fontweight='bold')
    plt.axis('off')

    # Prediction Info
    plt.subplot(1, 4, 2)
    plt.text(0.5, 0.6, f'Prediction: {class_names[pred_class]}',
             ha='center', va='center', fontsize=14, fontweight='bold',
             color='green' if pred_class == 0 else 'red')
    plt.text(0.5, 0.4, f'Confidence: {confidence:.2%}',
             ha='center', va='center', fontsize=12)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.axis('off')

    # Heatmap
    plt.subplot(1, 4, 3)
    plt.imshow(heatmap, cmap='jet')
    plt.title(title, fontsize=12, fontweight='bold')
    plt.colorbar(fraction=0.046, pad=0.04)
    plt.axis('off')

    # Overlay
    plt.subplot(1, 4, 4)
    plt.imshow(original_img)
    plt.imshow(heatmap, cmap='jet', alpha=0.5)
    plt.title('Overlay', fontsize=12, fontweight='bold')
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


def save_simple_prediction(original_img, pred_class, confidence, save_path, class_names):
    """Save simple prediction without visualization"""
    fig = plt.figure(figsize=(10, 5))

    # Original Image
    plt.subplot(1, 2, 1)
    plt.imshow(original_img)
    plt.title('Input Image', fontsize=14, fontweight='bold')
    plt.axis('off')

    # Prediction
    plt.subplot(1, 2, 2)
    plt.text(0.5, 0.6, f'Prediction:',
             ha='center', va='center', fontsize=14, fontweight='bold')
    plt.text(0.5, 0.4, f'{class_names[pred_class]}',
             ha='center', va='center', fontsize=18, fontweight='bold',
             color='green' if pred_class == 0 else 'red')
    plt.text(0.5, 0.2, f'Confidence: {confidence:.2%}',
             ha='center', va='center', fontsize=12)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


def detect_single_model(image_path, model_path, model_name, device, output_dir, visualization_mode=None):
    """Detect using a single model"""
    print(f"\nLoading model: {model_name}")
    model = load_model(model_path, model_name, device)

    # Load and preprocess image
    print("Loading image...")
    img_pil = Image.open(image_path).convert('RGB')
    transform = get_transforms(CONFIG['img_size'])
    img_tensor = transform(img_pil).unsqueeze(0).to(device)

    # Get prediction
    print("Making prediction...")
    with torch.no_grad():
        output = model(img_tensor)
        probabilities = F.softmax(output, dim=1)
        confidence, pred_class = probabilities.max(dim=1)
        pred_class = pred_class.item()
        confidence = confidence.item()

    print(f"Prediction: {CONFIG['class_names'][pred_class]} (Confidence: {confidence:.2%})")

    # Prepare image for visualization
    img_np = np.array(img_pil.resize((CONFIG['img_size'], CONFIG['img_size']))) / 255.0

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    image_name = os.path.splitext(os.path.basename(image_path))[0]

    if visualization_mode == 'gradcam':
        print("Generating Grad-CAM visualization...")
        target_layer = get_target_layer(model, model_name)
        gradcam = GradCAM(model, target_layer)
        cam = gradcam.generate_cam(img_tensor, target_class=pred_class)
        cam_resized = np.array(Image.fromarray(cam).resize((CONFIG['img_size'], CONFIG['img_size'])))

        save_path = os.path.join(output_dir, f'{image_name}_gradcam.png')
        visualize_and_save(img_np, cam_resized, save_path, 'Grad-CAM',
                           pred_class, confidence, CONFIG['class_names'])

    elif visualization_mode == 'occlusion':
        print("Generating Occlusion Sensitivity map...")
        sensitivity = occlusion_sensitivity(model, img_tensor, pred_class, patch_size=20, stride=10)

        save_path = os.path.join(output_dir, f'{image_name}_occlusion.png')
        visualize_and_save(img_np, sensitivity, save_path, 'Occlusion Sensitivity',
                           pred_class, confidence, CONFIG['class_names'])

    else:
        save_path = os.path.join(output_dir, f'{image_name}_prediction.png')
        save_simple_prediction(img_np, pred_class, confidence, save_path, CONFIG['class_names'])

    print(f"Results saved to: {save_path}")

    return pred_class, confidence, probabilities[0].cpu().numpy()


def detect_ensemble(image_path, model_configs, device, output_dir, ensemble_type):
    """Detect using ensemble of models"""
    print(f"\n{'='*70}")
    print(f"ENSEMBLE DETECTION - {ensemble_type}")
    print(f"{'='*70}")

    all_predictions = []
    all_confidences = []
    all_probabilities = []

    for model_name, model_path, vis_mode in model_configs:
        print(f"\n--- Model: {model_name} ---")
        pred, conf, probs = detect_single_model(
            image_path, model_path, model_name, device,
            os.path.join(output_dir, 'individual_models'), vis_mode
        )
        all_predictions.append(pred)
        all_confidences.append(conf)
        all_probabilities.append(probs)

    # Ensemble voting
    all_probabilities = np.array(all_probabilities)
    avg_probabilities = all_probabilities.mean(axis=0)
    ensemble_pred = avg_probabilities.argmax()
    ensemble_conf = avg_probabilities[ensemble_pred]

    # Voting analysis
    votes = np.bincount(all_predictions, minlength=2)

    print(f"\n{'='*70}")
    print("ENSEMBLE RESULTS")
    print(f"{'='*70}")
    print(f"Individual Predictions: {[CONFIG['class_names'][p] for p in all_predictions]}")
    print(f"Individual Confidences: {[f'{c:.2%}' for c in all_confidences]}")
    print(f"Vote Count - Normal: {votes[0]}, OSCC: {votes[1]}")
    print(f"Ensemble Prediction: {CONFIG['class_names'][ensemble_pred]}")
    print(f"Ensemble Confidence: {ensemble_conf:.2%}")
    print(f"{'='*70}")

    # Save ensemble visualization
    img_pil = Image.open(image_path).convert('RGB')
    img_np = np.array(img_pil.resize((CONFIG['img_size'], CONFIG['img_size']))) / 255.0
    image_name = os.path.splitext(os.path.basename(image_path))[0]

    # Create ensemble result visualization
    fig = plt.figure(figsize=(14, 8))

    # Original Image
    plt.subplot(2, 3, 1)
    plt.imshow(img_np)
    plt.title('Input Image', fontsize=12, fontweight='bold')
    plt.axis('off')

    # Individual predictions
    for idx, (pred, conf) in enumerate(zip(all_predictions, all_confidences)):
        plt.subplot(2, 3, idx + 2)
        plt.text(0.5, 0.6, f'Model {idx+1}:', ha='center', va='center', fontsize=10, fontweight='bold')
        plt.text(0.5, 0.4, f'{CONFIG["class_names"][pred]}', ha='center', va='center',
                 fontsize=12, fontweight='bold', color='green' if pred == 0 else 'red')
        plt.text(0.5, 0.2, f'{conf:.2%}', ha='center', va='center', fontsize=10)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis('off')

    # Ensemble result
    plt.subplot(2, 3, 5)
    plt.text(0.5, 0.7, 'ENSEMBLE', ha='center', va='center', fontsize=12, fontweight='bold')
    plt.text(0.5, 0.5, f'{CONFIG["class_names"][ensemble_pred]}', ha='center', va='center',
             fontsize=16, fontweight='bold', color='green' if ensemble_pred == 0 else 'red')
    plt.text(0.5, 0.3, f'Confidence: {ensemble_conf:.2%}', ha='center', va='center', fontsize=11)
    plt.text(0.5, 0.1, f'Votes: {votes[ensemble_pred]}/{len(all_predictions)}',
             ha='center', va='center', fontsize=9)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.axis('off')

    # Probability distribution
    plt.subplot(2, 3, 6)
    x = np.arange(len(CONFIG['class_names']))
    plt.bar(x, avg_probabilities, color=['green', 'red'], alpha=0.7)
    plt.xlabel('Class', fontweight='bold')
    plt.ylabel('Probability', fontweight='bold')
    plt.title('Average Probabilities', fontweight='bold')
    plt.xticks(x, CONFIG['class_names'])
    plt.ylim(0, 1)

    plt.tight_layout()
    save_path = os.path.join(output_dir, f'{image_name}_ensemble_result.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\nEnsemble results saved to: {save_path}")

    # Save detailed report
    report_path = os.path.join(output_dir, f'{image_name}_ensemble_report.txt')
    with open(report_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write(f"ENSEMBLE DETECTION REPORT - {ensemble_type}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Image: {os.path.basename(image_path)}\n")
        f.write(f"Detection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=" * 70 + "\n")
        f.write("INDIVIDUAL MODEL RESULTS\n")
        f.write("=" * 70 + "\n")
        for idx, (model_name, _, vis_mode) in enumerate(model_configs):
            f.write(f"\nModel {idx+1}: {model_name}\n")
            f.write(f"  Prediction: {CONFIG['class_names'][all_predictions[idx]]}\n")
            f.write(f"  Confidence: {all_confidences[idx]:.4f}\n")
            f.write(f"  Probabilities: Normal={all_probabilities[idx][0]:.4f}, OSCC={all_probabilities[idx][1]:.4f}\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("ENSEMBLE RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Vote Count: Normal={votes[0]}, OSCC={votes[1]}\n")
        f.write(f"Average Probabilities: Normal={avg_probabilities[0]:.4f}, OSCC={avg_probabilities[1]:.4f}\n")
        f.write(f"Final Prediction: {CONFIG['class_names'][ensemble_pred]}\n")
        f.write(f"Ensemble Confidence: {ensemble_conf:.4f}\n")
        f.write("=" * 70 + "\n")

    print(f"Detailed report saved to: {report_path}")

    return ensemble_pred, ensemble_conf


def main():
    print("=" * 70)
    print("ORAL CANCER DETECTION SYSTEM")
    print("=" * 70)
    print("\nSelect detection option:")
    print("1.  InceptionResNetV2")
    print("2.  XceptionNet")
    print("3.  EfficientNetB3")
    print("4.  InceptionResNetV2 with Grad-CAM")
    print("5.  InceptionResNetV2 with Occlusion Sensitivity")
    print("6.  XceptionNet with Grad-CAM")
    print("7.  XceptionNet with Occlusion Sensitivity")
    print("8.  EfficientNetB3 with Grad-CAM")
    print("9.  EfficientNetB3 with Occlusion Sensitivity")
    print("10. Ensemble Learning (Option 1 + 2 + 3)")
    print("11. Ensemble Learning (Option 4 + 6 + 8 - All Grad-CAM)")
    print("12. Ensemble Learning (Option 5 + 7 + 9 - All Occlusion)")
    print("=" * 70)

    choice = input("\nEnter your choice (1-12): ").strip()

    # Get image path
    image_path = input("Enter the path to the image: ").strip()

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nUsing device: {device}")

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_path = CONFIG['models_base_dir']

    try:
        if choice == '1':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_InceptionResNetV2_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"])
            detect_single_model(image_path, model_path, "InceptionResNetV2", device, output_dir)

        elif choice == '2':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_XceptionNet_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["XceptionNet"])
            detect_single_model(image_path, model_path, "XceptionNet", device, output_dir)

        elif choice == '3':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_EfficientNetB3_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["EfficientNetB3"])
            detect_single_model(image_path, model_path, "EfficientNetB3", device, output_dir)

        elif choice == '4':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_InceptionResNetV2_gradcam_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"])
            detect_single_model(image_path, model_path, "InceptionResNetV2", device, output_dir, 'gradcam')

        elif choice == '5':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_InceptionResNetV2_occlusion_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"])
            detect_single_model(image_path, model_path, "InceptionResNetV2", device, output_dir, 'occlusion')

        elif choice == '6':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_XceptionNet_gradcam_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["XceptionNet"])
            detect_single_model(image_path, model_path, "XceptionNet", device, output_dir, 'gradcam')

        elif choice == '7':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_XceptionNet_occlusion_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["XceptionNet"])
            detect_single_model(image_path, model_path, "XceptionNet", device, output_dir, 'occlusion')

        elif choice == '8':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_EfficientNetB3_gradcam_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["EfficientNetB3"])
            detect_single_model(image_path, model_path, "EfficientNetB3", device, output_dir, 'gradcam')

        elif choice == '9':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_EfficientNetB3_occlusion_{timestamp}")
            model_path = os.path.join(base_path, MODEL_PATHS["EfficientNetB3"])
            detect_single_model(image_path, model_path, "EfficientNetB3", device, output_dir, 'occlusion')

        elif choice == '10':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_ensemble_basic_{timestamp}")
            model_configs = [
                ("InceptionResNetV2", os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"]), None),
                ("XceptionNet", os.path.join(base_path, MODEL_PATHS["XceptionNet"]), None),
                ("EfficientNetB3", os.path.join(base_path, MODEL_PATHS["EfficientNetB3"]), None)
            ]
            detect_ensemble(image_path, model_configs, device, output_dir, "Basic Models")

        elif choice == '11':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_ensemble_gradcam_{timestamp}")
            model_configs = [
                ("InceptionResNetV2", os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"]), 'gradcam'),
                ("XceptionNet", os.path.join(base_path, MODEL_PATHS["XceptionNet"]), 'gradcam'),
                ("EfficientNetB3", os.path.join(base_path, MODEL_PATHS["EfficientNetB3"]), 'gradcam')
            ]
            detect_ensemble(image_path, model_configs, device, output_dir, "Grad-CAM Models")

        elif choice == '12':
            output_dir = os.path.join(CONFIG['output_dir'], f"detection_ensemble_occlusion_{timestamp}")
            model_configs = [
                ("InceptionResNetV2", os.path.join(base_path, MODEL_PATHS["InceptionResNetV2"]), 'occlusion'),
                ("XceptionNet", os.path.join(base_path, MODEL_PATHS["XceptionNet"]), 'occlusion'),
                ("EfficientNetB3", os.path.join(base_path, MODEL_PATHS["EfficientNetB3"]), 'occlusion')
            ]
            detect_ensemble(image_path, model_configs, device, output_dir, "Occlusion Sensitivity Models")

        else:
            print("Invalid choice! Exiting...")
            return

        print(f"\n{'='*70}")
        print("DETECTION COMPLETED SUCCESSFULLY!")
        print(f"{'='*70}")

    except FileNotFoundError as e:
        print(f"\n{'='*70}")
        print("ERROR: Model file not found!")
        print(f"{'='*70}")
        print(f"\n{str(e)}")
        print("\nPlease update the MODEL_PATHS in the CONFIG section with your actual trained model paths.")
        print("The paths should point to the 'best_model.pth' files in your training output folders.")

    except Exception as e:
        print(f"\n{'='*70}")
        print("ERROR OCCURRED!")
        print(f"{'='*70}")
        print(f"\n{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()