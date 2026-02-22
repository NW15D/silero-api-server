import re
from typing import List, Union, Optional
from pymorphy3 import MorphAnalyzer
from pymorphy3.analyzer import Parse
from transliterate import translit

NUMBERS_RU = """0,ноль,нулевой
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

NUMBERS_UK = """0,нуль,нульовий
1,один,перший
2,два,другий
3,три,третій
4,чотири,четвертий
5,п'ять,п'ятий
6,шість,шостий
7,сім,сьомий
8,вісім,восьмий
9,дев'ять,дев'ятий
10,десять,десятий
11,одинадцять,одинадцятий
12,дванадцять,дванадцятий
13,тринадцять,тринадцятий
14,чотирнадцять,чотирнадцятий
15,п'ятнадцять,п'ятнадцятий
16,шістнадцять,шістнадцятий
17,сімнадцять,сімнадцятий
18,вісімнадцять,вісімнадцятий
19,дев'ятнадцять,дев'ятнадцятий
20,двадцять,двадцятий
30,тридцять,тридцятий
40,сорок,сороковий
50,п'ятдесят,п'ятдесятий
60,шістдесят,шістдесятий
70,сімдесят,сімдесятий
80,вісімдесят,вісімдесятий
90,дев'яносто,дев'яностий
100,сто,сотий
200,двісті,двохсотий
300,триста,трьохсотий
400,чотириста,чотирьохсотий
500,п'ятсот,п'ятисотий
600,шістсот,шестисотий
700,сімсот,семисотий
800,вісімсот,восьмисотий
900,дев'ятсот,дев'ятисотий
1000,тисяча,тисячний
1000000,мільйон,мільйонний"""

class MorphProcessor:
    def __init__(self, lang: str = "ru"):
        self.lang = lang
        self.morph = MorphAnalyzer(lang=lang)
        self.num_data = NUMBERS_RU if lang == "ru" else NUMBERS_UK
        self.dict = {}
        for i in self.num_data.split("\n"):
            x, card, ord_ = i.split(",")
            self.dict[int(x)] = card
            self.dict[card] = ord_
        
        # Gender mappings for feminine numbers (1 and 2)
        # RU: 1 (один -> одна), 2 (два -> две)
        # UK: 1 (один -> одна), 2 (два -> дві)
        self.fem_map = {1: "одна", 2: "две"} if lang == "ru" else {1: "одна", 2: "дві"}

    def parse(self, word: str) -> Parse:
        words: List[Parse] = self.morph.parse(word)
        for w in words:
            if w.tag.case == "nomn":
                return w
        return words[0]

    def integer_to_words(self, integer: int, text: str = None) -> list[str]:
        if integer < 0:
            minus = "мінус" if self.lang == "uk" else "минус"
            return [minus] + self.integer_to_words(-integer, text)

        if integer == 0:
            return [self.dict[0]]

        if text:
            last_word = text.rsplit(" ", 1)[-1]
            tag = self.parse(last_word).tag
        else:
            tag = None

        hundred = 0
        ten = 0
        words = []

        k = len(str(integer)) - 1
        for digit_char in str(integer):
            digit = int(digit_char)

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
                    # Thousands are feminine: одна тисяча, дві тисячі
                    if k == 3 and digit <= 2:
                        words.append(self.fem_map[digit])
                    # Agreement with noun gender: одна задача, дві задачі
                    elif k == 0 and digit <= 2 and tag:
                        if tag.gender == "femn":
                            words.append(self.fem_map[digit])
                        elif tag.gender == "neut" and digit == 1:
                            words.append("одно" if self.lang == "ru" else "одне")
                        else:
                            words.append(self.dict[digit])
                    else:
                        words.append(self.dict.get(digit, str(digit)))

                if k > 2 and (hundred or ten or digit or (k > 3 and integer // (10**k) % 1000 > 0)):
                    # Handle thousands, millions, etc.
                    # This logic is simplified; for large numbers it might need more work
                    base_val = 10**k
                    if base_val in self.dict:
                        w2: Parse = self.parse(self.dict[base_val])
                        # make_agree_with_number doesn't always work perfectly for UK in pymorphy3, 
                        # but it's the best we have.
                        w2 = w2.make_agree_with_number(digit)
                        words.append(w2.word if w2 else self.dict[base_val])

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
        # RU: пять целых и две десятых
        # UK: п'ять цілих і дві десятих
        cel_word = "цілих" if self.lang == "uk" else "целых"
        cel_one = "ціла" if self.lang == "uk" else "целая"
        i_word = "і" if self.lang == "uk" else "и"
        
        words = self.integer_to_words(integer, "частина" if self.lang == "uk" else "часть")
        words += [cel_one if self.first(integer) else cel_word]
        words += [i_word]
        words += self.integer_to_words(decimal, "частина" if self.lang == "uk" else "часть")
        
        if decsize == 1:
            suffix = "десята" if self.first(decimal) else "десятих"
            if self.lang == "ru": suffix = "десятая" if self.first(decimal) else "десятых"
            words += [suffix]
        elif decsize == 2:
            suffix = "сота" if self.first(decimal) else "сотих"
            if self.lang == "ru": suffix = "сотая" if self.first(decimal) else "сотых"
            words += [suffix]
        elif decsize == 3:
            suffix = "тисячна" if self.first(decimal) else "тисячних"
            if self.lang == "ru": suffix = "тысячная" if self.first(decimal) else "тысячных"
            words += [suffix]
        return words

    def first(self, integer: int) -> bool:
        return (integer % 10 == 1) and (integer % 100 != 11)

    def preprocess_text(self, text: str) -> str:
        # Find [float/int] [space] [Russian/Ukrainian word]
        pattern = re.compile(r'(\d+[.,]\d+|\d+)\s+([а-яА-ЯёЁіІїЇєЄґҐ]+)')
        
        def replace_match(match):
            val_str = match.group(1).replace(",", ".")
            noun = match.group(2)
            
            if "." in val_str:
                parts = val_str.split(".")
                integer = int(parts[0])
                decimal = int(parts[1])
                decsize = len(parts[1])
                num_words = self.float_to_words(integer, decimal, decsize)
                morphed_noun = self.words_after_number(2, noun) 
            else:
                number = int(val_str)
                num_words = self.integer_to_words(number, noun)
                morphed_noun = self.words_after_number(number, noun)
            
            return " ".join(num_words + morphed_noun)
        
        text = pattern.sub(replace_match, text)
        text = translit(text, self.lang)
        return text

# Instances
PROCESSORS = {
    "ru": MorphProcessor("ru"),
    "uk": MorphProcessor("uk")
}

def apply_morphology(text: str, lang_code: str = "ru") -> str:
    lang = "uk" if lang_code in ["ua", "uk"] else "ru"
    processor = PROCESSORS.get(lang, PROCESSORS["ru"])
    return processor.preprocess_text(text)
