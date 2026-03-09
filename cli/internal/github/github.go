package github

import (
	"fmt"
	"os/exec"
	"strings"
)

// RunGH executes a gh CLI command and returns stdout.
func RunGH(args ...string) (string, error) {
	cmd := exec.Command("gh", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("gh %s: %s", strings.Join(args, " "), string(out))
	}
	return strings.TrimSpace(string(out)), nil
}

// CheckGHInstalled verifies that the gh CLI is installed and authenticated.
func CheckGHInstalled() error {
	_, err := exec.LookPath("gh")
	if err != nil {
		return fmt.Errorf("gh CLI not found. Install it from https://cli.github.com/")
	}
	_, err = RunGH("auth", "status")
	if err != nil {
		return fmt.Errorf("gh CLI not authenticated. Run: gh auth login")
	}
	return nil
}

// GetCurrentRepo returns the current repo in "owner/repo" format,
// derived from the origin remote URL rather than gh's parent resolution.
func GetCurrentRepo() (string, error) {
	cmd := exec.Command("git", "remote", "get-url", "origin")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("git remote get-url origin: %s", string(out))
	}
	url := strings.TrimSpace(string(out))
	// Handle both HTTPS and SSH URLs
	// https://github.com/owner/repo.git -> owner/repo
	// git@github.com:owner/repo.git -> owner/repo
	url = strings.TrimSuffix(url, ".git")
	if strings.Contains(url, "github.com/") {
		parts := strings.SplitN(url, "github.com/", 2)
		return parts[1], nil
	}
	if strings.Contains(url, "github.com:") {
		parts := strings.SplitN(url, "github.com:", 2)
		return parts[1], nil
	}
	return "", fmt.Errorf("could not parse GitHub repo from origin URL: %s", url)
}

// SetDefaultRepo sets the gh default repo for this directory.
func SetDefaultRepo(repo string) error {
	_, err := RunGH("repo", "set-default", repo)
	return err
}

// SetSecret sets a repository secret.
func SetSecret(repo, name, value string) error {
	cmd := exec.Command("gh", "secret", "set", name, "--body", value, "-R", repo)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("set secret %s: %s", name, string(out))
	}
	return nil
}

// SetVariable sets a repository variable.
func SetVariable(repo, name, value string) error {
	cmd := exec.Command("gh", "variable", "set", name, "--body", value, "-R", repo)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("set variable %s: %s", name, string(out))
	}
	return nil
}

// EnablePages enables GitHub Pages on the main branch from root.
func EnablePages(repo string) error {
	_, err := RunGH("api", fmt.Sprintf("repos/%s/pages", repo),
		"-X", "POST",
		"-f", "source[branch]=main",
		"-f", "source[path]=/",
	)
	// 409 means Pages is already enabled — that's fine
	if err != nil && !strings.Contains(err.Error(), "409") {
		return err
	}
	return nil
}

// TriggerWorkflow triggers a workflow by filename.
func TriggerWorkflow(repo, filename string) error {
	_, err := RunGH("workflow", "run", filename, "-R", repo)
	return err
}

// DisableNonEssentialWorkflows disables all workflows except the ones needed
// for the calendar pipeline (generate-calendar and pages-build-deployment).
func DisableNonEssentialWorkflows(repo string) ([]string, error) {
	keep := map[string]bool{
		"generate-calendar.yml":     true,
		"pages-build-deployment":    true, // dynamic workflow, no .yml
	}
	// List all workflows as JSON
	out, err := RunGH("api", fmt.Sprintf("repos/%s/actions/workflows", repo),
		"--jq", ".workflows[] | [.id, .path, .state] | @tsv",
	)
	if err != nil {
		return nil, err
	}
	var disabled []string
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "\t", 3)
		if len(parts) < 3 {
			continue
		}
		id, path, state := parts[0], parts[1], parts[2]
		if state == "disabled_manually" {
			continue
		}
		// Extract filename from path (e.g. ".github/workflows/foo.yml" -> "foo.yml")
		name := path
		if idx := strings.LastIndex(path, "/"); idx >= 0 {
			name = path[idx+1:]
		}
		if keep[name] {
			continue
		}
		// Disable this workflow
		_, err := RunGH("api", "-X", "PUT",
			fmt.Sprintf("repos/%s/actions/workflows/%s/disable", repo, id),
		)
		if err == nil {
			disabled = append(disabled, name)
		}
	}
	return disabled, nil
}
