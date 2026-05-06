# debug_services.py
from app.core.hash_norm import tokenize

phrase = 'Gin Hendrick’s'
if __name__ == "__main__":
    print(tokenize(phrase))