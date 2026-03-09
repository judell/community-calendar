package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// UpdateConfigJSON writes the Supabase URL and publishable key into config.json.
func UpdateConfigJSON(repoRoot, supabaseURL, publishableKey string) error {
	path := filepath.Join(repoRoot, "config.json")
	return replaceInFile(path, map[string]string{
		"https://dzpdualvwspgqghrysyz.supabase.co":    supabaseURL,
		"sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5": publishableKey,
	})
}

// UpdateHTMLFiles updates Supabase credentials in all HTML files.
func UpdateHTMLFiles(repoRoot, supabaseURL, publishableKey, projectRef string) error {
	files := []string{"index.html", "report.html", "test.html", "embed.html"}
	replacements := map[string]string{
		"https://dzpdualvwspgqghrysyz.supabase.co":        supabaseURL,
		"sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5":     publishableKey,
		"sb-dzpdualvwspgqghrysyz-auth-token": "sb-" + projectRef + "-auth-token",
	}
	for _, f := range files {
		path := filepath.Join(repoRoot, f)
		if err := replaceInFile(path, replacements); err != nil {
			return fmt.Errorf("%s: %w", f, err)
		}
	}
	return nil
}

// UpdateCronJobSQL updates the cron job DDL with the real project URL and anon key.
func UpdateCronJobSQL(repoRoot, supabaseURL, anonKey string) error {
	path := filepath.Join(repoRoot, "supabase", "ddl", "05_cron_jobs.sql")
	return replaceInFile(path, map[string]string{
		"https://dzpdualvwspgqghrysyz.supabase.co": supabaseURL,
		"<YOUR_LEGACY_ANON_KEY>":                   anonKey,
	})
}

// ListOtherCities returns names of city directories that don't match the chosen city.
func ListOtherCities(repoRoot, keepCity string) ([]string, error) {
	citiesDir := filepath.Join(repoRoot, "cities")
	entries, err := os.ReadDir(citiesDir)
	if err != nil {
		return nil, err
	}
	var others []string
	for _, e := range entries {
		if e.IsDir() && e.Name() != keepCity {
			others = append(others, e.Name())
		}
	}
	return others, nil
}

// RemoveOtherCities deletes city directories that don't match the chosen city.
func RemoveOtherCities(repoRoot, keepCity string) ([]string, error) {
	citiesDir := filepath.Join(repoRoot, "cities")
	entries, err := os.ReadDir(citiesDir)
	if err != nil {
		return nil, err
	}
	var removed []string
	for _, e := range entries {
		if e.IsDir() && e.Name() != keepCity {
			path := filepath.Join(citiesDir, e.Name())
			if err := os.RemoveAll(path); err != nil {
				return nil, fmt.Errorf("removing %s: %w", e.Name(), err)
			}
			removed = append(removed, e.Name())
		}
	}
	return removed, nil
}

// ListCities returns the names of city directories that have a feeds.txt.
func ListCities(repoRoot string) ([]string, error) {
	citiesDir := filepath.Join(repoRoot, "cities")
	entries, err := os.ReadDir(citiesDir)
	if err != nil {
		return nil, err
	}
	var cities []string
	for _, e := range entries {
		if e.IsDir() {
			feedsPath := filepath.Join(citiesDir, e.Name(), "feeds.txt")
			if _, err := os.Stat(feedsPath); err == nil {
				cities = append(cities, e.Name())
			}
		}
	}
	return cities, nil
}

func replaceInFile(path string, replacements map[string]string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	content := string(data)
	for old, new := range replacements {
		content = strings.ReplaceAll(content, old, new)
	}
	return os.WriteFile(path, []byte(content), 0644)
}
