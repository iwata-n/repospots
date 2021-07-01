import argparse
import json
from logging import debug
from git.cmd import Git

def _log(message):
    global debug
    if debug:
        print(message)

def analyze_member(result_files, all_files, member):
    '''
    memberだけがコミットしているファイル一覧
    '''
    _log(f'analyze_member {member}')
    r = []

    for path in all_files:
        _log(path)
        # 現在の管理対象外であれば無視
        if path not in result_files:
            _log(f'skip {path}')
            continue

        data = result_files[path]
        authors = data['authors']

        if not all([a in member for a in authors]):
            _log(f'skip {path} {authors}')
            continue

        r.append(data)

    s = sorted(r, key=lambda x: x['commit_count'], reverse=True)
    return [(x['commit_count'], x['path'], x['authors']) for x in s]


parser = argparse.ArgumentParser(description='analyze git repo.')
parser.add_argument('result', default='result.json', type=str, help='repospots result file')
parser.add_argument('--member', nargs='+', default=[], dest='member', action='append', type=str)
parser.add_argument('--debug', '-d', action='store_true')
args = parser.parse_args()

debug = args.debug

with open(args.result) as f:
    result = json.load(f)

g = Git(result['parameter']['path'])

ls_files = g.ls_files().split("\n")
all_files = filter(lambda x: x != ".", ls_files)

result_files = result['result']['files']

_log(f"head={result['result']['head']}")
member = sum(args.member, [])
for m in member:
    _log(f"member={m}")

r = analyze_member(result_files, all_files, member)
print('commit_count, path, authors')
for x in r:
    print(f"{x[0]},{x[1]},{' '.join(x[2])}")