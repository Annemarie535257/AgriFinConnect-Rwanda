# AgriFinConnect-Rwanda

A comprehensive machine learning project for agricultural financial services in Rwanda, featuring loan approval prediction and multilingual chatbot support.

## 📋 Project Overview

This repository contains two main machine learning models:

1. **Loan Approval Classifier** - Predicts loan approval/rejection based on applicant features
2. **Multilingual Loan Chatbot** - AI chatbot that provides loan application guidance in English, Kinyarwanda, and French

## 📊 Datasets

### 1. Loan Approval Dataset

**Source:** [Hugging Face - mariosyahirhalimm/loan_prediction_dataset](https://huggingface.co/datasets/mariosyahirhalimm/loan_prediction_dataset)

- **Dataset Name:** `mariosyahirhalimm/loan_prediction_dataset`
- **Size:** 614 samples
- **Features:** 13 columns including:
  - Applicant demographics (Gender, Married, Dependents, Education, Self_Employed)
  - Financial information (ApplicantIncome, CoapplicantIncome, LoanAmount, Loan_Amount_Term)
  - Credit information (Credit_History, Property_Area)
  - Target: Loan_Status (Approved/Rejected)

**Usage:**
```python
from datasets import load_dataset
ds = load_dataset("mariosyahirhalimm/loan_prediction_dataset")
```

### 2. Bitext Mortgage/Loans Chatbot Dataset

**Source:** Local CSV file (`Bitext-mortgage-loans-llm-chatbot-training-dataset/bitext-mortgage-loans-llm-chatbot-training-dataset.csv`)

- **Dataset Name:** Bitext Mortgage Loans LLM Chatbot Training Dataset
- **Size:** ~37,778 rows (English)
- **Format:** CSV with columns:
  - `system_prompt` - System instructions
  - `instruction` - User queries/questions
  - `response` - Assistant responses
  - `intent` - Query intent classification
  - `category` - Query category
  - `tags` - Additional tags

**Note:** This dataset is translated to Kinyarwanda and French using NLLB (No Language Left Behind) model during training, creating a multilingual dataset with ~113,334 total samples (37,778 × 3 languages).

## 🤖 Algorithms & Models

### 1. Loan Approval Model (`train_loan_approval_model.ipynb`)

#### Primary Algorithm: **Random Forest Classifier**
- **Library:** scikit-learn
- **Model:** `RandomForestClassifier`
- **Hyperparameters:**
  - `n_estimators`: 100 (number of decision trees)
  - `max_depth`: 10
  - `random_state`: 42
- **Performance:** ~83.7% accuracy on validation set
- **Training Method:** Ensemble learning with 100 decision trees

#### Alternative Algorithm: **XGBoost Classifier**
- **Library:** XGBoost
- **Model:** `XGBClassifier`
- **Hyperparameters:**
  - `n_estimators`: 100 (number of boosting rounds)
  - `max_depth`: 6
  - `random_state`: 42
  - `eval_metric`: "logloss"
- **Performance:** ~80.5% accuracy on validation set
- **Training Method:** Gradient boosting with 100 boosting rounds

**Note:** Both algorithms use `n_estimators` (number of trees/boosting rounds), not epochs. The models train all trees/rounds in a single pass.

**Preprocessing:**
- Label encoding for categorical variables
- Standard scaling for numerical features
- Missing value imputation (median for numeric, mode for categorical)
- Outlier handling using IQR method

### 2. Multilingual Chatbot (`train_agrifinconnect_chatbot.ipynb`)

#### Base Model: **Llama 3.2 3B Instruct**
- **Model:** `meta-llama/Llama-3.2-3B-Instruct`
- **Source:** [Hugging Face - Meta Llama 3.2 3B Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- **License:** Requires Meta license acceptance
- **Architecture:** Transformer-based causal language model
- **Parameters:** 3 billion

#### Fine-tuning Method: **LoRA (Low-Rank Adaptation) / PEFT**
- **Library:** PEFT (Parameter-Efficient Fine-Tuning)
- **Method:** LoRA with 4-bit quantization
- **LoRA Configuration:**
  - `r`: 16 (rank)
  - `lora_alpha`: 32
  - `lora_dropout`: 0.05
  - `target_modules`: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
- **Quantization:** 4-bit (BitsAndBytesConfig) for memory efficiency
- **Training Hyperparameters:**
  - `epochs`: 2
  - `learning_rate`: 2e-5
  - `max_seq_length`: 1024
  - `batch_size`: 2 (per device)
  - `gradient_accumulation_steps`: 4
  - `fp16`: True

#### Translation Model: **NLLB (No Language Left Behind)**
- **Model:** `facebook/nllb-200-distilled-600M`
- **Source:** [Hugging Face - NLLB 200](https://huggingface.co/facebook/nllb-200-distilled-600M)
- **Purpose:** Translates English dataset to Kinyarwanda (`kin_Latn`) and French (`fra_Latn`)
- **Languages Supported:** 200+ languages
- **Architecture:** Sequence-to-sequence transformer

## 🚀 Setup

### Prerequisites
- Python 3.9+
- Jupyter Notebook
- GPU recommended for chatbot training (optional for loan approval model)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Annemarie535257/AgriFinConnect-Rwanda.git
cd AgriFinConnect-Rwanda
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Additional Setup for Chatbot Training

1. **Hugging Face Account:**
   - Create an account at [Hugging Face](https://huggingface.co/)
   - Accept Meta's Llama license at [Llama 3.2 3B Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
   - Login via CLI:
   ```bash
   huggingface-cli login
   ```

2. **Dataset:**
   - Ensure the Bitext dataset CSV file is in the `Bitext-mortgage-loans-llm-chatbot-training-dataset/` directory

## 📁 Project Structure

```
AgriFinConnect-Rwanda/
├── train_loan_approval_model.ipynb      # Loan approval classifier training
├── train_agrifinconnect_chatbot.ipynb   # Multilingual chatbot training
├── loan_approval_model/                 # Saved model artifacts
│   ├── loan_classifier.joblib
│   ├── label_encoder.joblib
│   ├── scaler.joblib
│   └── feature_columns.joblib
├── Bitext-mortgage-loans-llm-chatbot-training-dataset/
│   └── bitext-mortgage-loans-llm-chatbot-training-dataset.csv
├── requirements.txt                      # Python dependencies
└── README.md                            # This file
```

## 📝 Usage

### Loan Approval Model

1. Open `train_loan_approval_model.ipynb`
2. Run all cells sequentially
3. The model will be saved in `loan_approval_model/` directory
4. Use the saved model for predictions on new loan applications

### Multilingual Chatbot

1. Open `train_agrifinconnect_chatbot.ipynb`
2. Ensure you're logged into Hugging Face
3. Run all cells sequentially
4. The fine-tuned model will be saved in `agrifinconnect-loan-chatbot/` directory
5. Use the model for multilingual loan application support

## 🔧 Key Features

### Loan Approval Model
- ✅ Data cleaning and preprocessing
- ✅ Comprehensive visualizations
- ✅ Multiple algorithm support (Random Forest, XGBoost)
- ✅ Confusion matrix visualization
- ✅ Feature importance analysis
- ✅ Model testing with sample predictions

### Multilingual Chatbot
- ✅ Supports 3 languages (English, Kinyarwanda, French)
- ✅ Automatic translation using NLLB
- ✅ Efficient fine-tuning with LoRA
- ✅ 4-bit quantization for memory efficiency
- ✅ Chat format compatible with Llama 3.2

## 📚 Dependencies

See `requirements.txt` for the complete list. Key packages include:

- **Loan Approval Model:**
  - `scikit-learn` - Machine learning algorithms
  - `xgboost` - Gradient boosting
  - `pandas` - Data manipulation
  - `matplotlib`, `seaborn` - Visualizations
  - `datasets` - Hugging Face datasets

- **Chatbot Model:**
  - `transformers` - Hugging Face transformers
  - `peft` - Parameter-efficient fine-tuning
  - `bitsandbytes` - Quantization
  - `accelerate` - Training acceleration
  - `torch` - PyTorch

## 📄 License

Please check individual model licenses:
- **Llama 3.2:** Requires Meta license acceptance
- **NLLB:** Check Facebook/Meta license terms
- **Other models:** Check respective Hugging Face model cards

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Note:** This project is part of the AgriFinConnect initiative for agricultural financial services in Rwanda.

