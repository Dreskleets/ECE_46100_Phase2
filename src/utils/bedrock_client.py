"""
Bedrock client for LLM-based metric analysis.
Uses caching to avoid redundant API calls.
"""
import hashlib
import json
import os
import time
from pathlib import Path

try:
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

# Cache directory
CACHE_DIR = Path("/tmp/bedrock_cache")
CACHE_DIR.mkdir(exist_ok=True)

class BedrockClient:
    """Client for AWS Bedrock with caching support."""
    
    def __init__(self):
        self.client = None
        self.enabled = BEDROCK_AVAILABLE and self._check_credentials()
        
        if self.enabled:
            try:
                self.client = boto3.client(
                    'bedrock-runtime',
                    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
                )
            except Exception as e:
                print(f"DEBUG: Bedrock client init failed: {e}")
                self.enabled = False
    
    def _check_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        key_id = os.getenv('AWS_ACCESS_KEY_ID', '')
        secret = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        # Check that credentials exist and aren't placeholder values
        return bool(
            key_id and secret and
            not key_id.startswith('REPLACE') and
            not secret.startswith('REPLACE')
        )
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> dict | None:
        """Retrieve cached response if available and fresh."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cached = json.load(f)
                # Cache valid for 24 hours
                if time.time() - cached.get('timestamp', 0) < 86400:
                    return cached.get('response')
            except Exception:
                pass
        return None
    
    def _cache_response(self, cache_key: str, response: dict):
        """Cache a response."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'response': response
                }, f)
        except Exception:
            pass
    
    def analyze_readme_for_benchmarks(self, readme_text: str, timeout: int = 10) -> dict:
        """
        Analyze README for performance claims and benchmarks.
        
        Returns:
            dict with 'score' (float 0-1) and 'reason' (str)
        """
        # Check cache first
        cache_key = self._get_cache_key(f"benchmarks:{readme_text[:500]}")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        # Fallback if Bedrock not available
        if not self.enabled:
            return {"score": 0.6, "reason": "Bedrock not available, using fallback"}
        
        # Truncate README to save tokens (first 2000 chars usually sufficient)
        truncated = readme_text[:2000] if len(readme_text) > 2000 else readme_text
        
        # Security: Sanitize input to prevent prompt injection
        # Remove potential control sequences and escape braces
        truncated = truncated.replace("```", "")  # Remove code blocks that might close prompt
        truncated = truncated.replace("{{", "{").replace("}}", "}")  # Escape braces
        
        prompt = f"""Analyze this model README and score it 0.0-1.0 based on evidence of performance claims:

Scoring criteria:
- Benchmark results with numbers (0.4 points)
- Performance metrics like accuracy, F1, BLEU, perplexity (0.3 points)
- Comparisons with other models (0.2 points)
- Links to evaluation datasets or papers (0.1 points)

README excerpt:
{truncated}

Respond ONLY with valid JSON in this exact format:
{{"score": 0.0, "reason": "explanation"}}"""

        try:
            response = self.client.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "temperature": 0.1,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                })
            )
            
            result = json.loads(response['body'].read())
            text = result['content'][0]['text'].strip()
            
            # Parse JSON from response
            # Claude sometimes adds markdown, so extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            parsed = json.loads(text)
            
            # Validate and clamp score
            score = float(parsed.get('score', 0.6))
            score = max(0.0, min(1.0, score))
            
            result = {
                "score": score,
                "reason": parsed.get('reason', 'Bedrock analysis')
            }
            
            # Cache result
            self._cache_response(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"DEBUG: Bedrock API call failed: {e}")
            # Fallback to heuristic
            return {"score": 0.6, "reason": f"Bedrock failed: {str(e)[:100]}"}


# Global instance
_bedrock_client = None

def get_bedrock_client() -> BedrockClient:
    """Get or create global Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
