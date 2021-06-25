import argparse
import fnmatch
from git import Repo

parser = argparse.ArgumentParser(description='Find bugspot in git repo.')
parser.add_argument('path', default='./', type=str,
                    help='repository path')
parser.add_argument('--branch', default='master', dest='branch', type=str)
parser.add_argument('--max_commit', default=None, dest='max_commit', type=int)
parser.add_argument('--exclude', nargs='+', dest='exclude', action='append', type=str)
parser.add_argument('--top', default=-1, dest='top', type=int)

args = parser.parse_args()

print(args)

exclude = sum(args.exclude, [])
path = args.path

print("path =", path)
print("exclude =", exclude)

repo = Repo(path)

commits = repo.iter_commits(args.branch, max_count=args.max_commit)

authors = dict()
files = dict()

for commit in commits:
    # マージコミットは無視する
    if len(commit.parents) > 1:
        continue

    author = commit.author.name

    if author in authors:
        authors[author] += 1
    else:
        authors[author] = 1

    for file in commit.stats.files:
        if any([fnmatch.fnmatch(file, e) for e in exclude]):
            continue
        if file in files:
            files[file]['change_count'] += 1
            if author in files[file]:
                files[file]['author'][author] += 1
            else:
                files[file]['author'][author] = 1
        else:
            files[file] = {'author': {author: 1}, 'change_count':1}

print("change authors top", args.top)
change_authors = sorted(files.items(), key = lambda x: len(x[1]['author']), reverse=True)
for k in change_authors[0:args.top]:
    a = k[1]['author']
    print(" ", k[0], 'author_count =', len(a), a)

print()
print("change count top", args.top)
change_count = sorted(files.items(), key = lambda x: x[1]['change_count'], reverse=True)
for k in change_count[0:args.top]:
    print(" ", k[0], 'count =', k[1]['change_count'])
