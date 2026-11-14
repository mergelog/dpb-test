#!/usr/bin/env python3
"""Validate the examples and exercise the official updater without creating PRs."""

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / '.github/dependabot.examples.yml.disabled'
SCHEMA_COMMIT = 'e2606e03284e60792672dc9e7e930f3c496c5c3d'
SCHEMA_URL = (
    'https://raw.githubusercontent.com/SchemaStore/schemastore/'
    + SCHEMA_COMMIT + '/src/schemas/json/dependabot-2.0.json'
)
TARGETS = {
    '@angular/compiler': '20.3.35', '@angular/core': '20.3.35',
    'rxjs': '7.8.2', 'tslib': '2.9.1', 'typescript': '5.9.3',
}
CASES = [
    'all', 'split', 'patch', 'ignored-version', 'production',
    'lockfile-pinned', 'lockfile-range', 'increase-if-necessary',
    'cooldown-excluded', 'actions', 'security', 'directories',
]


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f'duplicate YAML key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def parse(text):
    return yaml.load(text, Loader=UniqueLoader)


def comment_fragment(document, lines):
    """Parse literal commented examples instead of retyping their values."""
    uncommented = []
    for line in lines:
        assert line in document, f'commented example missing: {line}'
        uncommented.append(line.replace('# ', '', 1))
    return parse('\n'.join(uncommented))


def configurations():
    text = EXAMPLES.read_text()
    documents = text.split('\n---\n')
    configs = list(yaml.load_all(text, Loader=UniqueLoader))
    assert len(configs) == 9
    variants = {}

    def variant(name, number, lines):
        config = copy.deepcopy(configs[number - 1])
        config['updates'][0].update(comment_fragment(documents[number - 1], lines))
        variants[name] = config

    variant('cooldown-excluded', 1, [
        '    # cooldown:', '    #   default-days: 7', '    #   exclude: ["*"]',
    ])
    # The ignore fragment is a list item, so it is appended to the existing rules.
    ignored = copy.deepcopy(configs[2])
    ignored['updates'][0]['ignore'] += comment_fragment(documents[2], [
        '      # - dependency-name: "rxjs"', '      #   versions: ["7.8.2"]',
    ])
    variants['ignored-version'] = ignored
    variant('production', 3, ['    # allow:', '    #   - dependency-type: "production"'])
    variant('increase-if-necessary', 4, ['    # versioning-strategy: "increase-if-necessary"'])
    variant('manual-rebase', 4, ['    # rebase-strategy: "disabled"'])
    variant('target-branch', 9, ['    # target-branch: "dependency-testing"'])

    active_text = (ROOT / '.github/dependabot.yml').read_text()
    all_group = parse('\n'.join(
        line.replace('# ', '', 1)
        for line in active_text.splitlines()
        if line.startswith(('    # groups:', '    #   all-dependencies:',
                            '    #     patterns:', '    #       - "*"'))
    ))
    assert all_group['groups']['all-dependencies']['patterns'] == ['*']
    active_variant = parse(active_text)
    active_variant['updates'][0].update(all_group)
    variants['active-all-group'] = active_variant
    return configs, variants


def validate(output):
    configs, variants = configurations()
    with urllib.request.urlopen(SCHEMA_URL) as response:
        schema = json.load(response)
    validator = jsonschema.Draft7Validator(schema)
    checks = [(f'case-{i + 1}', config) for i, config in enumerate(configs)]
    checks += list(variants.items())
    checks.append(('active', parse((ROOT / '.github/dependabot.yml').read_text())))
    for name, config in checks:
        errors = list(validator.iter_errors(config))
        if errors:
            raise AssertionError(f'{name}: ' + '; '.join(error.message for error in errors))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'schema-validation.json').write_text(json.dumps({
        'schema_commit': SCHEMA_COMMIT, 'validated': [name for name, _ in checks],
        'scope': 'YAML and SchemaStore schema; not GitHub scheduling or repository settings',
    }, indent=2) + '\n')
    print(f'Validated {len(checks)} configurations, including literal commented variants.')


def fixture(path, ranges=False):
    path.mkdir(parents=True)
    package = {
        'name': 'dependabot-verification-fixture', 'version': '1.0.0', 'private': True,
        'dependencies': {'@angular/compiler': '20.3.34', '@angular/core': '20.3.34', 'rxjs': '7.8.1'},
        'devDependencies': {'tslib': '2.8.1', 'typescript': '5.9.2'},
    }
    (path / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    subprocess.run(['npm', 'install', '--package-lock-only', '--ignore-scripts', '--no-audit', '--no-fund'],
                   cwd=path, check=True, stdout=subprocess.DEVNULL)
    if ranges:
        for section in ['dependencies', 'devDependencies']:
            package[section] = {name: '^' + value for name, value in package[section].items()}
        (path / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
        lock = json.loads((path / 'package-lock.json').read_text())
        for section in ['dependencies', 'devDependencies']:
            lock['packages'][''][section] = package[section]
        (path / 'package-lock.json').write_text(json.dumps(lock, indent=2) + '\n')


def job_for(config):
    update = config['updates'][0]
    source = {
        'provider': 'github', 'repo': 'mergelog/dpb-test',
        'commit': os.environ.get('GITHUB_SHA') or subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    }
    source['directories' if 'directories' in update else 'directory'] = update.get('directories', update.get('directory', '/'))
    job = {
        'package-manager': {'npm': 'npm_and_yarn', 'github-actions': 'github_actions'}[update['package-ecosystem']],
        'source': source,
        'allowed-updates': update.get('allow', [{'dependency-type': 'direct', 'update-type': 'all'}]),
        'ignore-conditions': [], 'existing-pull-requests': [], 'existing-group-pull-requests': [],
        'dependency-groups': [],
    }
    for rule in update.get('ignore', []):
        for version in rule.get('versions', [None]):
            condition = {'dependency-name': rule['dependency-name']}
            if version:
                condition['version-requirement'] = version
            if 'update-types' in rule:
                condition['update-types'] = rule['update-types']
            job['ignore-conditions'].append(condition)
    # Bound the public-registry fixtures so future releases cannot change expectations.
    for name, target in TARGETS.items():
        job['ignore-conditions'].append({'dependency-name': name, 'version-requirement': '>' + target})
    for name, rules in update.get('groups', {}).items():
        rules = copy.deepcopy(rules)
        job['dependency-groups'].append({
            'name': name, 'applies-to': rules.pop('applies-to', 'version-updates'), 'rules': rules,
        })
    if 'cooldown' in update:
        job['cooldown'] = update['cooldown']
    if 'exclude-paths' in update:
        job['exclude-paths'] = update['exclude-paths']
    strategy = update.get('versioning-strategy')
    if strategy == 'lockfile-only':
        job['lockfile-only'] = True
    elif strategy:
        job['requirements-update-strategy'] = {
            'increase': 'bump_versions',
            'increase-if-necessary': 'bump_versions_if_necessary',
            'widen': 'widen_ranges',
        }[strategy]
    if 'commit-message' in update:
        message = update['commit-message']
        job['commit-message-options'] = {'prefix': message.get('prefix', ''),
                                         'include-scope': message.get('include') == 'scope'}
    return {'job': job}


def run_case(name, output, cli):
    configs, variants = configurations()
    index = {'all': 0, 'split': 1, 'patch': 2, 'lockfile-pinned': 3, 'lockfile-range': 3,
             'actions': 4, 'security': 5, 'directories': 6}
    config = copy.deepcopy(variants[name] if name in variants else configs[index[name]])
    directory = output / name
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / 'source'
    if source.exists():
        shutil.rmtree(source)
    if name == 'actions':
        workflow = source / '.github/workflows/fixture.yml'
        workflow.parent.mkdir(parents=True)
        workflow.write_text('name: Fixture\non: push\njobs:\n  fixture:\n    runs-on: ubuntu-latest\n    steps:\n'
                            '      - uses: actions/checkout@v4.1.0\n'
                            '      - uses: actions/upload-artifact@v4.6.0\n')
    elif name == 'directories':
        fixture(source / 'apps/web')
        fixture(source / 'packages/shared')
        fixture(source / 'apps/web/fixtures/ignored')
    else:
        fixture(source, ranges=name in ['lockfile-range', 'increase-if-necessary'])
    data = job_for(config)
    if name == 'security':
        # Synthetic advisories exercise grouped security logic; these are not real vulnerability claims.
        data['job'].update({
            'security-updates-only': True, 'dependencies': ['rxjs', 'typescript'],
            'security-advisories': [{'dependency-name': package, 'affected-versions': ['<' + TARGETS[package]],
                                     'patched-versions': [], 'unaffected-versions': []}
                                    for package in ['rxjs', 'typescript']],
        })
    (directory / 'job.json').write_text(json.dumps(data, indent=2) + '\n')
    result_file = directory / 'result.yml'
    command = [cli, 'update', '-f', str(directory / 'job.json'), '--local', str(source),
               '-o', str(result_file), '--timeout', '12m']
    print('Running official updater:', name, flush=True)
    with (directory / 'run.log').open('w') as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    log_text = (directory / 'run.log').read_text()
    print('\n'.join(log_text.splitlines()[-35:]), flush=True)
    assert completed.returncode == 0, f'{name}: CLI exited {completed.returncode}'
    result = parse(result_file.read_text())
    calls = result.get('output', [])
    errors = [call for call in calls if call['type'] in ['record_update_job_error', 'record_unknown_update_job_error']]
    assert not errors, errors
    prs = [call['expect']['data'] for call in calls if call['type'] == 'create_pull_request']
    names = {dependency['name'] for pr in prs for dependency in pr.get('dependencies', [])}
    summary = {'case': name, 'created_pr_count': len(prs), 'dependencies': sorted(names),
               'scope': 'official updater dry-run; no real pull requests are created'}
    (directory / 'observed.json').write_text(json.dumps(summary, indent=2) + '\n')
    if name in ['all', 'cooldown-excluded']:
        assert len(prs) == 1 and names == set(TARGETS), summary
    elif name == 'split':
        assert len(prs) == 3 and names == set(TARGETS), summary
        groups = [set(dep['name'] for dep in pr['dependencies']) for pr in prs]
        assert {'@angular/core', '@angular/compiler'} in groups, summary
        assert {'rxjs'} in groups and {'typescript', 'tslib'} in groups, summary
    elif name in ['patch', 'ignored-version', 'production']:
        expected = {'@angular/core', '@angular/compiler', 'rxjs', 'typescript'}
        if name == 'ignored-version':
            expected.remove('rxjs')
        if name == 'production':
            expected.remove('typescript')
        assert names == expected, summary
    elif name == 'lockfile-pinned':
        assert not prs, summary
    elif name in ['lockfile-range', 'increase-if-necessary']:
        assert names, summary
        for pr in prs:
            assert all(file['name'] == 'package-lock.json' for file in pr['updated-dependency-files']), pr.keys()
    elif name == 'actions':
        assert len(prs) == 1 and names == {'actions/checkout', 'actions/upload-artifact'}, summary
    elif name == 'security':
        assert len(prs) == 1 and names == {'rxjs', 'typescript'}, summary
    elif name == 'directories':
        assert names == set(TARGETS), summary
        assert 'fixtures/ignored/package' not in json.dumps(prs), 'excluded fixture was updated'
    (directory / 'passed.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('PASS:', json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--output', type=Path, default=ROOT / 'out/dependabot-verification')
    parser.add_argument('--cli', default='dependabot')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.validate:
        validate(output)
    if args.case:
        run_case(args.case, output, args.cli)


if __name__ == '__main__':
    main()
