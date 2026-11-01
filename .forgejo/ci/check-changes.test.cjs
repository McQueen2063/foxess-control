const test = require('node:test');
const assert = require('node:assert/strict');
const { fullTestsNeeded, checkMetadata } = require('./check-changes.cjs');

const manifest = {
  version: '1.0.23', domain: 'foxess_control', config_flow: true,
  documentation: 'https://github.com/McQueen2063/foxess-control',
  issue_tracker: 'https://github.com/McQueen2063/foxess-control/issues',
  codeowners: ['@McQueen2063'], requirements: ['wasmtime>=29.0.0'],
};
const current = JSON.stringify(manifest);
const previous = JSON.stringify({ ...manifest, version: '1.0.22' });

test('release-only changes skip full tests', () => {
  assert.equal(fullTestsNeeded([
    'README.md', 'docs/FORK_RELEASE.md', 'tests/test_fork_release.py',
    'custom_components/foxess_control/manifest.json',
  ], previous, current), false);
});

test('CI gate changes are checked by this fast suite', () => {
  assert.equal(fullTestsNeeded([
    '.forgejo/workflows/test.yml', '.forgejo/ci/check-changes.cjs',
    '.forgejo/ci/check-changes.test.cjs',
  ], previous, current), false);
});

test('runtime, dependencies, simulator, HA tests and unknown files require full tests', () => {
  for (const path of [
    'custom_components/foxess_control/_services.py', 'pyproject.toml',
    'Dockerfile.ci', 'Dockerfile.e2e-ci', 'simulator/server.py',
    'tests/e2e/ha_client.py', 'tests/test_services.py',
    'custom_components/foxess_control/translations/en.json', 'unknown.txt',
  ]) assert.equal(fullTestsNeeded([path], previous, current), true, path);
  assert.equal(fullTestsNeeded([], previous, current), true);
});

test('manifest changes other than version require full tests', () => {
  const changed = JSON.stringify({ ...manifest, requirements: ['wasmtime>=30'] });
  assert.equal(fullTestsNeeded(['custom_components/foxess_control/manifest.json'], previous, changed), true);
  assert.equal(fullTestsNeeded(['custom_components/foxess_control/manifest.json'], 'invalid', current), true);
});

test('metadata permits same or increasing versions and checks identity/changelog', () => {
  const changelog = '# Changelog\n\n## 1.0.23\n';
  const releaseTest = 'assert manifest["version"] == "1.0.23"';
  checkMetadata(current, changelog, releaseTest, previous);
  checkMetadata(current, changelog, releaseTest, current);
  assert.throws(() => checkMetadata(current, '', releaseTest, previous));
  assert.throws(() => checkMetadata(current, changelog, '', previous));
  assert.throws(() => checkMetadata(current, changelog, releaseTest,
    JSON.stringify({ ...manifest, version: '1.0.24' })));
  assert.throws(() => checkMetadata(JSON.stringify({ ...manifest, domain: 'changed' }),
    changelog, releaseTest, previous));
});
