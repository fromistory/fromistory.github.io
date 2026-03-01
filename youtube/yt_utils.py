import os.path

import pandas as pd

def get_events():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRPT5wfb1Eh7r7RqGXJNtXeUhbAlokMvIiZdB6PdAQZoRb4JkwCy5Lw4XylvAwnsr7lmVbqPdPrVsMO/pub?gid=1556948653&single=true&output=tsv'

    df = pd.read_csv(url, sep='\t', header=0)
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")

def cleanup():
    events = get_events()
    for e in events:
        if e['Category'] == 'Fan Sign' and int(e['Date']) < 220500:
            path = f'json/{e['Date']}.json'
            if os.path.exists(path):
                print('Delete file', f'json/{e['Date']}.json')
                os.remove(path)

if __name__ == '__main__':
    cleanup()