print(-1)
from nltk.corpus import wordnet
from app.core.utils.morphology3 import get_lemma, get_synonym_leader
import nltk

words = ['зеленая', 'трава', 'травушка', 'скакун', 'конь', 'погоны', 'эполеты', 'виннная', 'green',
         'horses', 'porto', 'fortified', 'wine']
data = ('Pale straw in color with delicate greenish highlights. '
        'Intense lemon citrus fruit with floral and flinty notes on the nose, '
        'Medium bodie, with apple and more citrus fruits on the palate as well '
        'as notes of almonds and hazelnuts. The finish is crisp, refreshing and long. '
        'Бледно-соломенный цвет с нежными зеленоватыми бликами. Интенсивный цитрусовый, лимонный, '
        'фруктовый аромат с цветочными и кремниевыми нотками. Среднетелое, с яблоком и большим количеством '
        'цитрусовых во вкусе, а так же нотами миндаля и фундука. Послевкусие свежее, освежающее и продолжительное.')
words = data.split()

print(0)
# Проверка WordNet
print("WordNet:", wordnet.synsets('dog')[0].definition())
try:
    nltk.data.find('corpora/omw-1.4')
    print("OMW 1.4: найдена")
except LookupError:
    print("OMW 1.4: не найдена")


if __name__ == "__main__":
    result = list(set([get_lemma(word) for word in words if get_lemma(word)]))
    print(len(result), result)
    for word in result:
        print(f'{word}: {get_synonym_leader(word)}')