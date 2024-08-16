# EigenScore

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/circle-dot/eigenscore.git
cd eigenscore
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Application

```bash
uvicorn app.main:app --reload
```

### 5. Access the API

Open your browser and go to: `http://127.0.0.1:8000/rankings`
