import re
from typing import List, Union, Optional
from pymorphy3 import MorphAnalyzer
from pymorphy3.analyzer import Parse
from transliterate import translit

NUMBERS = """0,ноль,нулевой
1,один,первый
2,два,второй
3,три,третий
4,четыре,четвертый
5,пять,пятый
6,шесть,шестой
7,семь,седьмой
8,восемь,восьмой
9,девять,девятый
10,десять,десятый
11,одиннадцать,одиннадцатый
12,двенадцать,двенадцатый
13,тринадцать,тринадцатый
14,четырнадцать,четырнадцатый
15,пятнадцать,пятнадцатый
16,шестнадцать,шестнадцатый
17,семнадцать,семнадцатый
18,восемнадцать,восемнадцатый
19,девятнадцать,девятнадцатый
20,двадцать,двадцатый
30,тридцать,тридцатый
40,сорок,сороковой
50,пятьдесят,пятидесятый
60,шестьдесят,шестидесятый
70,семьдесят,семидесятый
80,восемьдесят,восьмидесятый
90,девяносто,девяностый
100,сто,сотый
200,двести,двухсотый
300,триста,трехсотый
400,четыреста,четырехсотый
500,пятьсот,пятисотый
600,шестьсот,шестисотый
700,семьсот,семисотый
800,восемьсот,восьмисотый
900,девятьсот,девятисотый
1000,тысяча,тысячный
1000000,миллион,миллионный"""

class MorphNumber:
    def __init__(self):
        self.morph = MorphAnalyzer()

        # создаём словарь из чисел и порядковых числительных
        self.dict = {}
        for i in NUMBERS.split("\n"):
            x, card, ord_ = i.split(",")
            self.dict[int(x)] = card
            self.dict[card] = ord_

    def parse(self, word: str) -> Parse:
        words: List[Parse] = self.morph.parse(word)
        for word in words:
            if word.tag.case == "nomn":
                return word
        return words[0]

    def integer_to_words(self, integer: int, text: str = None) -> list[str]:
        if integer < 0:
            return ["минус"] + self.integer_to_words(-integer, text)

        if integer == 0:
            return ["ноль"]

        if text:
            last_word = text.rsplit(" ", 1)[-1]
            tag = self.parse(last_word).tag
        else:
            tag = None

        hundred = 0
        ten = 0
        words = []

        k = len(str(integer)) - 1
        for digit in str(integer):
            digit = int(digit)

            if k % 3 == 2:
                if digit > 0:
                    words.append(self.dict[digit * 100])
                hundred = digit

            elif k % 3 == 1:
                if digit > 1:
                    words.append(self.dict[digit * 10])
                ten = digit

            else:
                if ten == 1:
                    digit += 10

                if digit > 0:
                    if k == 3 and digit <= 2:
                        w: Parse = self.parse(self.dict[digit])
                        w = w.inflect({"femn"})
                        words.append(w.word if w else self.dict[digit])

                    elif k == 0 and digit <= 2 and tag:
                        w: Parse = self.parse(self.dict[digit])
                        w = w.inflect({tag.gender, tag.case})
                        words.append(w.word if w else self.dict[digit])
                    else:
                        words.append(self.dict.get(digit, str(digit)))

                if k > 2 and (hundred or ten or digit):
                    w2: Parse = self.parse(self.dict.get(10**k, "тысяча" if k==3 else "миллион"))
                    w2 = w2.make_agree_with_number(digit)
                    words.append(w2.word if w2 else "тысяч")

            k -= 1

        return words

    def words_after_number(self, number: int, text: str) -> list[str]:
        number = abs(number)
        words = []
        for word in text.split(" "):
            w: Parse = self.parse(word)
            grammemes = w.tag.numeral_agreement_grammemes(number)
            if grammemes == {"sing", "accs"}:
                grammemes = {"sing", w.tag.case}
            if w_inf := w.inflect(grammemes):
                words.append(w_inf.word)
            else:
                words.append(word)
        return words

    def float_to_words(self, integer: int, decimal: int, decsize: int) -> list[str]:
        words = self.integer_to_words(integer, "часть")
        words += ["целая" if self.first(integer) else "целых"]
        words += ["и"]
        words += self.integer_to_words(decimal, "часть")
        if decsize == 1:
            words += ["десятая" if self.first(decimal) else "десятых"]
        elif decsize == 2:
            words += ["сотая" if self.first(decimal) else "сотых"]
        elif decsize == 3:
            words += ["тысячная" if self.first(decimal) else "тысячных"]
        return words

    def first(self, integer: int) -> bool:
        return (integer % 10 == 1) and (integer % 100 != 11)

    def preprocess_text(self, text: str) -> str:
        """
        Find patterns like '5 минут' or '22.5 градуса' and replace with morphed words.
        """
        # Find [float/int] [space] [Russian word]
        pattern = re.compile(r'(\d+[.,]\d+|\d+)\s+([а-яА-ЯёЁ]+)')
        
        def replace_match(match):
            val_str = match.group(1).replace(",", ".")
            noun = match.group(2)
            
            if "." in val_str:
                parts = val_str.split(".")
                integer = int(parts[0])
                decimal = int(parts[1])
                decsize = len(parts[1])
                num_words = self.float_to_words(integer, decimal, decsize)
                # After float, noun is usually in genitive singular (e.g. 1.1 градуса)
                # but "words_after_number" with fixed 2 usually handles it well in Russian
                morphed_noun = self.words_after_number(2, noun) 
            else:
                number = int(val_str)
                num_words = self.integer_to_words(number, noun)
                morphed_noun = self.words_after_number(number, noun)
            
            return " ".join(num_words + morphed_noun)
        
        text = pattern.sub(replace_match, text)

        # Transliterate Latin to Cyrillic
        # This helps Silero RU models read English words or names if they are written in Latin
        text = translit(text, 'ru')
        
        return text

# Global instance
MORPH_PROCESSOR = MorphNumber()

def apply_morphology(text: str) -> str:
    return MORPH_PROCESSOR.preprocess_text(text)
