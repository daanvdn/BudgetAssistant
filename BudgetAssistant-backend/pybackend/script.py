import random

def pick_random_month_for_quarter(quarter_nr:int):
    if quarter_nr == 1:
        return random.choice([1,2,3])
    elif quarter_nr == 2:
        return random.choice([4,5,6])
    elif quarter_nr == 3:
        return random.choice([7,8,9])
    elif quarter_nr == 4:
        return random.choice([10,11,12])

#pick_random_month_for_quarter(xl("D2"))
def pick_random_day(month:int):
    import random
    if month == 2:
        return random.choice([x for x in range(1,29)])
    elif month in [4,6,9,11]:
        return random.choice([x for x in range(1,31)])
    else:
        return random.choice([x for x in range(1,32)])

pick_random_day(xl("E2"))


if __name__ == '__main__':
    pass