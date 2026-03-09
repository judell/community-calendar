package state

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const stateFile = ".cc-cli-state.json"

// State holds all values collected and derived during init.
type State struct {
	Step            int    `json:"step"`
	Token           string `json:"token"`
	OrgSlug         string `json:"org_slug"`
	City            string `json:"city"`
	GHUser          string `json:"gh_user"`
	AnthropicKey    string `json:"anthropic_key"`
	OpenAIKey       string `json:"openai_key"`
	TicketmasterKey string `json:"ticketmaster_key"`
	ProjectName     string `json:"project_name"`
	ProjectRef      string `json:"project_ref"`
	DBPass          string `json:"db_pass"`
	Region          string `json:"region"`
	SupabaseURL     string `json:"supabase_url"`
	AnonKey         string `json:"anon_key"`
	PublishableKey  string `json:"publishable_key"`
	ServiceRoleKey  string `json:"service_role_key"`
	GHOAuthID       string `json:"gh_oauth_id"`
	GHOAuthSecret   string `json:"gh_oauth_secret"`
	GoogleOAuthID   string `json:"google_oauth_id"`
	GoogleOAuthSecret string `json:"google_oauth_secret"`
}

// Path returns the state file path relative to repoRoot.
func Path(repoRoot string) string {
	return filepath.Join(repoRoot, stateFile)
}

// Load reads state from disk. Returns nil state if file doesn't exist.
func Load(repoRoot string) (*State, error) {
	data, err := os.ReadFile(Path(repoRoot))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var s State
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

// Save writes state to disk.
func Save(repoRoot string, s *State) error {
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(Path(repoRoot), data, 0600)
}

// Remove deletes the state file.
func Remove(repoRoot string) error {
	err := os.Remove(Path(repoRoot))
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
