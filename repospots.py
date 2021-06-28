import argparse
import yaml
import fnmatch
from git import Repo, config

def parse_repo(path, branch, depth, exclude):
    repo = Repo(path)

    commits = repo.iter_commits(branch, max_count=depth)

    authors = dict()
    files = dict()
    total_commits = 0

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

        for file in commit.stats.files:
            if any([fnmatch.fnmatch(file, e) for e in exclude]):
                continue

            if file in files:
                files[file]['change_count'] += 1
                if author in files[file]['author']:
                    files[file]['author'][author] += 1
                else:
                    files[file]['author'][author] = 1
            else:
                files[file] = {'author': {author: 1}, 'change_count':1}

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
    parser.add_argument('--employee', nargs='+', dest='employee', default=[], action='append', type=str)
    parser.add_argument('--config', dest='config', default='', type=str)
    parser.add_argument('--show-summary', dest='show_summary', default=True, type=bool)

    return parser.parse_args()

def print_summary(total_commits, files, authors):
    print("summary")
    print(f" total commits={total_commits}")
    print(f" total files={len(files)}")
    print(f' authors={authors}')
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

def main():
    args = argument()
    path = args.path
    branch = args.branch
    depth = args.depth
    top = args.top
    exclude = sum(args.exclude, [])
    employee = sum(args.employee, [])

    if args.config:
        config = load_config(args.config)
        branch = config['parse']['branch']
        depth = config['parse']['depth']
        top = config['output']['top']
        exclude = config['parse']['file']['exclude']
        employee = config['parse']['employee']

    print("config")
    print(f" path={path}")
    print(f" branch={branch}")
    print(f" depth={depth}")
    print(f" top={top}")
    print(f" exclude={exclude}")
    print(f" employee={employee}")
    print('')

    total_commits, files, authors = parse_repo(path, branch, depth, exclude)

    print_summary(total_commits, files, authors)
    print_order_by_number_of_authors(files, top)
    print_order_by_change_count(files, top)
    #print_no_employee(files, employee)

if __name__ == '__main__':
    main()


