# 🦷 Oral Cancer Detection System

An AI/ML-based web application developed using Django to support preliminary oral cancer screening through image-based prediction and symptom assessment.

## 📌 Project Overview

Oral cancer can be difficult to identify in its early stages. This project explores how machine learning and web technologies can help users assess potential warning signs and access oral health information.

**Disclaimer:** This project is for educational and research purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.

## ✨ Features

* **Image-Based Prediction:** Uses a trained machine learning model to analyze submitted images.
* **Symptom Assessment:** Provides a symptom-based assessment.
* **User Management:** Supports application user accounts.
* **Admin Management:** Provides administrative functionality.
* **Oral Health Information:** Helps users learn about oral cancer.
* **Web Interface:** Built using Django templates and frontend technologies.

## 🛠️ Technologies Used

* Python
* Django
* Machine Learning
* HTML, CSS and JavaScript
* MySQL
* Pickle for model storage

## 📂 Project Structure

```text
oral-cancer-detection/
├── manage.py
├── myapp/
├── oralcancer/
├── templates/
├── static/
├── train.py
├── prediction.py
├── new_code_train.py
├── oral_cancer_model.pkl
└── README.md
```

*Note: The structure above highlights key project files and directories.*

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Nan-gif18/oral-cancer-detection.git
cd oral-cancer-detection
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

If the repository contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise, install the dependencies listed in your project configuration.

### 4. Configure the database

Configure your local MySQL database and the required environment variables in accordance with the Django settings.

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## 🔬 Machine Learning Model

The project includes a trained model saved as `oral_cancer_model.pkl`. The training and prediction scripts are included in the repository.

Prediction quality depends on the training data and model evaluation. Clinical validation would be required before using this system for medical decisions.

## 🔮 Future Improvements

* Improve model accuracy and evaluate performance on independent datasets.
* Enhance the user interface and accessibility.
* Add comprehensive model evaluation metrics.
* Strengthen security and deployment configuration.
* Obtain appropriate clinical validation.

## 👩‍💻 Author

**Nandhana**

GitHub: [Nan-gif18](https://github.com/Nan-gif18)

---

If you find this project useful, consider starring the repository!
