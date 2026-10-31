# Shared deployment workflows

## Line endings

Repositories using these workflows include a root `.gitattributes` file that marks PHP, workflow, shell, PowerShell, JSON, and YAML files as text with LF line endings. This keeps diffs stable across Windows and Linux checkouts and prevents CRLF-only changes from appearing in deployment commits. Existing files are normalized when their repository next performs a deliberate renormalization; future checkouts and edits use LF.

## SSH connection variables

Set `DEPLOY_HOST`, `DEPLOY_USER`, and `DEPLOY_PORT` under **Settings → Secrets and variables → Actions → Variables** in the calling repository, or as organization variables available to that repository. Each variable overrides only its corresponding connection setting. Missing or empty variables fall back to the workflow's existing host, user, and port; reusable workflows fall back to their inputs or each `deployments_json` mapping, with port `22` when no port is supplied.

For example, a caller with an existing destination can use:

```yaml
deploy_host: ${{ vars.DEPLOY_HOST || 'example.com' }}
deploy_user: ${{ vars.DEPLOY_USER || 'deploy' }}
deploy_port: ${{ vars.DEPLOY_PORT || '22' }}
```

The application workflows resolve variables before calling their currently pinned reusable workflow versions. The shared workflows also support variables directly when called at a revision containing this change. For multi-directory workflows, the variables apply to every mapping; unset variables preserve the individual mapping values. Caller JSON uses `toJSON` to encode variable values safely.

The manual actions in this repository and `kasb-center` accept optional SSH host, user, and port inputs as fallbacks for these variables. Supply a host and user either through variables or through the manual inputs. SSH authentication still uses `SERVER_SSH_KEY` and `SERVER_KNOWN_HOSTS` secrets.

## Deploy a selected branch or commit

Use `.github/workflows/deploy-ref-rsync.yml@v1.5.0` to deploy a branch, tag, or full commit SHA from the calling repository. It snapshots the live server to the `snapshot` branch before deploying, uses the same concurrency group as the standard single-directory deployment, and returns the resolved commit as the `deployed_sha` output and in the run summary. An invalid ref or missing source directory fails before accessing the server.

Add this manual workflow to the application repository's default branch, replacing the example server and directory settings:

```yaml
name: Deploy selected commit
run-name: Deploy ${{ inputs.deploy_ref }}

on:
  workflow_dispatch:
    inputs:
      deploy_ref:
        description: Branch, tag, or full commit SHA to deploy
        required: true
        type: string

permissions:
  contents: write

jobs:
  deploy:
    uses: hamidrg-deployments/deployment-workflows/.github/workflows/deploy-ref-rsync.yml@v1.5.0
    with:
      deploy_ref: ${{ inputs.deploy_ref }}
      deploy_host: ${{ vars.DEPLOY_HOST || 'example.com' }}
      deploy_port: ${{ vars.DEPLOY_PORT || '22' }}
      deploy_user: ${{ vars.DEPLOY_USER || 'deploy' }}
      deploy_path: /srv/application
      source_path: application
    secrets:
      ssh_private_key: ${{ secrets.SERVER_SSH_KEY }}
      ssh_known_hosts: ${{ secrets.SERVER_KNOWN_HOSTS }}
```

In **Actions → Deploy selected commit → Run workflow**, keep the workflow branch set to the default branch and enter the revision to deploy in `deploy_ref`. For a particular commit on any branch, supply its full SHA. For the current tip of a branch, supply its branch name, such as `feature/example`; use `refs/heads/feature/example` to disambiguate a branch from a tag with the same name.

The workflow resolves the requested revision once and uses that checkout throughout deployment. It does not execute application scripts. Like the standard deployment, rsync preserves destination-only files and excludes `.git/` and `.env`. Other configuration files already tracked in the selected revision are included in deployment; select a revision appropriate for the target server.

## Multiple deployment directories

Use `deploy-ref-multiple-rsync.yml@v1.5.0` with `deploy_ref` and the same `deployments_json` mappings as `deploy-multiple-rsync.yml`. All source directories are validated before connecting to the server; all live directories are snapshotted before deploying any of them. The selected commit is used for every mapping and returned as `deployed_sha`.

## Repositories without a configured target

The manual `Deploy selected commit` action in this repository and `kasb-center` requires the source subdirectory and destination directory at run time. Set the SSH connection variables above or supply the fallback SSH inputs, and configure `SERVER_SSH_KEY` and `SERVER_KNOWN_HOSTS` with access to that destination before running it. Repositories with existing deployment mappings retain those mappings in their own manual actions.

Sources must be subdirectories within the selected checkout. Git submodules are not deployed by these workflows; deploy their source repositories directly. In particular, the `kasb-center` integration repository's `backend`, `api`, and `cms` directories are submodules.
