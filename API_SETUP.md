# EdgeOptimizer - Cloud API Setup

## Setting up OpenAI API for Real Cloud Inference

### 1. Get OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the generated key (starts with `sk-...`)

### 2. Configure the API Key

**Option A: Direct Configuration**
Edit `configs/experiment_config.json` and replace:
```json
"cloud_api_key": "your-openai-api-key-here"
```
with:
```json
"cloud_api_key": "sk-your-actual-api-key-here"
```

**Option B: Environment Variable (Recommended)**
1. Set environment variable: `export OPENAI_API_KEY="sk-your-actual-api-key-here"`
2. The code will automatically use this if no key is set in config

### 3. Test Configuration
Run the experiment to test both local and cloud inference:
```bash
python experiments/power_comparison_working.py
```

### 4. Switch Between Real and Mock API
In `configs/experiment_config.json`:
- For real API calls: `"use_mock_cloud": false`
- For mock responses: `"use_mock_cloud": true`

### API Usage Notes
- OpenAI API charges per token
- The experiment uses `gpt-3.5-turbo` by default (cheaper than GPT-4)
- Max tokens is set to 50 to minimize costs during testing
- Monitor your usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)

### Troubleshooting
- **401 Unauthorized**: Check your API key
- **429 Rate Limited**: You've hit rate limits, try again later
- **Quota Exceeded**: Add billing info to your OpenAI account
- **Network Error**: Check internet connection
