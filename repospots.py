import argparse
from git.objects.commit import Commit
import yaml
import json
import fnmatch
from git import Repo, config

def parse_repo(path, branch, depth, exclude, large_commit_lines):
    repo = Repo(path)

    commits = repo.iter_commits(branch, max_count=depth)

    authors = dict()
    files = dict()
    total_commits = 0
    large_commit = list()

    for commit in commits:
        # マージコミットは無視する
        if len(commit.parents) > 1:
            continue

        total_commits += 1

        author = commit.author.name

        if author in authors:
            authors[author] += 1
        else:
            authors[author] = 1

        if commit.stats.total['lines'] > large_commit_lines:
            large_commit.append({'hash': commit.hexsha, 'total': commit.stats.total})

        for file in commit.stats.files:
            if any([fnmatch.fnmatch(file, e) for e in exclude]):
                continue

            if file in files:
                f = files[file]
                f['commit_hash'].append(commit.hexsha)
                f['authored_datetime'].append(commit.authored_datetime.strftime("%Y/%m/%d %H:%M:%S"))
                if author in f['author']:
                    f['author'][author] += 1
                else:
                    f['author'][author] = 1
                f['commit_count'] += 1
                f['author_count'] = len(f['author'])
                files[file] = f
            else:
                files[file] = {
                    'authored_datetime': [commit.authored_datetime.strftime("%Y/%m/%d %H:%M:%S")],
                    'author': {
                        author: 1
                    },
                    'author_count': 1,
                    'commit_count': 1,
                    'commit_hash': [commit.hexsha]
                }

    print(large_commit)

    return total_commits, files, authors

def load_config(path):
    with open(path, 'r') as yml:
        config = yaml.safe_load(yml)
    return config

def argument():
    parser = argparse.ArgumentParser(description='Find bugspot in git repo.')
    parser.add_argument('path', default='./', type=str, help='repository path')
    parser.add_argument('--branch', default='master', dest='branch', type=str)
    parser.add_argument('--depth', default=None, dest='depth', type=int)
    parser.add_argument('--exclude', nargs='+', default=[], dest='exclude', action='append', type=str)
    parser.add_argument('--top', default=-1, dest='top', type=int)
    parser.add_argument('--member', nargs='+', dest='member', default=[], action='append', type=str)
    parser.add_argument('--config', dest='config', default='', type=str)
    parser.add_argument('--show-summary', dest='show_summary', default=True, type=bool)

    return parser.parse_args()

def print_summary(result):
    print("summary")
    print(f" total commits={result['total_commits']}")
    print(f" total files={result['total_files']}")
    print(f" authors={result['authors']}")
    print('')

def print_order_by_number_of_authors(files, top):
    print(f"Order by number of authors. top:{top}")
    change_authors = sorted(files.items(), key = lambda x: len(x[1]['author']), reverse=True)
    for k in change_authors[0:top]:
        a = k[1]['author']
        print(f" {k[0]} author_count={len(a)} {a}")
    print('')

def print_order_by_change_count(files, top):
    print(f"Order by change count top{top}")
    change_count = sorted(files.items(), key = lambda x: x[1]['change_count'], reverse=True)
    for k in change_count[0:top]:
        print(f" {k[0]} count={k[1]['change_count']}")
    print('')

def print_no_employee(files, employee):
    d = {x[0]: list(x[1]['author'].keys()) for x in files.items()}
    filter_list = filter(lambda x: not all(y in employee for y in x[1]), d.items())
    for i in filter_list:
        print(i)

def calc_risk(file):
    len(file['authors'])

def only_one_author(files):
    return filter(lambda x: len(x[1]['author']) == 1 and x[1]['change_count'] > 1, files.items())

def main():
    args = argument()
    path = args.path
    branch = args.branch
    depth = args.depth
    top = args.top
    exclude = sum(args.exclude, [])
    member = sum(args.member, [])

    if args.config:
        config = load_config(args.config)
        branch = config['parse']['branch']
        depth = config['parse']['depth']
        large_commit_lines = config['parse']['large_commit_lines']
        top = config['output']['top']
        exclude = config['parse']['file']['exclude']
        member = config['parse']['member']

    parameter = {
        'path': path,
        'branch': branch,
        'depth': depth,
        'large_commit_lines': large_commit_lines,
        'top': top,
        'exclude': exclude,
        'member': member
    }

    print("config")
    print(f" path={path}")
    print(f" branch={branch}")
    print(f" depth={depth}")
    print(f" top={top}")
    print(f" exclude={exclude}")
    print(f" member={member}")
    print('')

    total_commits, files, authors = parse_repo(path, branch, depth, exclude, large_commit_lines)
    result_files = calc_risk(files)

    result = {
        'total_commits': total_commits,
        'total_files': len(files),
        'authors': list(authors.keys()),
        'files': result_files,
    }

    # print_summary(result)
    # print_order_by_number_of_authors(files, top)
    # print_order_by_change_count(files, top)
    # print_no_employee(files, employee)
    # for r in ranking:
    #     print(r)

    # o = only_one_author(files)
    # a = filter(lambda x: 'iwata-n' in x[1]['author'], o)
    # print(json.dumps(list(a), sort_keys=True, indent=2))

    print(json.dumps({'parameter': parameter, 'result': result}, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()


