package cmd

import (
	"fmt"

	"github.com/judell/community-calendar/cli/internal/github"
)

func Build() error {
	repo, err := github.GetCurrentRepo()
	if err != nil {
		return fmt.Errorf("could not determine GitHub repo: %w", err)
	}

	fmt.Printf("Triggering build for %s...", repo)
	if err := github.TriggerWorkflow(repo, "generate-calendar.yml"); err != nil {
		return fmt.Errorf("\n  %w", err)
	}
	fmt.Println(" ✓")
	fmt.Println()
	fmt.Println("Build started. Check status with: cc-cli status")

	return nil
}
