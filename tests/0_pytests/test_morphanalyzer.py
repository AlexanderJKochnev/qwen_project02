from nltk.corpus import wordnet
from app.core.utils.morphology3 import get_lemma
import nltk
words = ['зеленая', 'трава', 'травушка', 'скакун', 'конь', 'погоны', 'эполеты', 'виннная', 'green',
         'horses', 'porto', 'fortified', 'wine']
data = 'Pale straw in color with delicate greenish highlights. Intense lemon citrus fruit with floral and flinty notes on the nose, Medium bodie, with apple and more citrus fruits on the palate as well as notes of almonds and hazelnuts. The finish is crisp, refreshing and long.'
words = data.split()


# Проверка WordNet
print("WordNet:", wordnet.synsets('dog')[0].definition())
try:
    nltk.data.find('corpora/omw-1.4')
    print("OMW 1.4: найдена")
except LookupError:
    print("OMW 1.4: не найдена")





if __name__ == "__main__":
    print(1)
    for word in words:
        print(get_lemma(word))
