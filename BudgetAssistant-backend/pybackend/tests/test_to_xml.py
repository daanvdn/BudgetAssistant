import xml.etree.ElementTree as ET

def do_convert_to_xml(text):
    entries = text.strip().split('\n\n')
    root = ET.Element('root')

    for entry_text in entries:
        lines = entry_text.strip().split('\n')
        month = lines[0].strip()
        expenses = []
        revenue = []

        i = 1
        while i < len(lines):
            if lines[i].strip() == 'EXPENSES':
                i += 1
                while i < len(lines) and lines[i].strip() != 'REVENUE':
                    expenses.append(lines[i].strip())
                    i += 1
            elif lines[i].strip() == 'REVENUE':
                i += 1
                while i < len(lines) and not lines[i].strip().isdigit():
                    revenue.append(lines[i].strip())
                    i += 1

        entry = ET.SubElement(root, 'entry')
        month_elem = ET.SubElement(entry, 'month')
        month_elem.text = month

        if expenses:
            expenses_elem = ET.SubElement(entry, 'expenses')
            expenses_elem.text = 'category;amount\n' + '\n'.join(expenses)

        if revenue:
            revenue_elem = ET.SubElement(entry, 'revenue')
            revenue_elem.text = 'category;amount\n' + '\n'.join(revenue)

    return ET.tostring(root, encoding='unicode')

def test():
    # Example usage
    text = """11_2023
REVENUE
e_REVENUE 54

12_2022
EXPENSES
c_EXPENSES -19
REVENUE
c_REVENUE 19

12_2023
REVENUE
e_REVENUE 20

2_2023
REVENUE
c_REVENUE 12

3_2022
EXPENSES
a_EXPENSES -3
REVENUE
a_REVENUE 1

3_2023
EXPENSES
c_EXPENSES -23

4_2022
EXPENSES
a_EXPENSES -4
REVENUE
a_REVENUE 3

5_2022
EXPENSES
a_EXPENSES -3

5_2023
REVENUE
d_REVENUE 14

6_2022
REVENUE
a_REVENUE 4

6_2023
EXPENSES
d_EXPENSES -27
REVENUE
d_REVENUE 13

7_2022
REVENUE
b_REVENUE 5

7_2023
EXPENSES
d_EXPENSES -15

8_2022
EXPENSES
b_EXPENSES -5

8_2023
REVENUE
d_REVENUE 15

9_2022
EXPENSES
b_EXPENSES -6
REVENUE
b_REVENUE 6

9_2023
EXPENSES
d_EXPENSES -16
REVENUE
d_REVENUE 16
"""

    xml_output = do_convert_to_xml(text)
    print(xml_output)

