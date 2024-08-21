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


---

## CronJob

1. **Replace `ACCESS_TOKEN`**: Substitute `ACCESS_TOKEN` with the current access token used in the `.env` file.

2. **Replace the Log File Path**: Update `"path/to/file/post_request.log"` with the actual path to the log file.

3. **Set Up the Cron Job**:
   - Open the crontab editor by running `crontab -e` on your machine.
   - Add the following line to schedule the cron job:
     ```bash
        0 * * * * ~/path/to/file/post_request.sh
     ```
     Replace path/to/file with the actual path to the file
4. **Save and Exit**: Save the changes and exit the editor to activate the cron job.

--- 
