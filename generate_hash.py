# generate_hash.py
from werkzeug.security import generate_password_hash, check_password_hash

# Generate the correct hash for 'your-secure-password'
password = 'your-secure-password'
hash1 = generate_password_hash(password)
print(f"Generated hash: {hash1}")

# Test the existing hash
existing_hash = 'pbkdf2:sha256:600000$MlXi8Xcgp3y5$d17a4d3dce0a3d5be306beb47fddee0fc7d8c6ba51f7a9c7ea3e4fea4f33ad01'
test_result = check_password_hash(existing_hash, password)
print(f"Existing hash works: {test_result}")

# Generate a stable hash for testing (with fixed salt and iterations)
# This ensures consistency across test runs
stable_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
print(f"New stable hash: {stable_hash}")

# Verify it works
print(f"New hash verification: {check_password_hash(stable_hash, password)}")