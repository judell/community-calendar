package supabase

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

const apiBase = "https://api.supabase.com"

// Client wraps the Supabase Management API.
type Client struct {
	token      string
	httpClient *http.Client
}

// NewClient creates a Management API client with the given personal access token.
func NewClient(token string) *Client {
	return &Client{
		token:      token,
		httpClient: &http.Client{Timeout: 120 * time.Second},
	}
}

// Organization represents a Supabase organization.
type Organization struct {
	ID   string `json:"id"`
	Slug string `json:"slug"`
	Name string `json:"name"`
}

// Project represents a Supabase project.
type Project struct {
	ID             string `json:"id"`
	Ref            string `json:"ref"`
	Name           string `json:"name"`
	OrganizationID string `json:"organization_id"`
	Region         string `json:"region"`
	Status         string `json:"status"`
}

// APIKey represents a project API key.
type APIKey struct {
	Name   string `json:"name"`
	APIKey string `json:"api_key"`
	Type   string `json:"type"`
}

// HealthStatus represents a service health entry.
type HealthStatus struct {
	Name    string `json:"name"`
	Status  string `json:"status"`
	Healthy bool   `json:"healthy"`
}

// ListOrganizations returns all organizations the user belongs to.
func (c *Client) ListOrganizations() ([]Organization, error) {
	var orgs []Organization
	err := c.get("/v1/organizations", &orgs)
	return orgs, err
}

// CreateProject creates a new Supabase project.
func (c *Client) CreateProject(name, orgSlug, dbPass, regionCode string) (*Project, error) {
	body := map[string]interface{}{
		"name":              name,
		"organization_slug": orgSlug,
		"db_pass":           dbPass,
		"region_selection": map[string]string{
			"type": "smartGroup",
			"code": regionCode,
		},
	}
	var proj Project
	err := c.post("/v1/projects", body, &proj)
	return &proj, err
}

// GetProjectHealth returns health statuses for a project's services.
func (c *Client) GetProjectHealth(ref string) ([]HealthStatus, error) {
	var statuses []HealthStatus
	err := c.get(fmt.Sprintf("/v1/projects/%s/health?services=auth,rest,db", ref), &statuses)
	return statuses, err
}

// WaitForProject polls until the project's services are ACTIVE_HEALTHY.
func (c *Client) WaitForProject(ref string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		statuses, err := c.GetProjectHealth(ref)
		if err == nil {
			allHealthy := true
			for _, s := range statuses {
				if s.Status != "ACTIVE_HEALTHY" {
					allHealthy = false
					break
				}
			}
			if allHealthy && len(statuses) > 0 {
				return nil
			}
		}
		time.Sleep(5 * time.Second)
	}
	return fmt.Errorf("timed out waiting for project to become healthy")
}

// GetAPIKeys retrieves all API keys for a project.
func (c *Client) GetAPIKeys(ref string) ([]APIKey, error) {
	var keys []APIKey
	err := c.get(fmt.Sprintf("/v1/projects/%s/api-keys?reveal=true", ref), &keys)
	return keys, err
}

// RunSQL executes a SQL query against the project database.
func (c *Client) RunSQL(ref, query string) error {
	body := map[string]string{"query": query}
	var result interface{}
	return c.post(fmt.Sprintf("/v1/projects/%s/database/query", ref), body, &result)
}

// UpdateAuthConfig updates the auth configuration for a project.
func (c *Client) UpdateAuthConfig(ref string, config map[string]interface{}) error {
	return c.patch(fmt.Sprintf("/v1/projects/%s/config/auth", ref), config)
}

// DeployEdgeFunction creates or updates an edge function.
// Uses POST to create, PATCH to update if it already exists.
func (c *Client) DeployEdgeFunction(ref, name, body string, verifyJWT bool) error {
	payload := map[string]interface{}{
		"slug":       name,
		"name":       name,
		"verify_jwt": verifyJWT,
		"body":       body,
	}
	var result interface{}
	err := c.post(fmt.Sprintf("/v1/projects/%s/functions", ref), payload, &result)
	if err != nil && strings.Contains(err.Error(), "409") {
		// Already exists — update via PATCH
		return c.patch(fmt.Sprintf("/v1/projects/%s/functions/%s", ref, name), map[string]interface{}{
			"verify_jwt": verifyJWT,
			"body":       body,
		})
	}
	return err
}

// SetSecrets sets environment secrets for a project's edge functions.
func (c *Client) SetSecrets(ref string, secrets map[string]string) error {
	var payload []map[string]string
	for k, v := range secrets {
		payload = append(payload, map[string]string{"name": k, "value": v})
	}
	return c.post(fmt.Sprintf("/v1/projects/%s/secrets", ref), payload, nil)
}

// --- HTTP helpers ---

func (c *Client) get(path string, result interface{}) error {
	req, err := http.NewRequest("GET", apiBase+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	return c.doJSON(req, result)
}

func (c *Client) post(path string, body interface{}, result interface{}) error {
	data, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequest("POST", apiBase+path, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", "application/json")
	return c.doJSON(req, result)
}

func (c *Client) patch(path string, body interface{}) error {
	data, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequest("PATCH", apiBase+path, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("PATCH %s failed (HTTP %d): %s", path, resp.StatusCode, string(respBody))
	}
	return nil
}

func (c *Client) doJSON(req *http.Request, result interface{}) error {
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	if resp.StatusCode >= 300 {
		return fmt.Errorf("%s %s failed (HTTP %d): %s", req.Method, req.URL.Path, resp.StatusCode, string(respBody))
	}

	if result != nil {
		return json.Unmarshal(respBody, result)
	}
	return nil
}
