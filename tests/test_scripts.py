"""Behavior checks: temporary Git repositories and fake SCP; no real hosts."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'

class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / 'tracked file.txt').write_text('initial')
        self.git('add', '.')
        self.git('commit', '-qm', 'initial')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'scp.jsonl'
        fake = self.bin / 'scp'
        fake.write_text('#!/usr/bin/env python3\nimport os,sys,json\nwith open(os.environ["SCP_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\nsys.exit(int(os.environ.get("SCP_FAIL","0")))\n')
        fake.chmod(0o755)
        self.env.update(PATH=str(self.bin) + os.pathsep + self.env['PATH'], SCP_LOG=str(self.log))

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, env=self.env, stderr=subprocess.STDOUT, text=True).strip()

    def run_script(self, name, *args, ok=True):
        r = subprocess.run(['bash', str(SCRIPTS / name), *args], cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=10)
        if ok: self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        else: self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def feature(self, name):
        self.git('switch', '-c', name)
        (self.repo / 'feature.txt').write_text(name)
        self.git('add', '.')
        self.git('commit', '-qm', name)
        self.git('switch', 'main')

    def merged_feature(self):
        self.feature('feature/merged')
        self.git('merge', '--no-ff', '-m', 'merge', 'feature/merged')

    def options(self):
        return ('--host', 'test@example.invalid', '--remote-root', '/remote/project dir')

    def calls(self):
        return [json.loads(s) for s in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_explicit_valid_base_required(self):
        self.run_script('clean_branches.sh', ok=False)
        self.run_script('clean_branches.sh', '--base', 'missing', ok=False)

    def test_dry_run_preserves_merged_and_unmerged(self):
        self.merged_feature()
        self.feature('feature/unmerged')
        before = self.git('for-each-ref', 'refs/heads')
        r = self.run_script('clean_branches.sh', '--base', 'main')
        self.assertIn('Would delete merged branch: feature/merged', r.stdout)
        self.assertEqual(before, self.git('for-each-ref', 'refs/heads'))

    def test_apply_preserves_unmerged_and_other_prefixes(self):
        self.merged_feature()
        self.feature('feature/unmerged')
        self.git('branch', 'other-feature/keep')
        self.run_script('clean_branches.sh', '--base', 'main', '--apply')
        branches = self.git('branch', '--format=%(refname:short)').splitlines()
        self.assertNotIn('feature/merged', branches)
        self.assertIn('feature/unmerged', branches)
        self.assertIn('other-feature/keep', branches)

    def test_current_branch_and_equivalent_base_preserved(self):
        self.git('switch', '-c', 'feature/current')
        self.git('branch', 'feature/same-base')
        self.run_script('clean_branches.sh', '--base', 'main', '--apply')
        self.assertEqual(self.git('branch', '--show-current'), 'feature/current')
        self.git('show-ref', '--verify', 'refs/heads/feature/same-base')

    def test_linked_worktree_branch_refused(self):
        self.merged_feature()
        self.git('worktree', 'add', str(self.root / 'linked'), 'feature/merged')
        self.run_script('clean_branches.sh', '--base', 'main', '--apply', ok=False)
        self.git('show-ref', '--verify', 'refs/heads/feature/merged')

    def test_detached_head_dry_run(self):
        self.merged_feature()
        self.git('switch', '--detach')
        self.run_script('clean_branches.sh', '--base', 'main')
        self.git('show-ref', '--verify', 'refs/heads/feature/merged')

    def test_transfers_require_configuration_and_valid_port(self):
        for script in ['push_to_vps.sh', 'pull_migrations.sh']:
            self.run_script(script, ok=False)
            self.run_script(script, *self.options(), '--port', '0', ok=False)
        self.assertEqual(self.calls(), [])

    def test_push_preview_no_connection(self):
        (self.repo / 'tracked file.txt').write_text('changed')
        r = self.run_script('push_to_vps.sh', *self.options())
        self.assertIn('tracked file.txt', r.stdout)
        self.assertEqual(self.calls(), [])

    def test_push_spaces_untracked_rename_and_deletion(self):
        self.git('mv', 'tracked file.txt', 'renamed file.txt')
        (self.repo / 'untracked file.txt').write_text('new')
        self.run_script('push_to_vps.sh', *self.options(), '--apply')
        self.assertEqual({c[-2] for c in self.calls()}, {'./renamed file.txt', './untracked file.txt'})
        self.log.unlink()
        self.git('add', '.')
        self.git('commit', '-qm', 'renamed')
        (self.repo / 'renamed file.txt').unlink()
        self.run_script('push_to_vps.sh', *self.options(), '--apply')
        self.assertEqual(self.calls(), [])

    def test_push_symlink_refused_before_connection(self):
        (self.repo / 'link').symlink_to('/etc/hostname')
        self.run_script('push_to_vps.sh', *self.options(), '--apply', ok=False)
        self.assertEqual(self.calls(), [])

    def test_copy_failure_is_reported(self):
        (self.repo / 'tracked file.txt').write_text('changed')
        self.env['SCP_FAIL'] = '7'
        r = self.run_script('push_to_vps.sh', *self.options(), '--apply', ok=False)
        self.assertEqual(r.returncode, 7)
        self.assertNotIn('Transferred', r.stdout)

    def test_pull_preview_and_failure(self):
        (self.repo / 'my app' / 'migrations').mkdir(parents=True)
        self.run_script('pull_migrations.sh', *self.options())
        self.assertEqual(self.calls(), [])
        self.env['SCP_FAIL'] = '8'
        r = self.run_script('pull_migrations.sh', *self.options(), '--apply', ok=False)
        self.assertEqual(r.returncode, 8)
        self.assertEqual(self.calls()[0][-1], './my app/migrations/')
        self.assertNotIn('Transferred', r.stdout)

if __name__ == '__main__':
    unittest.main()
