package prompt

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

// Ask prompts the user for input with a label. Returns the trimmed response.
func Ask(label string) (string, error) {
	fmt.Printf("  %s: ", label)
	text, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(text), nil
}

// AskRequired prompts the user and rejects empty input.
func AskRequired(label string) (string, error) {
	for {
		val, err := Ask(label)
		if err != nil {
			return "", err
		}
		if val != "" {
			return val, nil
		}
		fmt.Println("  (required)")
	}
}

// AskOptional prompts the user, allowing empty input.
func AskOptional(label string) (string, error) {
	return Ask(label + " (optional, Enter to skip)")
}

// AskWithDefault prompts the user with a default value.
func AskWithDefault(label, defaultVal string) (string, error) {
	fmt.Printf("  %s [%s]: ", label, defaultVal)
	text, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	val := strings.TrimSpace(text)
	if val == "" {
		return defaultVal, nil
	}
	return val, nil
}

// Choose presents numbered options and returns the selected index (0-based).
func Choose(label string, options []string) (int, error) {
	fmt.Printf("\n  %s:\n", label)
	for i, opt := range options {
		fmt.Printf("    %d. %s\n", i+1, opt)
	}
	for {
		fmt.Printf("  Select [1]: ")
		text, err := reader.ReadString('\n')
		if err != nil {
			return 0, err
		}
		val := strings.TrimSpace(text)
		if val == "" {
			return 0, nil
		}
		var idx int
		if _, err := fmt.Sscanf(val, "%d", &idx); err == nil && idx >= 1 && idx <= len(options) {
			return idx - 1, nil
		}
		fmt.Println("  (invalid choice)")
	}
}

// Confirm asks a yes/no question, defaulting to yes.
func Confirm(label string) (bool, error) {
	fmt.Printf("  %s [Y/n]: ", label)
	text, err := reader.ReadString('\n')
	if err != nil {
		return false, err
	}
	val := strings.TrimSpace(strings.ToLower(text))
	return val == "" || val == "y" || val == "yes", nil
}
