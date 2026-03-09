package cmd

import (
	"fmt"
	"os/exec"
	"strings"

	"github.com/judell/community-calendar/cli/internal/github"
)

func Status() error {
	repo, err := github.GetCurrentRepo()
	if err != nil {
		return fmt.Errorf("could not determine GitHub repo: %w", err)
	}

	cmd := exec.Command("gh", "run", "list", "--limit", "5", "-R", repo)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("gh run list: %s", out)
	}

	output := strings.TrimSpace(string(out))
	if output == "" {
		fmt.Println("No workflow runs found.")
	} else {
		fmt.Println(output)
	}

	return nil
}
