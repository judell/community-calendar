package cmd

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/judell/community-calendar/cli/internal/config"
	"github.com/judell/community-calendar/cli/internal/github"
	"github.com/judell/community-calendar/cli/internal/prompt"
	"github.com/judell/community-calendar/cli/internal/state"
	"github.com/judell/community-calendar/cli/internal/supabase"
)

// Steps:
//  1 = gathered token + org
//  2 = gathered city + user + API keys
//  3 = project created + ready + keys retrieved
//  4 = OAuth credentials gathered
//  5 = auth providers configured
//  6 = DDL applied + admin granted
//  7 = edge functions deployed
//  8 = supabase secrets set
//  9 = frontend files updated + other cities removed
// 10 = github secrets/vars + pages + workflow

func Init() error {
	fmt.Println()
	fmt.Println("Community Calendar Setup")
	fmt.Println("========================")
	fmt.Println()

	// --- Prerequisites ---
	if err := github.CheckGHInstalled(); err != nil {
		return err
	}

	repoRoot, err := findRepoRoot()
	if err != nil {
		return fmt.Errorf("not in a community-calendar repo: %w", err)
	}

	repo, err := github.GetCurrentRepo()
	if err != nil {
		return fmt.Errorf("could not determine GitHub repo: %w", err)
	}
	owner := strings.Split(repo, "/")[0]
	fmt.Printf("  Repo: %s\n", repo)

	// Ensure gh default repo matches the fork, not upstream
	if err := github.SetDefaultRepo(repo); err != nil {
		return fmt.Errorf("setting default repo: %w", err)
	}
	fmt.Println()

	// Check for saved state
	s, err := state.Load(repoRoot)
	if err != nil {
		return fmt.Errorf("loading state: %w", err)
	}
	if s != nil && s.Step > 0 {
		fmt.Printf("  Found saved progress (completed through step %d).\n", s.Step)
		resume, err := prompt.Confirm("Resume from where you left off?")
		if err != nil {
			return err
		}
		if !resume {
			s = &state.State{}
		}
	}
	if s == nil {
		s = &state.State{}
	}

	// --- Step 1: Supabase token + org ---
	if s.Step < 1 {
		fmt.Println("Step 1: Supabase")
		fmt.Println("  Get a token at: https://supabase.com/dashboard/account/tokens")
		s.Token, err = prompt.AskRequired("Access token")
		if err != nil {
			return err
		}

		client := supabase.NewClient(s.Token)

		orgs, err := client.ListOrganizations()
		if err != nil {
			return fmt.Errorf("listing organizations: %w", err)
		}
		if len(orgs) == 0 {
			return fmt.Errorf("no Supabase organizations found")
		}

		orgNames := make([]string, len(orgs))
		for i, o := range orgs {
			orgNames[i] = o.Name
		}
		orgIdx, err := prompt.Choose("Select organization", orgNames)
		if err != nil {
			return err
		}
		s.OrgSlug = orgs[orgIdx].Slug

		s.Step = 1
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Printf("Step 1: Supabase (saved — org: %s)\n", s.OrgSlug)
	}

	client := supabase.NewClient(s.Token)

	// --- Step 2: City + user + API keys ---
	if s.Step < 2 {
		fmt.Println("\nStep 2: Your fork")

		cities, err := config.ListCities(repoRoot)
		if err != nil {
			return fmt.Errorf("listing cities: %w", err)
		}
		if len(cities) > 0 {
			fmt.Printf("  Existing cities: %s\n", strings.Join(cities, ", "))
		}
		s.City, err = prompt.AskRequired("City name for this fork")
		if err != nil {
			return err
		}

		s.GHUser, err = prompt.AskRequired("GitHub username (for admin access)")
		if err != nil {
			return err
		}

		fmt.Println("\nStep 3: API keys")
		s.AnthropicKey, err = prompt.AskRequired("Anthropic API key (https://console.anthropic.com)")
		if err != nil {
			return err
		}

		s.OpenAIKey, err = prompt.AskOptional("OpenAI API key (https://platform.openai.com)")
		if err != nil {
			return err
		}

		s.TicketmasterKey, err = prompt.AskOptional("Ticketmaster Consumer Key (https://developer.ticketmaster.com — use the Consumer Key, not Consumer Secret)")
		if err != nil {
			return err
		}

		s.Step = 2
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Printf("Step 2: Fork config (saved — city: %s, user: %s)\n", s.City, s.GHUser)
		fmt.Println("Step 3: API keys (saved)")
	}

	// --- Step 3: Create Supabase project ---
	if s.Step < 3 {
		fmt.Println()

		s.ProjectName, err = prompt.AskWithDefault("Supabase project name", "community-calendar-"+s.City)
		if err != nil {
			return err
		}

		s.DBPass = generatePassword(32)

		s.Region, err = prompt.AskWithDefault("Region", "americas")
		if err != nil {
			return err
		}

		fmt.Printf("\nCreating Supabase project \"%s\"...", s.ProjectName)
		proj, err := client.CreateProject(s.ProjectName, s.OrgSlug, s.DBPass, s.Region)
		if err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		s.ProjectRef = proj.Ref
		s.SupabaseURL = fmt.Sprintf("https://%s.supabase.co", s.ProjectRef)

		fmt.Printf("  Project ref: %s\n", s.ProjectRef)
		fmt.Printf("  URL: %s\n", s.SupabaseURL)

		fmt.Printf("Waiting for project to be ready...")
		if err := client.WaitForProject(s.ProjectRef, 10*time.Minute); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		// Retrieve keys
		keys, err := client.GetAPIKeys(s.ProjectRef)
		if err != nil {
			return fmt.Errorf("getting API keys: %w", err)
		}

		for _, k := range keys {
			switch {
			case k.Type == "publishable":
				s.PublishableKey = k.APIKey
			case k.Name == "anon" || k.Type == "anon":
				s.AnonKey = k.APIKey
			case k.Name == "service_role":
				s.ServiceRoleKey = k.APIKey
			}
		}
		// Always use anon key for config.json — the REST API requires
		// the JWT anon key, not the publishable key.
		s.PublishableKey = s.AnonKey

		s.Step = 3
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Printf("Step 4: Project created (saved — ref: %s)\n", s.ProjectRef)
	}

	callbackURL := fmt.Sprintf("%s/auth/v1/callback", s.SupabaseURL)
	siteURL := fmt.Sprintf("https://%s.github.io/community-calendar/", owner)

	// --- Step 4: OAuth credentials ---
	if s.Step < 4 {
		fmt.Println("\nStep 4: Create OAuth apps")
		fmt.Println("  Your Supabase project is ready. Create OAuth apps using these URLs:")
		fmt.Println()
		fmt.Println("  GitHub OAuth App → https://github.com/settings/developers")
		fmt.Println("    Click 'New OAuth App' (not GitHub App)")
		fmt.Printf("    Homepage URL:     %s\n", siteURL)
		fmt.Printf("    Callback URL:     %s\n", callbackURL)
		fmt.Println("    Leave 'Enable Device Flow' unchecked")
		s.GHOAuthID, err = prompt.AskRequired("Client ID")
		if err != nil {
			return err
		}
		s.GHOAuthSecret, err = prompt.AskRequired("Client Secret (click 'Generate a new client secret')")
		if err != nil {
			return err
		}

		fmt.Println()
		fmt.Println("  Google OAuth App → https://console.cloud.google.com/apis/credentials")
		fmt.Println("    If you don't have a Google Cloud project yet:")
		fmt.Println("      1. Go to console.cloud.google.com → create a new project (or use existing)")
		fmt.Println("      2. Go to 'APIs & Services' → 'OAuth consent screen' → 'Get started'")
		fmt.Println("      3. App name: e.g. 'Community Calendar', email: yours → Next")
		fmt.Println("      4. Audience: External → Next")
		fmt.Println("      5. Contact email: yours → Next")
		fmt.Println("      6. Check the policy box → click 'Continue', then 'Create'")
		fmt.Println("    Then create credentials:")
		fmt.Println("      7. Go to Credentials (left sidebar) → '+ Create credentials' → 'OAuth client ID'")
		fmt.Println("      8. Application type: Web application")
		fmt.Println("      9. Authorized redirect URIs: add the callback URL below")
		fmt.Printf("    Callback URL: %s\n", callbackURL)
		s.GoogleOAuthID, err = prompt.AskRequired("Client ID")
		if err != nil {
			return err
		}
		s.GoogleOAuthSecret, err = prompt.AskRequired("Client Secret")
		if err != nil {
			return err
		}

		s.Step = 4
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Step 5: OAuth apps (saved)")
	}

	// --- Step 5: Auth config ---
	if s.Step < 5 {
		fmt.Println()
		fmt.Printf("Configuring auth providers...")
		redirectList := fmt.Sprintf("%s**,%s**", siteURL, "http://localhost:8080/")
		err = client.UpdateAuthConfig(s.ProjectRef, map[string]interface{}{
			"external_github_enabled":   true,
			"external_github_client_id": s.GHOAuthID,
			"external_github_secret":    s.GHOAuthSecret,
			"external_google_enabled":   true,
			"external_google_client_id": s.GoogleOAuthID,
			"external_google_secret":    s.GoogleOAuthSecret,
			"site_url":                  siteURL,
			"uri_allow_list":            redirectList,
		})
		if err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		s.Step = 5
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Configuring auth providers... ✓ (saved)")
	}

	// --- Step 6: DDL + admin ---
	if s.Step < 6 {
		fmt.Printf("Applying database schema...")
		if err := applyDDL(client, s.ProjectRef, repoRoot, s.SupabaseURL, s.AnonKey); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		fmt.Printf("Granting admin access to %s...", s.GHUser)
		adminSQL := fmt.Sprintf(
			"INSERT INTO admin_github_users (github_user) VALUES ('%s') ON CONFLICT DO NOTHING;",
			s.GHUser,
		)
		if err := client.RunSQL(s.ProjectRef, adminSQL); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		s.Step = 6
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Applying database schema... ✓ (saved)")
		fmt.Printf("Granting admin access to %s... ✓ (saved)\n", s.GHUser)
	}

	// --- Step 7: Edge functions ---
	if s.Step < 7 {
		fmt.Printf("Deploying edge functions...")
		fnNames := []string{"load-events", "my-picks", "capture-event"}
		for _, fn := range fnNames {
			fnPath := filepath.Join(repoRoot, "supabase", "functions", fn, "index.ts")
			body, err := os.ReadFile(fnPath)
			if err != nil {
				return fmt.Errorf("\n  reading %s: %w", fn, err)
			}
			if err := client.DeployEdgeFunction(s.ProjectRef, fn, string(body), false); err != nil {
				return fmt.Errorf("\n  deploying %s: %w", fn, err)
			}
		}
		fmt.Println(" ✓")

		s.Step = 7
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Deploying edge functions... ✓ (saved)")
	}

	// --- Step 8: Supabase secrets ---
	if s.Step < 8 {
		fmt.Printf("Setting Supabase secrets...")
		secrets := map[string]string{
			"GITHUB_REPO":      repo,
			"ANTHROPIC_API_KEY": s.AnthropicKey,
		}
		if s.OpenAIKey != "" {
			secrets["OPENAI_API_KEY"] = s.OpenAIKey
		}
		if err := client.SetSecrets(s.ProjectRef, secrets); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		s.Step = 8
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Setting Supabase secrets... ✓ (saved)")
	}

	// --- Step 9: Frontend files + remove cities ---
	if s.Step < 9 {
		fmt.Printf("Updating frontend config files...")
		if err := config.UpdateConfigJSON(repoRoot, s.SupabaseURL, s.PublishableKey); err != nil {
			return fmt.Errorf("\n  config.json: %w", err)
		}
		if err := config.UpdateHTMLFiles(repoRoot, s.SupabaseURL, s.PublishableKey, s.ProjectRef); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		// Ensure chosen city directory exists with feeds.txt
		cityDir := filepath.Join(repoRoot, "cities", s.City)
		if err := os.MkdirAll(cityDir, 0755); err != nil {
			return fmt.Errorf("\n  creating city dir: %w", err)
		}
		feedsPath := filepath.Join(cityDir, "feeds.txt")
		if _, err := os.Stat(feedsPath); os.IsNotExist(err) {
			if err := os.WriteFile(feedsPath, []byte(starterFeeds), 0644); err != nil {
				return fmt.Errorf("\n  creating feeds.txt: %w", err)
			}
			fmt.Printf("Created cities/%s/feeds.txt with sample ICS feeds\n", s.City)
		}

		// Optionally remove other city directories
		otherCities, _ := config.ListOtherCities(repoRoot, s.City)
		if len(otherCities) > 0 {
			fmt.Printf("  Other city directories found: %s\n", strings.Join(otherCities, ", "))
			fmt.Println("  Keeping them gives you sample data for development.")
			removeOthers, err := prompt.Confirm("Remove other city directories?")
			if err != nil {
				return err
			}
			if removeOthers {
				removed, err := config.RemoveOtherCities(repoRoot, s.City)
				if err != nil {
					return fmt.Errorf("\n  %w", err)
				}
				fmt.Printf("Removed: %s\n", strings.Join(removed, ", "))
			} else {
				fmt.Println("  Keeping other city directories.")
			}
		}

		// Update workflow locations description to match remaining cities
		if err := updateWorkflowLocations(repoRoot); err != nil {
			return fmt.Errorf("\n  updating workflow locations: %w", err)
		}

		// Strip per-city scrape blocks from workflow (forks use feeds.txt only)
		fmt.Printf("Stripping upstream scrape blocks from workflow...")
		if err := stripScrapeBlocks(repoRoot); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		// Ensure download_feeds.py exists (fork may predate it)
		feedsScript := filepath.Join(repoRoot, "scripts", "download_feeds.py")
		if _, err := os.Stat(feedsScript); os.IsNotExist(err) {
			fmt.Println("  Warning: scripts/download_feeds.py not found.")
			fmt.Println("  Sync your fork from upstream to get this required script.")
		}

		s.Step = 9
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Updating frontend config files... ✓ (saved)")
		fmt.Println("Removing other city directories... ✓ (saved)")
	}

	// --- Step 10: GitHub secrets/vars + Pages + workflow ---
	if s.Step < 10 {
		fmt.Printf("Setting GitHub Actions secrets...")
		ghSecrets := map[string]string{
			"SUPABASE_ANON_KEY": s.AnonKey,
			"ANTHROPIC_API_KEY": s.AnthropicKey,
		}
		if s.TicketmasterKey != "" {
			ghSecrets["TICKETMASTER_API_KEY"] = s.TicketmasterKey
		}
		for k, v := range ghSecrets {
			if err := github.SetSecret(repo, k, v); err != nil {
				return fmt.Errorf("\n  %w", err)
			}
		}
		fmt.Println(" ✓")

		fmt.Printf("Setting GitHub Actions variables...")
		ghVars := map[string]string{
			"SUPABASE_URL": s.SupabaseURL,
			"SUPABASE_KEY": s.AnonKey,
		}
		for k, v := range ghVars {
			if err := github.SetVariable(repo, k, v); err != nil {
				return fmt.Errorf("\n  %w", err)
			}
		}
		fmt.Println(" ✓")

		fmt.Printf("Enabling GitHub Pages...")
		if err := github.EnablePages(repo); err != nil {
			return fmt.Errorf("\n  %w", err)
		}
		fmt.Println(" ✓")

		fmt.Printf("Disabling non-essential workflows...")
		disabled, err := github.DisableNonEssentialWorkflows(repo)
		if err != nil {
			// Non-fatal — workflows may not be enabled yet on fork
			fmt.Println(" (skipped)")
		} else if len(disabled) > 0 {
			fmt.Printf(" ✓ (%s)\n", strings.Join(disabled, ", "))
		} else {
			fmt.Println(" ✓ (none to disable)")
		}

		s.Step = 10
		if err := state.Save(repoRoot, s); err != nil {
			return fmt.Errorf("saving state: %w", err)
		}
	} else {
		fmt.Println("Setting GitHub Actions secrets... ✓ (saved)")
		fmt.Println("Setting GitHub Actions variables... ✓ (saved)")
		fmt.Println("Enabling GitHub Pages... ✓ (saved)")
	}

	// Clean up state file on success
	state.Remove(repoRoot)

	// --- Commit and push ---
	fmt.Printf("Committing configuration...")
	gitAdd := exec.Command("git", "add", "-A")
	gitAdd.Dir = repoRoot
	if out, err := gitAdd.CombinedOutput(); err != nil {
		return fmt.Errorf("git add: %s", out)
	}
	gitCommit := exec.Command("git", "commit", "-m", "Configure fork")
	gitCommit.Dir = repoRoot
	if out, err := gitCommit.CombinedOutput(); err != nil {
		return fmt.Errorf("git commit: %s", out)
	}
	fmt.Println(" ✓")

	fmt.Printf("Pushing to GitHub...")
	gitPush := exec.Command("git", "push", "origin", "main")
	gitPush.Dir = repoRoot
	if out, err := gitPush.CombinedOutput(); err != nil {
		return fmt.Errorf("git push: %s", out)
	}
	fmt.Println(" ✓")

	// Done
	fmt.Println()
	fmt.Printf("Done! Your calendar will be live at:\n")
	fmt.Printf("  %s?city=%s\n", siteURL, s.City)
	fmt.Println()
	fmt.Println("Next steps:")
	fmt.Printf("  1. Enable workflows: visit https://github.com/%s/actions and click\n", repo)
	fmt.Println("     \"I understand my workflows, go ahead and enable them\"")
	fmt.Println("  2. Trigger the first build: cc-cli build")
	fmt.Println("  3. Check build status: cc-cli status")

	return nil
}

// starterFeeds provides sample ICS feed URLs for a new city.
// These are real feeds from Davis, CA — a good starting set to verify the pipeline works.
const starterFeeds = `# Sample ICS feeds (from Davis, CA) — replace with feeds for your city
# The workflow downloads all https:// URLs automatically via scripts/download_feeds.sh

# Meetup
https://www.meetup.com/mosaics/events/ical/
https://www.meetup.com/intercultural-mosaics/events/ical/
https://www.meetup.com/yolo-county-board-game-gathering/events/ical/
https://www.meetup.com/pence-adult-art-programs/events/ical/
https://www.meetup.com/art-in-action/events/ical/
https://www.meetup.com/mindful-embodied-spirituality/events/ical/
https://www.meetup.com/winters-shut-up-and-write-meetup-group/events/ical/

# iCal feeds
https://thedirt.online/events/?ical=1
https://visitdavis.org/events/?ical=1
https://visityolo.com/event/?ical=1
https://putahcreekcouncil.org/events/?ical=1
https://hatefreetogether.org/events/?ical=1

# Google Calendar
https://calendar.google.com/calendar/ical/davisbikeclubwww%40gmail.com/public/basic.ics
`

// applyDDL reads and executes all DDL files in order.
func applyDDL(client *supabase.Client, ref, repoRoot, supabaseURL, anonKey string) error {
	ddlDir := filepath.Join(repoRoot, "supabase", "ddl")
	entries, err := os.ReadDir(ddlDir)
	if err != nil {
		return fmt.Errorf("reading ddl directory: %w", err)
	}

	// Sort to ensure correct order
	var sqlFiles []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".sql") {
			sqlFiles = append(sqlFiles, e.Name())
		}
	}
	sort.Strings(sqlFiles)

	for _, f := range sqlFiles {
		data, err := os.ReadFile(filepath.Join(ddlDir, f))
		if err != nil {
			return fmt.Errorf("reading %s: %w", f, err)
		}
		sql := string(data)

		// Template the cron job SQL with real values
		if f == "05_cron_jobs.sql" {
			sql = strings.ReplaceAll(sql, "https://dzpdualvwspgqghrysyz.supabase.co", supabaseURL)
			sql = strings.ReplaceAll(sql, "<YOUR_LEGACY_ANON_KEY>", anonKey)
		}

		if err := client.RunSQL(ref, sql); err != nil {
			return fmt.Errorf("executing %s: %w", f, err)
		}
	}
	return nil
}

func generatePassword(length int) string {
	b := make([]byte, length)
	rand.Read(b)
	return hex.EncodeToString(b)[:length]
}

// updateWorkflowLocations rewrites the locations description in the workflow
// to list the actual city directories present in cities/.
func updateWorkflowLocations(repoRoot string) error {
	citiesDir := filepath.Join(repoRoot, "cities")
	entries, err := os.ReadDir(citiesDir)
	if err != nil {
		return err
	}

	var cities []string
	for _, e := range entries {
		if e.IsDir() {
			cities = append(cities, e.Name())
		}
	}
	sort.Strings(cities)

	workflowPath := filepath.Join(repoRoot, ".github", "workflows", "generate-calendar.yml")
	content, err := os.ReadFile(workflowPath)
	if err != nil {
		return err
	}

	oldLine := `        description: 'Locations to process (comma-separated:`
	newDesc := fmt.Sprintf("        description: 'Locations to process (comma-separated: %s or \"all\")'",
		strings.Join(cities, ","))

	lines := strings.Split(string(content), "\n")
	for i, line := range lines {
		if strings.HasPrefix(line, oldLine) {
			lines[i] = newDesc
			break
		}
	}

	return os.WriteFile(workflowPath, []byte(strings.Join(lines, "\n")), 0644)
}

// stripScrapeBlocks removes per-city "Scrape <City> sources" blocks from the
// workflow. Forks don't have the scrapers — they use feeds.txt only.
// Each block starts with a "# ====.../<City>" comment header and the
// "- name: Scrape ..." step, ending just before the next "# ====" header
// or the "Download live feeds" section.
func stripScrapeBlocks(repoRoot string) error {
	workflowPath := filepath.Join(repoRoot, ".github", "workflows", "generate-calendar.yml")
	content, err := os.ReadFile(workflowPath)
	if err != nil {
		return err
	}

	lines := strings.Split(string(content), "\n")
	var result []string
	inScrapeBlock := false

	for i := 0; i < len(lines); i++ {
		trimmed := strings.TrimSpace(lines[i])

		// Detect start of a city-specific scrape section:
		// A "# ====..." header followed by a "- name: Scrape" step
		if strings.HasPrefix(trimmed, "# =") && strings.Contains(trimmed, "=") {
			// Look ahead to see if this section contains a Scrape step
			isScrapeSection := false
			for j := i + 1; j < len(lines) && j < i+5; j++ {
				if strings.Contains(lines[j], "- name: Scrape") {
					isScrapeSection = true
					break
				}
			}
			if isScrapeSection {
				inScrapeBlock = true
				continue
			}
		}

		if inScrapeBlock {
			// End of scrape block: next "# ====" header or non-blank/non-comment content
			if strings.HasPrefix(trimmed, "# =") && strings.Contains(trimmed, "=") {
				inScrapeBlock = false
				// Re-process this line (it might be the Download section header)
				i--
				continue
			}
			// Skip all lines in the scrape block
			continue
		}

		result = append(result, lines[i])
	}

	return os.WriteFile(workflowPath, []byte(strings.Join(result, "\n")), 0644)
}

func findRepoRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "config.json")); err == nil {
			if _, err := os.Stat(filepath.Join(dir, "supabase", "ddl")); err == nil {
				return dir, nil
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("could not find community-calendar repo root")
		}
		dir = parent
	}
}
