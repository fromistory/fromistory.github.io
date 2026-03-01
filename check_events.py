import re
from twitter_utils import get_events_dict

if __name__ == '__main__':
    with open('raw/test.txt', encoding='utf-8') as f:
        data = f.read()

    # Use regex to find all occurrences of a 6-digit date followed by tab
    # and capture everything until the next date (non-greedy)
    # pattern = re.compile(r'(\d{6})\t(.*?)(?=(\n\d{6}\t)|$)', re.DOTALL)

    # events = pattern.findall(data)

    # Convert to a clean list of (date, description)
    # clean_events = [(date, desc.replace('\n', ' ').strip()) for date, desc, _ in events]

    clean_events =[d.split(' ', maxsplit=1) for d in data.split('\n')]

    by_date = dict()

    by_name = dict()

    # Print results
    for date, desc in clean_events:
        by_date.setdefault(date, set())
        by_date[date].add(desc)

        by_name.setdefault(desc, set())
        by_name[desc].add(date)

    by_date = dict(sorted(by_date.items()))

    total_events = 0
    for k, vs in by_date.items():
        print(k, vs)
        total_events += len(vs)


    print(len(by_date), total_events)
    curr = get_events_dict(False)
    # events_by_date = dict()
    # for d, e in curr.items():
    #     events_by_date.setdefault(d, [])
    #     events_by_date[d].append(e)
    #
    # for d, e in events_by_date.items():
    #     print(d, len(e))

    set_a = set({x for v in by_date.values() for x in v})

    set_b = set()
    for d, xs in curr.items():
        for x in xs:
            set_b.add(x['Eng Name'])
    # set_b = set([x['Eng Name'] for d, x in curr.items()])

    diff = set_a - set_b
    for d in diff:
        print(by_name[d], d)
    #
    #
    # print(len(diff))

    # set([c['Date'] for c in curr])



    for d, vs in by_date.items():
        if d not in curr:
            print('Missing ', d, vs)
        elif len(vs) > len(curr[d]):
            print('Count mismatch', d, len(curr[d]), len(vs), vs)
