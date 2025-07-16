## ⚙️ Setup

### 1. Create and activate a virtual environment
For Windows:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```
For macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Install ntlk
Run this in venv
```bash
import nltk                         
nltk.download('wordnet')   
nltk.download('omw-1.4')
```

### Environment Configuration
Create a .env file in the root directory and fill in your AWS credentials:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-southeast-2
```