// Dependency-free checks: Node is already installed in the runner image.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');

const manifestPath = 'custom_components/foxess_control/manifest.json';
const metadataPaths = new Set([
  'tests/test_fork_release.py',
  '.forgejo/workflows/test.yml',
  '.forgejo/ci/check-changes.cjs',
  '.forgejo/ci/check-changes.test.cjs',
]);

function fullTestsNeeded(paths, previousManifest, currentManifest) {
  if (!paths.length) return true; // An uncertain/empty diff must not bypass tests.
  for (const path of paths) {
    if (path.endsWith('.md') || metadataPaths.has(path)) continue;
    if (path !== manifestPath) return true;
    try {
      const before = JSON.parse(previousManifest);
      const after = JSON.parse(currentManifest);
      delete before.version;
      delete after.version;
      assert.deepStrictEqual(before, after);
    } catch {
      return true;
    }
  }
  return false;
}

function versionParts(version) {
  assert.match(version, /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/);
  return version.split('.').map(BigInt);
}

function checkMetadata(manifestText, changelog, releaseTest, previousManifest) {
  const manifest = JSON.parse(manifestText);
  const current = versionParts(manifest.version);
  assert.equal(manifest.domain, 'foxess_control');
  assert.equal(manifest.config_flow, true);
  assert.equal(manifest.documentation, 'https://github.com/McQueen2063/foxess-control');
  assert.ok(manifest.issue_tracker.startsWith(`${manifest.documentation}/`));
  assert.deepStrictEqual(manifest.codeowners, ['@McQueen2063']);
  assert.ok(changelog.includes(`## ${manifest.version}\n`), 'Missing changelog heading');
  const expected = releaseTest.match(/manifest\["version"\]\s*==\s*"([^"]+)"/);
  assert.ok(expected, 'Missing explicit manifest version assertion');
  assert.equal(expected[1], manifest.version, 'Release test and manifest disagree');
  if (previousManifest) {
    const previous = versionParts(JSON.parse(previousManifest).version);
    const firstDifference = current.findIndex((part, index) => part !== previous[index]);
    assert.ok(firstDifference < 0 || current[firstDifference] > previous[firstDifference],
      'Release version must not decrease');
  }
}

function main() {
  const read = (path) => fs.readFileSync(path, 'utf8');
  const git = (...args) => execFileSync('git', args, { encoding: 'utf8' });
  const currentManifest = read(manifestPath);
  const base = process.env.BASE_SHA || '';
  let previousManifest;
  let full = true;
  // GitHub/Forgejo supplies a PR base or the pre-push commit. Use the merge
  // base for PRs so unrelated base-branch changes do not expand the diff.
  if (/^[0-9a-f]{40}$/.test(base) && !/^0+$/.test(base)) {
    try {
      const comparison = process.env.EVENT_NAME === 'pull_request'
        ? git('merge-base', base, 'HEAD').trim() : base;
      previousManifest = git('show', `${comparison}:${manifestPath}`);
      const paths = git('diff', '--no-renames', '--name-only', '-z', comparison, 'HEAD')
        .split('\0').filter(Boolean);
      full = fullTestsNeeded(paths, previousManifest, currentManifest);
      console.log(`Changed paths: ${JSON.stringify(paths)}`);
    } catch (error) {
      console.log(`Cannot establish safe metadata-only diff; running full tests: ${error.message}`);
    }
  }
  if (process.env.EVENT_NAME === 'workflow_dispatch') full = true;
  checkMetadata(currentManifest, read('CHANGELOG.md'), read('tests/test_fork_release.py'), previousManifest);
  console.log(full ? 'Full unit and HA lifecycle tests required.' : 'Metadata-only: Docker builds and HA lifecycle tests skipped.');
  fs.appendFileSync(process.env.GITHUB_OUTPUT, `full=${full}\n`);
}

module.exports = { fullTestsNeeded, checkMetadata };
if (require.main === module) main();
